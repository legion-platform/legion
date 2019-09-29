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
import io
import logging
import os.path
import shutil
import uuid

import yaml
from legion.packager.rest.constants import LEGION_SUB_PATH_NAME, RESOURCES_FOLDER, HANDLER_MODULE, CONDA_FILE_NAME, \
    ENTRYPOINT_TEMPLATE, ENTRYPOINT_DOCKER_TEMPLATE, HANDLER_APP, DESCRIPTION_TEMPLATE, \
    DOCKERFILE_CONDA_INST_INSTRUCTIONS_TEMPLATE, DOCKERFILE_TEMPLATE
from legion.packager.rest.data_models import PackagingResourceArguments, LegionProjectManifest
from legion.packager.rest.io_proc_utils import make_executable, run
from legion.packager.rest.manifest_and_resource import validate_model_manifest, get_model_manifest
from legion.packager.rest.template import DockerTemplateContext, render_packager_template
from legion.packager.rest.version import __version__


def work(model, output_folder, conda_env, ignore_conda, conda_env_name,
         dockerfile, arguments: PackagingResourceArguments):
    """
    Create REST API wrapper (does packaging) from Legion's General Python Prediction Interface (GPPI)

    :param arguments:
    :param model: Path to Legion's General Python Prediction Interface (GPPI) (zip archive unpacked to folder)
    :param output_folder: Path to save results to
    :param conda_env:
    :param ignore_conda:
    :param conda_env_name:
    :param dockerfile:
    :return: model manifest
    """
    # Use absolute paths
    model = os.path.abspath(model)
    output_folder = os.path.abspath(output_folder)

    # Output status to console
    logging.info(f'Trying to make REST service from model {model} in {output_folder}')

    # Parse and validate manifest
    manifest = get_model_manifest(model)
    validate_model_manifest(manifest)

    logging.info('Model information - name: %s, version: %s', manifest.model.name, manifest.model.version)
    conda_dep_list = os.path.join(model, manifest.binaries.conda_path)
    # Choose name for conda env name
    context = _generate_template_context(arguments, conda_env,
                                         conda_env_name, ignore_conda,
                                         manifest, output_folder, conda_dep_list)

    # Building of variables for template file and generating of output
    final_entrypoint = render_packager_template(ENTRYPOINT_TEMPLATE, context.dict())
    final_entrypoint_docker = render_packager_template(ENTRYPOINT_DOCKER_TEMPLATE, context.dict())

    # Copying of model to destination subdirectory
    model_location = os.path.join(model, manifest.model.workDir)
    target_model_location = os.path.join(output_folder, LEGION_SUB_PATH_NAME)

    logging.info(f'Copying {model_location} to {target_model_location}')
    shutil.copytree(model_location, target_model_location)

    # Copying of handler function
    handler_location = os.path.join(RESOURCES_FOLDER, f'{HANDLER_MODULE}.py')
    target_handler_location = os.path.join(output_folder, f'{HANDLER_MODULE}.py')

    logging.info(f'Copying handler {handler_location} to {target_handler_location}')
    shutil.copy(handler_location, target_handler_location)

    # Copying of conda env
    target_conda_env_location = os.path.join(output_folder, CONDA_FILE_NAME)
    logging.info(f'Copying handler {conda_dep_list} to {target_conda_env_location}')
    shutil.copy(conda_dep_list, target_conda_env_location)

    # Saving formatted string to file
    entrypoint_target = os.path.join(output_folder, ENTRYPOINT_TEMPLATE)
    logging.info(f'Dumping {ENTRYPOINT_TEMPLATE} to {entrypoint_target}')
    with open(entrypoint_target, 'w') as out_stream:
        out_stream.write(final_entrypoint)
    make_executable(entrypoint_target)

    # Save description file
    description_target = os.path.join(output_folder, DESCRIPTION_TEMPLATE)
    logging.info(f'Dumping {DESCRIPTION_TEMPLATE} to {entrypoint_target}')
    description_data = render_packager_template(DESCRIPTION_TEMPLATE, context.dict())
    with open(description_target, 'w') as out_stream:
        out_stream.write(description_data)

    if dockerfile:
        entrypoint_docker_target = os.path.join(output_folder, ENTRYPOINT_DOCKER_TEMPLATE)
        logging.info(f'Dumping {ENTRYPOINT_DOCKER_TEMPLATE} to {entrypoint_target}')
        with open(entrypoint_docker_target, 'w') as out_stream:
            out_stream.write(final_entrypoint_docker)

        if arguments.dockerfileAddCondaInstallation:
            context.conda_installation_content = render_packager_template(DOCKERFILE_CONDA_INST_INSTRUCTIONS_TEMPLATE,
                                                                          context.dict())

        dockerfile_content = render_packager_template(DOCKERFILE_TEMPLATE, context.dict())
        dockerfile_target = os.path.join(output_folder, DOCKERFILE_TEMPLATE)
        logging.info(f'Dumping {DOCKERFILE_TEMPLATE} to {dockerfile_target}')

        with open(dockerfile_target, 'w') as out_stream:
            out_stream.write(dockerfile_content)
        make_executable(dockerfile_target)

    return manifest


