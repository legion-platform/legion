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

from .data_models import PackagingResourceConnection, PackagingResourceConnectionBody

LOGGER = logging.getLogger(__name__)


def _build_s3_driver(connection_body: PackagingResourceConnectionBody):
    driver = S3Driver(
        key=connection_body.user,
        secret=connection_body.secret,
    )
    return driver, driver.get_container(connection_body.uri)


def upload_file_to_connection(local_path: str, remote_path: str, connection: PackagingResourceConnection):
    connection_type = connection.body.type.upper()
    if connection_type == 'S3':
        driver, container = _build_s3_driver(connection.body)
    else:
        raise Exception(f'Unsupported driver {connection_type}')

    container.upload_blob(local_path, blob_name=remote_path)
