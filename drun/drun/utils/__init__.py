#
#    Copyright 2017 EPAM Systems
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
Utils
"""
from .utils import _get_auth_credentials_for_external_resource, \
    string_to_bool, normalize_name, send_header_to_stderr, \
    Colors, DockerContainerContext, TemporaryFolder, ExternalFileReader, \
    normalize_external_resource_path, is_local_resource, \
    normalize_name_to_dns_1123, save_file, download_file, get_git_revision, remove_directory, detect_ip
from .template import render_template