def _generate_template_context(arguments: PackagingResourceArguments,
                               conda_env: str,
                               conda_env_name: str,
                               ignore_conda: bool,
                               manifest: LegionProjectManifest,
                               output_folder: str,
                               conda_dep_list: str) -> DockerTemplateContext:
    """
    Generate Docker packager context for templates
    """
    env_id = str(uuid.uuid4())
    if conda_env_name:
        logging.info(f'Using specified conda env name {conda_env_name!r} instead of generation')
        env_id = conda_env_name
    else:
        logging.info(f'Conda env name {env_id!r} has been generated')

    if not ignore_conda:
        logging.info('Working with local conda installation')
        if conda_env == 'create':
            logging.info(f'Creating conda env with name {env_id!r}')
            run('conda', 'create', '--yes', '-vv', '--name', env_id)
        else:
            logging.info('Ignoring creation of conda env due to passed argument')

        # Install requirements from dep. list
        logging.info(f'Installing mandatory requirements from {conda_dep_list} to {env_id!r}')
        run('conda', 'env', 'update', f'--name={env_id}', f'--file={conda_dep_list}')

        # Export conda env
        logging.info(f'Exporting conda env {env_id}')
        _1, stdout, _2 = run('conda', 'env', 'export', '-n', env_id, stream_output=False)
        buffer = io.StringIO(stdout)
        conda_info = yaml.load(buffer)

        # Get conda prefix, pip list
        conda_prefix = conda_info.get('prefix')

        # Install additional requirements to env (gunicorn)
        logging.info(f'Installing additional packages (gunicorn) in env {env_id} at {conda_prefix}')
        run(f'{conda_prefix}/bin/pip', 'install', 'gunicorn[gevent]')
        run(f'{conda_prefix}/bin/pip', 'install', 'flask')
    else:
        logging.info(f'Local usage of conda has been disabled due to flag specified')
        conda_prefix = arguments.dockerfileCondaEnvsLocation

    logging.info(f'Building context for template')

    return DockerTemplateContext(
        model_name=manifest.model.name,
        model_version=manifest.model.version,
        legion_version=manifest.legionVersion,
        packager_version=__version__,
        path=f'{conda_prefix}/bin',
        path_docker=f'{arguments.dockerfileCondaEnvsLocation}/{env_id}/bin',
        conda_env_name=env_id,
        gunicorn_bin=f'{conda_prefix}/bin/gunicorn',
        gunicorn_bin_docker=f'{arguments.dockerfileCondaEnvsLocation}/{env_id}/bin/gunicorn',
        timeout=arguments.timeout,
        host=arguments.host,
        port=arguments.port,
        workers=arguments.workers,
        threads=arguments.threads,
        pythonpath=output_folder,
        wsgi_handler=f'{HANDLER_MODULE}:{HANDLER_APP}',
        model_location=LEGION_SUB_PATH_NAME,
        entrypoint_target=ENTRYPOINT_TEMPLATE,
        handler_file=f'{HANDLER_MODULE}.py',
        base_image=arguments.dockerfileBaseImage,
        conda_installation_content='',
        conda_file_name=CONDA_FILE_NAME,
        entrypoint_docker=ENTRYPOINT_DOCKER_TEMPLATE
    )
