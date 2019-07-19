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

from .manifest_and_resource import parse_resource_file, extract_connection_from_resource
from .io_proc_utils import setup_logging, remove_directory, create_zip_archive
from .pipeline import work
from .constants import TARGET_DOCKER_REGISTRY, TARGET_ARCHIVE_STORAGE, DOCKERFILE_TEMPLATE, PULL_DOCKER_REGISTRY
from .utils import build_archive_name, build_image_name
from .external_storage import upload_file_to_connection
from .docker import build_docker_image


@click.command()
@click.argument('model', type=click.Path())
@click.argument('output_folder', type=click.Path())
@click.option('--conda-env',
              type=click.Choice(['create', 'update'], case_sensitive=False),
              default='create', show_default=True,
              help='Mode for working with env - create new env or update existed.')
@click.option('--ignore-conda',
              is_flag=True,
              help='Do not do any actions with conda. It does not affect Dockerfile.')
@click.option('--conda-env-name',
              type=str, default=None, show_default=True,
              help='Set specific conda env name.')
@click.option('--dockerfile',
              is_flag=True,
              help='Create Dockerfile in target folder.')
@click.option('--dockerfile-add-conda-installation',
              is_flag=True,
              help='Add conda installation section to Dockerfile (may be not compatible with base docker image).')
@click.option('--dockerfile-base-image',
              type=str, default='python:3.6', show_default=True,
              help='Set base image for Dockerfile')
@click.option('--dockerfile-conda-envs-location',
              type=str, default='/opt/conda/envs/', show_default=True,
              help='Location of conda envs in Docker image.')
@click.option('--host',
              type=str, default='0.0.0.0', show_default=True)
@click.option('--port',
              type=int, default=5000, show_default=True)
@click.option('--timeout',
              type=int, default=60, show_default=True)
@click.option('--workers',
              type=int, default=1, show_default=True)
@click.option('--threads',
              type=int, default=4, show_default=True)
@click.option('--verbose',
              is_flag=True,
              help='Verbose output')
def work_cli(model, output_folder, conda_env, ignore_conda, conda_env_name,
             dockerfile, dockerfile_base_image, dockerfile_add_conda_installation, dockerfile_conda_envs_location,
             host, port, timeout, workers, threads, verbose):
    """
    Create REST API wrapper (does packaging) from Legion's General Python Prediction Interface (GPPI)
    """
    setup_logging(verbose)
    work(model, output_folder, conda_env, ignore_conda, conda_env_name,
         dockerfile, dockerfile_base_image, dockerfile_add_conda_installation, dockerfile_conda_envs_location,
         host, port, timeout, workers, threads)


@click.command()
@click.argument('model', type=click.Path(exists=True, dir_okay=True, readable=True))
@click.argument('resource_file', type=click.Path(exists=True, file_okay=True, readable=True))
@click.option('--verbose',
              is_flag=True,
              help='Verbose output')
def work_resource_file(model, resource_file, verbose):
    setup_logging(verbose)
    resource_info = parse_resource_file(resource_file).spec

    output_folder = tempfile.mkdtemp()
    logging.info('Using %r as temporary directory', output_folder)

    manifest = work(model,
                    output_folder,
                    conda_env='create',
                    ignore_conda=True,
                    conda_env_name='',
                    dockerfile=True,
                    dockerfile_base_image=resource_info.arguments.dockerfileBaseImage,
                    dockerfile_add_conda_installation=resource_info.arguments.dockerfileAddCondaInstallation,
                    dockerfile_conda_envs_location=resource_info.arguments.dockerfileCondaEnvsLocation,
                    host=resource_info.arguments.host,
                    port=resource_info.arguments.port,
                    timeout=resource_info.arguments.timeout,
                    workers=resource_info.arguments.workers,
                    threads=resource_info.arguments.threads)

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
    if docker_target_connection:
        # Start docker build & push mechanism
        image_name = build_image_name(manifest.model.name, manifest.model.version)
        build_docker_image(output_folder,
                           DOCKERFILE_TEMPLATE,
                           image_name,
                           docker_target_connection,
                           docker_pull_connection)

    logging.info('Removing temporary directory %r', output_folder)
    remove_directory(output_folder)


if __name__ == '__main__':
    work_cli()

