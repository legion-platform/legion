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
import logging
import tempfile

import click
from legion.packager.rest.data_models import PackagingResourceArguments

from legion.packager.rest.constants import TARGET_DOCKER_REGISTRY, TARGET_ARCHIVE_STORAGE, DOCKERFILE_TEMPLATE, \
    PULL_DOCKER_REGISTRY
from legion.packager.rest.docker_builder import build_docker_image
from legion.packager.rest.external_storage import upload_file_to_connection
from legion.packager.rest.io_proc_utils import setup_logging, remove_directory, create_zip_archive
from legion.packager.rest.manifest_and_resource import parse_resource_file, extract_connection_from_resource, \
    save_result
from legion.packager.rest.pipeline import work
from legion.packager.rest.utils import build_archive_name, build_image_name, TemplateNameValues


@click.command()
@click.argument('model', type=click.Path(exists=True, dir_okay=True, readable=True))
@click.argument('resource_file', type=click.Path(exists=True, file_okay=True, readable=True))
@click.option('--verbose',
              is_flag=True,
              help='Verbose output')
def work_resource_file(model, resource_file, verbose):
    setup_logging(verbose)
    resource_info = parse_resource_file(resource_file)
    model_packaging_spec = resource_info.model_packaging.spec
    if not model_packaging_spec.arguments:
        model_packaging_spec.arguments = {}

    arguments = PackagingResourceArguments(**model_packaging_spec.arguments)
    output_folder = tempfile.mkdtemp()
    logging.info('Using %r as temporary directory', output_folder)

    manifest = work(model,
                    output_folder,
                    conda_env='create',
                    ignore_conda=True,
                    conda_env_name='',
                    dockerfile=True,
                    arguments=arguments)

    # Check if archive target is set
    archive_target_connection = extract_connection_from_resource(resource_info, TARGET_ARCHIVE_STORAGE)
    if archive_target_connection:
        zip_output_folder = tempfile.mkdtemp()
        archive_name = build_archive_name(manifest.model.name, manifest.model.version)
        # Create ZIP archive
        archive_path = create_zip_archive(output_folder, archive_name, zip_output_folder)
        # Upload archive
        upload_file_to_connection(archive_path, archive_name, archive_target_connection)
        remove_directory(zip_output_folder)

    # Check if docker target is set
    docker_pull_connection = extract_connection_from_resource(resource_info, PULL_DOCKER_REGISTRY)
    docker_target_connection = extract_connection_from_resource(resource_info, TARGET_DOCKER_REGISTRY)

    image_name = build_image_name(arguments.imageName,
                                  TemplateNameValues(Name=manifest.model.name, Version=manifest.model.version))
    if docker_target_connection:
        # Start docker build & push mechanism
        build_docker_image(output_folder,
                           DOCKERFILE_TEMPLATE,
                           image_name,
                           docker_target_connection,
                           docker_pull_connection)

    logging.info('Removing temporary directory %r', output_folder)
    remove_directory(output_folder)

    save_result(f'{docker_target_connection.spec.uri}/{image_name}')


if __name__ == '__main__':
    work_resource_file()  # pylint: disable=E1120
