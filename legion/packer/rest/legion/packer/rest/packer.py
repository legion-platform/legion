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
import os
import os.path
import stat
import io
import typing
import logging
import subprocess
import shutil
import uuid

import click
import yaml
import pydantic

from .version import __version__


PROJECT_FILE = 'legion.project.yaml'
LEGION_SUB_PATH_NAME = 'legion_model'
CONDA_FILE_NAME = 'conda.yaml'
RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), 'resources')
ENTRYPOINT_TEMPLATE = 'entrypoint.sh'
DESCRIPTION_TEMPLATE = 'description.txt'
ENTRYPOINT_DOCKER_TEMPLATE = 'entrypoint.docker.sh'
DOCKERFILE_TEMPLATE = 'Dockerfile'
DOCKERFILE_CONDA_INST_INSTRUCTIONS_TEMPLATE = 'conda.Dockerfile'
HANDLER_MODULE = 'legion_handler'
HANDLER_APP = 'app'


class LegionProjectManifestBinaries(pydantic.BaseModel):
    """
    Legion Project Manifest's Binaries description
    """

    type: str
    dependencies: str
    conda_path: typing.Optional[str]


class LegionProjectManifestModel(pydantic.BaseModel):
    """
    Legion Project Manifest's Model description
    """

    name: str
    version: str
    workDir: str
    entrypoint: str


class LegionProjectManifestToolchain(pydantic.BaseModel):
    """
    Legion Project Manifest's Toolchain description
    """

    name: str
    version: str


class LegionProjectManifest(pydantic.BaseModel):
    """
    Legion Project Manifest description class
    """

    binaries: LegionProjectManifestBinaries
    model: typing.Optional[LegionProjectManifestModel]
    legionVersion: typing.Optional[str]
    toolchain: typing.Optional[LegionProjectManifestToolchain]


class PackagingResourceArguments(pydantic.BaseModel):
    """
    Legion Packaging Resource Arguments
    """

    dockerfilePush: str
    dockerfileAddCondaInstallation: bool
    dockerfileBaseImage: str
    dockerfileCondaEnvsLocation: str
    host: str
    port: int
    timeout: int
    workers: int
    threads: int


class PackagingResource(pydantic.BaseModel):
    """
    Legion Packaging Resource
    """

    arguments: PackagingResourceArguments


