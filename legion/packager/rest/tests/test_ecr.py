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
import pytest
from legion.packager.rest.extensions.ecr import get_ecr_credentials, extract_repository_from_ecr_url, ECRRegistry
from legion.sdk.models import ConnectionSpec


def test_validate_connection_type() -> None:
    conn_spec = ConnectionSpec(type='git')

    with pytest.raises(ValueError, match=r".*Unexpected connection type.*"):
        get_ecr_credentials(conn_spec, 'some/docker:url')


def test_extract_repository_from_ecr_url():
    registry_info = extract_repository_from_ecr_url(
        '5555555555.dkr.ecr.eu-central-1.amazonaws.com/counter-3.3:460c-8f3c-eb3b3d2e1d98'
    )

    assert registry_info == ECRRegistry(id='5555555555', repository_name='counter-3.3')


def test_extract_repository_from_ecr_url_with_namespace():
    registry_info = extract_repository_from_ecr_url(
        '5555555555.dkr.ecr.eu-central-1.amazonaws.com/eks-legion-test/counter-3.3:460c-8f3c-eb3b3d2e1d98'
    )

    assert registry_info == ECRRegistry(id='5555555555', repository_name='eks-legion-test/counter-3.3')


def test_extract_repository_from_ecr_url_invalid_image():
    with pytest.raises(ValueError, match=r".*is invalid ecr image.*"):
        extract_repository_from_ecr_url('docker.io/library/alpine:3.6')
