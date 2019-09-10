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
"""
External storage handler
"""
import logging

from cloudstorage.drivers.amazon import S3Driver
from legion.sdk.models import Connection

LOGGER = logging.getLogger(__name__)


def _build_s3_driver(connection: Connection):
    driver = S3Driver(
        key=connection.spec.username,
        secret=connection.spec.key_secret,
    )
    return driver, driver.get_container(connection.spec.uri)


def upload_file_to_connection(local_path: str, remote_path: str, connection: Connection):
    connection_type = connection.spec.type.upper()
    if connection_type == 'S3':
        _, container = _build_s3_driver(connection)
    else:
        raise Exception(f'Unsupported driver {connection_type}')

    container.upload_blob(local_path, blob_name=remote_path)
