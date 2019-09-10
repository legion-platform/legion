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
from legion.cli.parsers import toolchain_integration
from legion.cli.parsers.toolchain_integration import ID_AND_FILE_MISSED_ERROR_MESSAGE, IGNORE_NOT_FOUND_ERROR_MESSAGE
from legion.cli.utils.output import JSON_OUTPUT_FORMAT, JSONPATH_OUTPUT_FORMAT
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.toolchain_integration import ToolchainIntegrationClient
from legion.sdk.models import ToolchainIntegration, ToolchainIntegrationSpec

TI_ID = 'some-id'


@pytest.fixture
def ti_client() -> ToolchainIntegrationClient:
    return ToolchainIntegrationClient()


@pytest.fixture
def ti() -> ToolchainIntegration:
    return ToolchainIntegration(
        id=TI_ID,
        spec=ToolchainIntegrationSpec(
            default_image="mock-image",
            entrypoint="default-entrypoint",
        ),
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_get(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient, ti: ToolchainIntegration):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'get', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['get', '--id', TI_ID, '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code == 0
    assert json.loads(result.output) == [ti.to_dict()]


def test_get_all(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient, ti: ToolchainIntegration):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'get_all', return_value=[ti])

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['get', '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    client_mock.assert_called_once_with()
    assert result.exit_code == 0
    assert json.loads(result.output) == [ti.to_dict()]


def test_get_jsonpath(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                      ti: ToolchainIntegration):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'get', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['get', '--id', TI_ID, '-o',
                                                                             f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code == 0
    assert result.output.strip() == TI_ID


def test_get_default_output_format(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                                   ti: ToolchainIntegration):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'get', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['get', '--id', TI_ID],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code == 0
    assert TI_ID in result.stdout


def test_get_wrong_output_format(cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['get', '--id', TI_ID, '-o', wrong_format],
                               obj=ti_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_edit(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
              ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'edit', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['edit', '-f', ti_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert json.loads(result.output) == [ti.to_dict()]


def test_edit_jsonpath(mocker, tmp_path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                       ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'edit', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['edit', '-f', ti_file, '-o',
                                                                             f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert result.output.strip() == TI_ID


def test_edit_default_output_format(mocker, tmp_path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                                    ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'edit', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['edit', '-f', ti_file],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert TI_ID in result.stdout


def test_edit_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                         ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['edit', '-f', ti_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_edit_wrong_output_format(cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['edit', '--id', TI_ID, '-o', wrong_format],
                               obj=ti_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_create(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'create', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['create', '-f', ti_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert json.loads(result.output) == [ti.to_dict()]


def test_create_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                           ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['create', '-f', ti_file, '-o', JSON_OUTPUT_FORMAT],
                               obj=ti_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_create_wrong_output_format(cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    wrong_format = 'wrong-format'
    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['edit', '--id', TI_ID, '-o', wrong_format],
                               obj=ti_client)

    assert result.exit_code != 0
    assert f'invalid choice: {wrong_format}' in result.output


def test_create_jsonpath(mocker, tmp_path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                         ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'create', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['create', '-f', ti_file, '-o',
                                                                             f'{JSONPATH_OUTPUT_FORMAT}=[*].id'],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert result.output.strip() == TI_ID


def test_create_default_output_format(mocker, tmp_path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                                      ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'create', return_value=ti)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['create', '-f', ti_file],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti)
    assert result.exit_code == 0
    assert TI_ID in result.stdout


def test_delete_by_file(tmp_path: pathlib.Path, mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                        ti: ToolchainIntegration):
    message = "tiection was deleted"
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'delete', return_value=message)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['delete', '-f', ti_file],
                               obj=ti_client)

    client_mock.assert_called_once_with(ti.id)
    assert result.exit_code == 0
    assert message in result.stdout


def test_delete_by_id(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    message = "tiection was deleted"
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'delete', return_value=message)

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['delete', '--id', TI_ID],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code == 0
    assert message in result.stdout


def test_delete_id_and_file_missed(cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['delete'], obj=ti_client)

    assert result.exit_code != 0
    assert ID_AND_FILE_MISSED_ERROR_MESSAGE in str(result.exception)


def test_delete_id_and_file_present(tmp_path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                                    ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'ToolchainIntegration'}}))
    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['delete', '--id', 'some-id', '-f', ti_file],
                               obj=ti_client)

    assert result.exit_code != 0
    assert ID_AND_FILE_MISSED_ERROR_MESSAGE in str(result.exception)


def test_delete_wrong_kind(tmp_path: pathlib.Path, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient,
                           ti: ToolchainIntegration):
    ti_file = tmp_path / "ti.yaml"
    ti_file.write_text(json.dumps({**ti.to_dict(), **{'kind': 'Wrong'}}))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['delete', '-f', ti_file],
                               obj=ti_client)

    assert result.exit_code != 0
    assert "Unknown kind of object: 'Wrong'" in str(result.exception)


def test_delete_ignore_not_found_disabled(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.NOT_FOUND))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration, ['delete', '--id', TI_ID],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code != 0
    assert "Got error from server" in str(result.exception)


def test_delete_ignore_not_found_enabled(mocker, cli_runner: CliRunner, ti_client: ToolchainIntegrationClient):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.NOT_FOUND))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['delete', '--id', TI_ID, '--ignore-not-found'],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code == 0
    assert IGNORE_NOT_FOUND_ERROR_MESSAGE.format(TI_ID) in result.stdout


def test_delete_ignore_not_found_enabled_http_code(mocker, cli_runner: CliRunner,
                                                   ti_client: ToolchainIntegrationClient):
    client_mock = mocker.patch.object(ToolchainIntegrationClient, 'delete',
                                      side_effect=WrongHttpStatusCode(http.HTTPStatus.BAD_REQUEST))

    result = cli_runner.invoke(toolchain_integration.toolchain_integration,
                               ['delete', '--id', TI_ID, '--ignore-not-found'],
                               obj=ti_client)

    client_mock.assert_called_once_with(TI_ID)
    assert result.exit_code != 0
    assert "Got error from server" in str(result.exception)