def get_model_manifest(model: str) -> LegionProjectManifest:
    """
    Extract model manifest from file to object

    :param model: path to unpacked model (folder)
    :type model: str
    :return: None
    """
    manifest_file = os.path.join(model, PROJECT_FILE)
    if not manifest_file:
        raise Exception(f'Can not find manifest file {manifest_file}')

    try:
        with open(manifest_file, 'r') as manifest_stream:
            data = yaml.load(manifest_stream)
    except yaml.YAMLError as yaml_error:
        raise Exception(f'Can not parse YAML file: {yaml_error}')

    try:
        return LegionProjectManifest(**data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion manifest file is in incorrect format: {valid_error}')


def parse_resource_file(resource_file: str) -> PackagingResource:
    """
    Extract resource information

    :param resource_file: path to resource file
    :type resource_file: str
    :return: None
    """
    try:
        with open(resource_file, 'r') as resource_file_stream:
            data = yaml.load(resource_file_stream)
    except yaml.YAMLError as yaml_error:
        raise Exception(f'Can not parse YAML file: {yaml_error}')

    try:
        return PackagingResource(**data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion resource file is in incorrect format: {valid_error}')


def make_executable(path: str) -> None:
    """
    Make file executable

    :param path: path to file
    :type path: str
    :return: None
    """
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def validate_model_manifest(manifest: LegionProjectManifest) -> None:
    """
    Check that provided Legion Project Manifest is valid for current packer.

    :param manifest: Manifest object
    :type manifest: :py:class:`LegionProjectManifest`
    :raises Exception: If error in Manifest object is present
    :return: None
    """
    if manifest.binaries.type != 'python':
        raise Exception(f'Unsupported model binaries type: {manifest.binaries.type}')

    if manifest.binaries.dependencies != 'conda':
        raise Exception(f'Unsupported model dependencies type: {manifest.binaries.dependencies}')

    if not manifest.model:
        raise Exception('Model section is not set')

    if not manifest.legionVersion:
        raise Exception('legionVersion is not set')

    if not manifest.binaries.conda_path:
        raise Exception('Conda path is not set')


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging instance

    :param verbose: use verbose output
    :type verbose: bool
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(format='[legion][%(levelname)5s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                        level=log_level)


def run(*args: str, cwd=None, stream_output: bool = True):
    """
    Run system command and stream / capture stdout and stderr

    :param args: Commands to run (list). E.g. ['cp, '-R', '/var/www', '/www']
    :type args: :py:class:`typing.List[str]`
    :param cwd: (Optional). Program working directory. Current is used if not provided.
    :type cwd: str
    :param stream_output: (Optional). Flag that enables streaming child process output to stdout and stderr.
    :return: typing.Union[int, typing.Tuple[int, str, str]] -- exit_code (for stream_output mode)
             or exit_code + stdout + stderr.
    """
    args_line = ' '.join(args)
    logging.info(f'Running command "{args_line}"')

    cmd_env = os.environ.copy()
    if stream_output:
        child = subprocess.Popen(args, env=cmd_env, cwd=cwd, universal_newlines=True,
                                 stdin=subprocess.PIPE)
        exit_code = child.wait()
        if exit_code is not 0:
            raise Exception("Non-zero exitcode: %s" % (exit_code))
        return exit_code
    else:
        child = subprocess.Popen(
            args, env=cmd_env, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, universal_newlines=True)
        (stdout, stderr) = child.communicate()
        exit_code = child.wait()
        if exit_code is not 0:
            raise Exception("Non-zero exit code: %s\n\nSTDOUT:\n%s\n\nSTDERR:%s" %
                            (exit_code, stdout, stderr))
        return exit_code, stdout, stderr


def load_template(template_name) -> str:
    """
    Load template from resources folder

    :param template_name: name of template
    :type template_name: str
    :return: str -- template file content
    """
    logging.info(f'Loading template file {template_name} from {RESOURCES_FOLDER}')
    template_path = os.path.join(RESOURCES_FOLDER, template_name)
    with open(template_path, 'r') as template_stream:
        return template_stream.read()


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
    :return: None
    """
    # Use absolute paths
    model = os.path.abspath(model)
    output_folder = os.path.abspath(output_folder)

    # Output status to console
    logging.info(f'Trying to make REST service from model {model} in {output_folder}')

    # Parse and validate manifest
    manifest = get_model_manifest(model)
    validate_model_manifest(manifest)

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


@click.command()
@click.argument('model', type=click.Path())
@click.argument('output_folder', type=click.Path())
@click.option('--conda-env',
              type=click.Choice(['create', 'update'], case_sensitive=False),
              default='create', show_default=True,
              help='Mode for working with env - create new env or update existed')
@click.option('--ignore-conda',
              is_flag=True,
              help='Do not do any actions with conda. It does not affect Dockerfile.')
@click.option('--conda-env-name',
              type=str, default=None, show_default=True,
              help='Set specific conda env name')
@click.option('--dockerfile',
              is_flag=True,
              help='Create Dockerfile in target folder')
@click.option('--dockerfile-add-conda-installation',
              is_flag=True,
              help='Add conda installation section to Dockerfile (may be not compatible with base docker image)')
@click.option('--dockerfile-base-image',
              type=str, default='python:3.6', show_default=True,
              help='Set base image for Dockerfile')
@click.option('--dockerfile-conda-envs-location',
              type=str, default='/opt/conda/envs/', show_default=True,
              help='Location of conda envs in Docker image')
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
    return work(model, output_folder, conda_env, ignore_conda, conda_env_name,
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
    resource_info = parse_resource_file(resource_file)

    return work(model,
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


if __name__ == '__main__':
    work_cli()

