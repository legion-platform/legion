#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import http
import json
import pathlib

import pytest
from click.testing import CliRunner
from legion.cli.parsers import connection
from legion.cli.parsers.connection import ID_AND_FILE_MISSED_ERROR_MESSAGE, IGNORE_NOT_FOUND_ERROR_MESSAGE
from legion.cli.utils.output import JSON_OUTPUT_FORMAT, JSONPATH_OUTPUT_FORMAT
from legion.sdk.clients.connection import ConnectionClient
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.models import Connection, ConnectionSpec

CONN_ID = 'some-id'


@pytest.fixture
def conn_client() -> ConnectionClient:
    return ConnectionClient()


@pytest.fixture
def conn() -> Connection:
    return Connection(
        id=CONN_ID,
        spec=ConnectionSpec(
            key_secret="mock-key-secret",
            uri="mock-url",
        ),
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_get(mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    client_mock = mocker.patch.object(ConnectionClient, 'get', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['get', '--id', CONN_ID, '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code == 0
    assert json.loads(result.output) == [conn.to_dict()]


def test_get_all(mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    client_mock = mocker.patch.object(ConnectionClient, 'get_all', return_value=[conn])

    result = cli_runner.invoke(connection.connection, ['get', '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    client_mock.assert_called_once_with()
    assert result.exit_code == 0
    assert json.loads(result.output) == [conn.to_dict()]


def test_get_jsonpath(mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    client_mock = mocker.patch.object(ConnectionClient, 'get', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['get', '--id', CONN_ID, '-o',
                                                        f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code == 0
    assert result.output.strip() == CONN_ID


def test_get_default_output_format(mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    client_mock = mocker.patch.object(ConnectionClient, 'get', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['get', '--id', CONN_ID],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code == 0
    assert CONN_ID in result.stdout


def test_get_wrong_output_format(cli_runner: CliRunner, conn_client: ConnectionClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(connection.connection, ['get', '--id', CONN_ID, '-o', wrong_format],
                               obj=conn_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_edit(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'edit', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['edit', '-f', conn_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert json.loads(result.output) == [conn.to_dict()]


def test_edit_jsonpath(mocker, tmp_path, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'edit', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['edit', '-f', conn_file, '-o',
                                                        f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert result.output.strip() == CONN_ID


def test_edit_default_output_format(mocker, tmp_path, cli_runner: CliRunner, conn_client: ConnectionClient,
                                    conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'edit', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['edit', '-f', conn_file],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert CONN_ID in result.stdout


def test_edit_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, conn_client: ConnectionClient,
                         conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(connection.connection, ['edit', '-f', conn_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_edit_wrong_output_format(cli_runner: CliRunner, conn_client: ConnectionClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(connection.connection, ['edit', '--id', CONN_ID, '-o', wrong_format],
                               obj=conn_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_create(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'create', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['create', '-f', conn_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert json.loads(result.output) == [conn.to_dict()]


def test_create_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, conn_client: ConnectionClient,
                           conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(connection.connection, ['create', '-f', conn_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=conn_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_create_wrong_output_format(cli_runner: CliRunner, conn_client: ConnectionClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(connection.connection, ['edit', '--id', CONN_ID, '-o', wrong_format],
                               obj=conn_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_create_jsonpath(mocker, tmp_path, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'create', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['create', '-f', conn_file, '-o',
                                                        f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert result.output.strip() == CONN_ID


def test_create_default_output_format(mocker, tmp_path, cli_runner: CliRunner, conn_client: ConnectionClient,
                                      conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'create', return_value=conn)

    result = cli_runner.invoke(connection.connection, ['create', '-f', conn_file],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn)
    assert result.exit_code == 0
    assert CONN_ID in result.stdout


def test_delete_by_file(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, conn_client: ConnectionClient,
                        conn: Connection):
    message = "connection was deleted"
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    client_mock = mocker.patch.object(ConnectionClient, 'delete', return_value=message)

    result = cli_runner.invoke(connection.connection, ['delete', '-f', conn_file],
                               obj=conn_client)

    client_mock.assert_called_once_with(conn.id)
    assert result.exit_code == 0
    assert message in result.stdout


def test_delete_by_id(mocker, cli_runner: CliRunner, conn_client: ConnectionClient):
    message = "connection was deleted"
    client_mock = mocker.patch.object(ConnectionClient, 'delete', return_value=message)

    result = cli_runner.invoke(connection.connection, ['delete', '--id', CONN_ID],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code == 0
    assert message in result.stdout


def test_delete_id_and_file_missed(cli_runner: CliRunner, conn_client: ConnectionClient):
    result = cli_runner.invoke(connection.connection, ['delete'], obj=conn_client)

    assert result.exit_code != 0
    assert ID_AND_FILE_MISSED_ERROR_MESSAGE in str(result.exception)


def test_delete_id_and_file_present(tmp_path, cli_runner: CliRunner, conn_client: ConnectionClient, conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Connection'}}))
    result = cli_runner.invoke(connection.connection, ['delete', '--id', 'some-id', '-f', conn_file],
                               obj=conn_client)

    assert result.exit_code != 0
    assert ID_AND_FILE_MISSED_ERROR_MESSAGE in str(result.exception)


def test_delete_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, conn_client: ConnectionClient,
                           conn: Connection):
    conn_file = tmp_path / "conn.yaml"
    conn_file.write_text(json.dumps({**conn.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(connection.connection, ['delete', '-f', conn_file],
                               obj=conn_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_delete_ignore_not_found_disabled(mocker, cli_runner: CliRunner, conn_client: ConnectionClient):
    client_mock = mocker.patch.object(ConnectionClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.NOT_FOUND))

    result = cli_runner.invoke(connection.connection, ['delete', '--id', CONN_ID],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code != 0
    assert "Got error from server" in str(result.exception)


def test_delete_ignore_not_found_enabled(mocker, cli_runner: CliRunner, conn_client: ConnectionClient):
    client_mock = mocker.patch.object(ConnectionClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.NOT_FOUND))

    result = cli_runner.invoke(connection.connection, ['delete', '--id', CONN_ID, '--ignore-not-found'],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code == 0
    assert IGNORE_NOT_FOUND_ERROR_MESSAGE.format(CONN_ID) in result.stdout


def test_delete_ignore_not_found_enabled_http_code(mocker, cli_runner: CliRunner, conn_client: ConnectionClient):
    client_mock = mocker.patch.object(ConnectionClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.BAD_REQUEST))

    result = cli_runner.invoke(connection.connection, ['delete', '--id', CONN_ID, '--ignore-not-found'],
                               obj=conn_client)

    client_mock.assert_called_once_with(CONN_ID)
    assert result.exit_code != 0
    assert "Got error from server" in str(result.exception)
