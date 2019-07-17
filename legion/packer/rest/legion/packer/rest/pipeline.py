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
import os.path
import io
import logging
import shutil
import uuid

import yaml

from .version import __version__
from .constants import *
from .manifest_and_resource import validate_model_manifest, get_model_manifest
from .io_proc_utils import make_executable, run, load_template


def work(model, output_folder, conda_env, ignore_conda, conda_env_name,
         dockerfile, dockerfile_base_image, dockerfile_add_conda_installation, dockerfile_conda_envs_location,
         host, port, timeout, workers, threads):
    """
    Create REST API wrapper (does packaging) from Legion's General Python Prediction Interface (GPPI)

    :param model: Path to Legion's General Python Prediction Interface (GPPI) (zip archive unpacked to folder)
    :type model: str
    :param output_folder: Path to save results to
    :type output_folder: str
    :param conda_env:
    :type conda_env:
    :param ignore_conda:
    :type ignore_conda:
    :param conda_env_name:
    :type conda_env_name:
    :param dockerfile:
    :type dockerfile:
    :param dockerfile_base_image:
    :type dockerfile_base_image:
    :param dockerfile_add_conda_installation:
    :type dockerfile_add_conda_installation:
    :param dockerfile_conda_envs_location:
    :type dockerfile_conda_envs_location:
    :param host: Host to bind HTTP handler on, e.g. '0.0.0.0'
    :type host: str
    :param port: Port to bind HTTP handler on, e.g. 5000
    :type port: int
    :param timeout: Timeout for HTTP connections, in seconds, e.g. 60
    :type timeout: int
    :param workers: Count of worker processes to handle HTTP, e.g. 1.
                    Warning: some models does not work correctly with multiple workers
    :param threads: Count of worker threads to handle HTTP, e.g. 4.
    :return: LegionProjectManifest -- model manifest
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

    # Choose name for conda env name
    env_id = str(uuid.uuid4())
    if conda_env_name:
        logging.info(f'Using specified conda env name {conda_env_name!r} instead of generation')
        env_id = conda_env_name
    else:
        logging.info(f'Conda env name {env_id!r} has been generated')
    conda_dep_list = os.path.join(model, manifest.binaries.conda_path)

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
        conda_prefix = dockerfile_conda_envs_location

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

    # Building of variables for template file and generating of output
    entrypoint_template = load_template(ENTRYPOINT_TEMPLATE)
    entrypoint_docker_template = load_template(ENTRYPOINT_TEMPLATE)
    logging.info(f'Building context for template')
    context = {
        'model_name': manifest.model.name,
        'model_version': manifest.model.version,
        'legion_version': manifest.legionVersion,
        'packer_version': __version__,
        'path': f'{conda_prefix}/bin',
        'path_docker': f'{dockerfile_conda_envs_location}/{env_id}/bin',
        'conda_env_name': env_id,
        'gunicorn_bin': f'{conda_prefix}/bin/gunicorn',
        'gunicorn_bin_docker': f'{dockerfile_conda_envs_location}/{env_id}/bin/gunicorn',
        'timeout': timeout,
        'host': host,
        'port': port,
        'workers': workers,
        'threads': threads,
        'pythonpath': output_folder,
        'wsgi_handler': f'{HANDLER_MODULE}:{HANDLER_APP}',
        'model_location': LEGION_SUB_PATH_NAME,
        'entrypoint_target': ENTRYPOINT_TEMPLATE,
        'handler_file': f'{HANDLER_MODULE}.py',
        'base_image': dockerfile_base_image,
        'conda_installation_content': '',
        'conda_file_name': CONDA_FILE_NAME,
        'entrypoint_docker': ENTRYPOINT_DOCKER_TEMPLATE
    }
    final_entrypoint = entrypoint_template.format(**context)
    final_entrypoint_docker = entrypoint_docker_template.format(**context)

    # Saving formatted string to file
    entrypoint_target = os.path.join(output_folder, ENTRYPOINT_TEMPLATE)
    logging.info(f'Dumping {ENTRYPOINT_TEMPLATE} to {entrypoint_target}')
    with open(entrypoint_target, 'w') as out_stream:
        out_stream.write(final_entrypoint)
    make_executable(entrypoint_target)

    # Save description file
    description_template = load_template(DESCRIPTION_TEMPLATE)
    description_target = os.path.join(output_folder, DESCRIPTION_TEMPLATE)
    logging.info(f'Dumping {DESCRIPTION_TEMPLATE} to {entrypoint_target}')
    description_data = description_template.format(**context)
    with open(description_target, 'w') as out_stream:
        out_stream.write(description_data)

    if dockerfile:
        entrypoint_docker_target = os.path.join(output_folder, ENTRYPOINT_DOCKER_TEMPLATE)
        logging.info(f'Dumping {ENTRYPOINT_DOCKER_TEMPLATE} to {entrypoint_target}')
        with open(entrypoint_docker_target, 'w') as out_stream:
            out_stream.write(final_entrypoint_docker)

        if dockerfile_add_conda_installation:
            conda_installation_content_tpl = load_template(DOCKERFILE_CONDA_INST_INSTRUCTIONS_TEMPLATE)
            conda_installation_content = conda_installation_content_tpl.format(**context)
            context['conda_installation_content'] = conda_installation_content

        dockerfile_template = load_template(DOCKERFILE_TEMPLATE)
        dockerfile_content = dockerfile_template.format(**context)
        dockerfile_target = os.path.join(output_folder, DOCKERFILE_TEMPLATE)
        logging.info(f'Dumping {DOCKERFILE_TEMPLATE} to {dockerfile_target}')

        with open(dockerfile_target, 'w') as out_stream:
            out_stream.write(dockerfile_content)
        make_executable(dockerfile_target)

    return manifest


def build_docker_image(output_folder, local_image_name):
    pass


def push_docker_image(local_image_name, image_name):
    pass

