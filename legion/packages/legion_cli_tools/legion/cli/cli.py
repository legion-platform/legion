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
CLI logic for legion
"""
import argparse
import logging
import os
import stat
import sys
import time

import legion.core.config
import legion.core.containers.docker
import legion.core.containers.definitions
import legion.core.containers.headers
import legion.core.external.edi
import legion.core.external.grafana
import legion.core.model
import legion.core.utils
import legion.cli.template
import legion.services.k8s
import legion.services.edi.security
import legion.services.serving.pyserve
from legion.core.utils import Colors

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def output_table(headers, rows):
    """
    Output table to console

    :param headers: list of header names
    :type headers: list[str]
    :param rows: list of rows
    :type rows: list[list[any]]
    :return: None
    """
    columns_width = [max(len(str(row[col_idx])) for row in rows) for col_idx, column in enumerate(headers)]
    columns_width = [max(columns_width[col_idx], len(column)) for col_idx, column in enumerate(headers)]

    print('|'.join('{name:{width}} '.format(name=column, width=columns_width[col_idx])
                   for col_idx, column in enumerate(headers)))
    for row in rows:
        print('|'.join('{name:{width}} '.format(name=str(column_value), width=columns_width[col_idx])
                       for col_idx, column_value in enumerate(row)))


def generate_token(args):
    """
    Generate JWT for specified model

    :param args: command arguments
    :type args: argparse.Namespace
    :return: str -- token
    """
    edi_client = legion.external.edi.build_client(args)
    token = edi_client.get_token(args.model_id, args.model_version, args.expiration_date)
    print(token)


def inspect(args):
    """
    Inspect models on remote cluster or local machine

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    LOGGER.info('Sending inspect request to {!r}'.format(edi_client))
    model_deployments = edi_client.inspect(args.model_id, args.model_version)

    data = []

    for deployment in model_deployments:
        if deployment.status == 'ok' and deployment.model_api_ok:
            line_color = Colors.OKGREEN
        elif deployment.status == 'warning':
            line_color = Colors.WARNING
        else:
            line_color = Colors.FAIL

        errors = ''

        if not deployment.model_api_ok:
            errors = 'MODEL API DOES NOT RESPOND'

        if errors:
            errors = 'ERROR: {}'.format(errors)

        data.append({
            'deployment': deployment,
            'errors': errors,
            'line_color': line_color
        })

    if args.format == INSPECT_FORMAT_COLORIZED:
        if data:
            print('{}Model deployments:{}'.format(Colors.BOLD, Colors.ENDC))

            for item in data:
                deploy_mode = item['deployment'].deploy_mode
                if deploy_mode == legion.core.containers.definitions.ModelDeploymentDescription.MODE_LOCAL:
                    api_url = '{}:{}'.format(legion.core.config.LOCAL_DEPLOY_HOSTNAME,
                                             item['deployment'].local_port)
                    print('{}* [LOCAL]{} {}{}{} (ver. {}) container: {} api: {} image: {} {}{}{}'.format(
                        item['line_color'], Colors.ENDC,
                        Colors.UNDERLINE, item['deployment'].model, Colors.ENDC, item['deployment'].version,
                        item['deployment'].container_id, api_url,
                        item['deployment'].image,
                        item['line_color'], item['errors'],
                        Colors.ENDC
                    ))
                elif deploy_mode == legion.core.containers.definitions.ModelDeploymentDescription.MODE_CLUSTER:
                    print('{}* [CLUSTER]{} {}{}{} (ver. {}) image: {} {}{}/{} pods ready {}{}'.format(
                        item['line_color'], Colors.ENDC,
                        Colors.UNDERLINE, item['deployment'].model, Colors.ENDC, item['deployment'].version,
                        item['deployment'].image,
                        item['line_color'], item['deployment'].ready_replicas, item['deployment'].scale, item['errors'],
                        Colors.ENDC
                    ))
                else:
                    print('Unknown deployment mode {}'.format(deploy_mode))

        if not model_deployments:
            print('{}-- cannot find any model deployments --{}'.format(Colors.WARNING, Colors.ENDC))

        if not data and model_deployments:
            print('{}-- cannot find any model deployments after filtering --{}'.format(Colors.WARNING, Colors.ENDC))
    elif args.format == INSPECT_FORMAT_TABULAR:
        headers = 'Model ID', 'Version', 'Deploy Mode', 'Container', 'Local Port', 'Image', 'Ready', 'Scale', 'Errors'
        items = [[
            item['deployment'].model,
            item['deployment'].version,
            item['deployment'].deploy_mode,
            item['deployment'].container_id,
            item['deployment'].local_port,
            item['deployment'].image,
            str(item['deployment'].ready_replicas),
            str(item['deployment'].scale),
            item['errors'],
        ] for item in data]

        if data:
            output_table(headers, items)


def get_related_model_deployments(client, affected_deployments):
    """
    Get actual status of model deployments

    :param client: EDI client
    :type client: :py:class:`legion.external.edi.EdiClient`
    :param affected_deployments: affected by main operation (e.g. deploy) model deployments
    :type affected_deployments: list[:py:class:`legion.core.containers.k8s.ModelDeploymentDescription`]
    :return: list[:py:class:`legion.core.containers.k8s.ModelDeploymentDescription`] -- actual status of model deployments
    """
    affected_deployment_ids = {
        deployment.id_and_version
        for deployment
        in affected_deployments
    }
    actual_deployments_status = client.inspect()
    LOGGER.debug('Filtering all models using affected deployment list')
    return [deployment
            for deployment in actual_deployments_status
            if deployment.id_and_version in affected_deployment_ids]


def wait_operation_finish(args, edi_client, model_deployments, wait_callback):
    """
    Wait operation to finish according command line arguments. Uses wait_callback for checking status

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :param edi_client: EDI client instance
    :type edi_client: :py:class:`legion.external.edi.EdiClient`
    :param model_deployments: models that have been affected during operation call
    :type model_deployments: list[:py:class:`legion.core.containers.k8s.ModelDeploymentDescription`]
    :param wait_callback: function that will be called to ensure that operation completed (should return True)
    :type wait_callback: py:class:`Callable[[list[:py:class:`legion.core.containers.k8s.ModelDeploymentDescription`]],
                                            typing.Optional[bool]]`
    :return: None
    """
    if not args.no_wait:
        start = time.time()
        if args.timeout <= 0:
            raise Exception('Invalid --timeout argument: should be positive integer')

        LOGGER.debug('Starting checking cycle limited to {} s.'.format(args.timeout))

        while True:
            elapsed = time.time() - start
            if elapsed > args.timeout:
                raise Exception('Time out: operation has not been confirmed')

            LOGGER.info('Requesting actual status of affected deployments')
            affected_deployments_status = get_related_model_deployments(edi_client, model_deployments)
            LOGGER.debug('Server returned list of actual affected deployment statuses: {!r}'
                         .format(affected_deployments_status))

            result = wait_callback(affected_deployments_status)
            if result:
                LOGGER.info('Callback have confirmed completion of the operation')
                break
            else:
                LOGGER.info('Callback have not confirmed completion of the operation')

            LOGGER.debug('Sleep before next request')
            time.sleep(1)


def check_all_scaled(deployments_status, expected_scale, expected_count):
    """
    Check that all model finished scale process and now are OK

    :param deployments_status: actual deployment status
    :type deployments_status: list[:py:class:`legion.core.containers.k8s.ModelDeploymentDescription`]
    :param expected_scale: expected scale
    :type expected_scale: int
    :param expected_count: expected count of models
    :type expected_count: int
    :return: bool -- result of validation
    """
    # Get fully deployed models
    finally_deployed_models = [deployment
                               for deployment in deployments_status
                               if deployment.ready_replicas == expected_scale and deployment.model_api_ok]

    # Wait until all modes will be scaled
    return len(finally_deployed_models) == expected_count


def undeploy(args):
    """
    Undeploy model from remote cluster or on local machine

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    LOGGER.info('Sending undeploy request to {!r}'.format(edi_client))
    model_deployments = edi_client.undeploy(args.model_id,
                                            args.grace_period,
                                            args.model_version,
                                            args.ignore_not_found)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: not affected_deployments_status)


def scale(args):
    """
    Scale model instances on remote cluster

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    LOGGER.info('Sending scale request to {!r}'.format(edi_client))
    model_deployments = edi_client.scale(args.model_id, args.scale, args.model_version)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: check_all_scaled(affected_deployments_status,
                                                                               args.scale,
                                                                               len(model_deployments)))


def deploy(args):
    """
    Deploy model on remote cluster or on local machine

    :param args: command arguments with .model_id, .namespace, .livenesstimeout, .readinesstimeout, .model_iam_role,
                 .port, .memory, .cpu and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    LOGGER.info('Sending deploy request to {!r}'.format(edi_client))
    model_deployments = edi_client.deploy(args.image, model_iam_role=args.model_iam_role, count=args.scale,
                                          livenesstimeout=args.livenesstimeout, readinesstimeout=args.readinesstimeout,
                                          local_port=args.port, memory=args.memory, cpu=args.cpu)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: check_all_scaled(affected_deployments_status,
                                                                               args.scale,
                                                                               len(model_deployments)))


def sandbox(args):
    """
    Create local sandbox
    It generates bash script to run sandbox


    :param args: command arguments with .image, .force_recreate
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    work_directory = '/work-directory'

    local_fs_work_directory = os.path.abspath(os.getcwd())

    legion_data_directory = '/opt/legion/'
    model_file = 'model.bin'

    arguments = dict(
        local_fs=local_fs_work_directory,
        image=args.image,
        work_directory=work_directory,
        legion_data_directory=legion_data_directory,
        model_file=model_file,
        remove_arguments='--rm' if legion.core.config.SANDBOX_CREATE_SELF_REMOVING_CONTAINER else '',
        docker_socket_path=legion.core.config.SANDBOX_DOCKER_MOUNT_PATH
    )
    cmd = legion.utils.render_template('sandbox-cli.sh.tmpl', arguments)

    path_to_activate = os.path.abspath(os.path.join(os.getcwd(), 'legion-activate.sh'))

    if os.path.exists(path_to_activate) and not args.force_recreate:
        print('File {} already existed, ignoring creation of sandbox'.format(path_to_activate))
        return

    with open(path_to_activate, 'w') as activate_file:
        activate_file.write(cmd)

    current_mode = os.stat(path_to_activate)
    os.chmod(path_to_activate, current_mode.st_mode | stat.S_IEXEC)

    print('Sandbox has been created!')
    print('To activate run {!r} from command line'.format(path_to_activate))


def list_dependencies(_):
    """
    Print package dependencies

    :param _: command arguments
    :type _: :py:class:`argparse.Namespace`
    :return: None
    """
    dependencies = legion.utils.get_list_of_requirements()
    for name, version in dependencies:
        print('{}=={}'.format(name, version))


def _check_variable_exists_or_exit(name):
    """
    Check that variable with desired name exists or print error message and exit with code 1

    :param name: name of variable, case-sensitive
    :type name: str
    :return: None
    """
    if name not in legion.core.config.ALL_VARIABLES:
        print('Variable {!r} is unknown'.format(name))
        sys.exit(1)


def _print_variable_information(name, show_secrets=False):
    """
    Print information about variable to console

    :param name: name of variable, case-sensitive
    :type name: str
    :param show_secrets: (Optional) do not mask credentials
    :type show_secrets: bool
    :return: None
    """
    description = legion.core.config.ALL_VARIABLES[name]
    current_value = getattr(legion.core.config, name)
    is_secret = any(sub in name for sub in ('_PASSWORD', '_TOKEN'))
    print('{} - {}\n  default: {!r}'.format(name, description.description, description.default))
    if current_value != description.default:
        if is_secret and not show_secrets:
            current_value = '****'
        print('  current: {!r}'.format(current_value))


def config_set(args):
    """
    Set configuration variable

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    variable_name = args.key.upper()
    _check_variable_exists_or_exit(variable_name)

    if not legion.core.config.ALL_VARIABLES[variable_name].configurable_manually:
        raise Exception('Variable {} is not configurable manually'.format(variable_name))

    legion.core.config.update_config_file(**{variable_name: args.value})

    _print_variable_information(variable_name, True)


def config_get(args):
    """
    Get configuration variable

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    variable_name = args.key.upper()
    _check_variable_exists_or_exit(variable_name)

    _print_variable_information(variable_name, args.show_secrets)


def config_get_all(args):
    """
    Get all configuration variables

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    configurable_values = filter(lambda i: i[1].configurable_manually, legion.core.config.ALL_VARIABLES.items())
    non_configurable_values = filter(lambda i: not i[1].configurable_manually, legion.core.config.ALL_VARIABLES.items())

    print('Configurable manually variables:\n===========================')
    for name, _ in configurable_values:
        _print_variable_information(name, args.show_secrets)

    if args.with_system:
        print('\n\n')

        print('System variables:\n===========================')
        for name, _ in non_configurable_values:
            _print_variable_information(name, args.show_secrets)


def config_path(_):
    """
    Get configuration storage path

    :param _: command arguments
    :type _: :py:class:`argparse.Namespace`
    :return: None
    """
    print(legion.core.config.get_config_file_path())


def configure_logging(args):
    """
    Set appropriate log level

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    if args.verbose or legion.core.config.DEBUG:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        stream=sys.stderr)


def build_parser():  # pylint: disable=R0915
    """
    Build parser for CLI

    :return: (:py:class:`argparse.ArgumentParser`, py:class:`argparse._SubParsersAction`)  -- CLI parser for LegionCTL
    """
    parser = argparse.ArgumentParser(description='legion Command-Line Interface')
    parser.add_argument('--verbose',
                        help='verbose log output',
                        action='store_true')
    parser.add_argument('--version',
                        help='get package version',
                        action='store_true')
    subparsers = parser.add_subparsers()

    # --------- SECURITY SECTION -----------
    login_parser = subparsers.add_parser('login', description='Save edi credentials to the config')
    legion.edi.security.add_edi_arguments(login_parser, required=True)
    login_parser.set_defaults(func=legion.edi.security.login)

    generate_token_parser = subparsers.add_parser('generate-token', description='generate JWT token for model')
    generate_token_parser.add_argument('--model-id', type=str, help='Model ID')
    generate_token_parser.add_argument('--model-version', type=str, help='Model version')
    generate_token_parser.add_argument('--expiration-date', type=str,
                                       help='Token expiration date in utc: %Y-%m-%dT%H:%M:%S')
    legion.edi.security.add_edi_arguments(generate_token_parser)
    generate_token_parser.set_defaults(func=generate_token)

    # --------- KUBERNETES SECTION -----------
    deploy_parser = subparsers.add_parser('deploy',
                                          description='deploys a model into a kubernetes cluster')
    deploy_parser.add_argument('image',
                               type=str, help='docker image')
    deploy_parser.add_argument('--local',
                               action='store_true',
                               help='deploy model locally. Incompatible with other arguments')
    deploy_parser.add_argument('--port',
                               default=0,
                               type=int, help='port to listen on. Only for --local mode')
    deploy_parser.add_argument('--model-iam-role',
                               type=str, help='IAM role to be used at model pod')
    deploy_parser.add_argument('--scale',
                               default=1,
                               type=int, help='count of instances')
    deploy_parser.add_argument('--livenesstimeout',
                               default=2,
                               type=int, help='model startup timeout for liveness probe')
    deploy_parser.add_argument('--readinesstimeout',
                               default=2,
                               type=int, help='model startup timeout for readiness probe')
    deploy_parser.add_argument('--memory', default=None, type=str, help='limit memory for model deployment')
    deploy_parser.add_argument('--cpu', default=None, type=str, help='limit cpu for model deployment')
    legion.external.edi.add_arguments_for_wait_operation(deploy_parser)
    legion.edi.security.add_edi_arguments(deploy_parser)
    deploy_parser.set_defaults(func=deploy)

    inspect_parser = subparsers.add_parser('inspect',
                                           description='get information about currently deployed models')
    inspect_parser.add_argument('--model-id',
                                type=str, help='model ID')
    inspect_parser.add_argument('--model-version',
                                type=str, help='model version')
    inspect_parser.add_argument('--format',
                                default=VALID_INSPECT_FORMATS[0],
                                choices=VALID_INSPECT_FORMATS, help='output format')
    inspect_parser.add_argument('--local',
                                action='store_true',
                                help='analyze local deployed models')
    legion.edi.security.add_edi_arguments(inspect_parser)
    inspect_parser.set_defaults(func=inspect)

    scale_parser = subparsers.add_parser('scale',
                                         description='change count of model pods')
    scale_parser.add_argument('model_id',
                              type=str, help='model ID')
    scale_parser.add_argument('scale',
                              type=int, help='new count of replicas')
    scale_parser.add_argument('--model-version',
                              type=str, help='model version')
    legion.external.edi.add_arguments_for_wait_operation(scale_parser)
    legion.edi.security.add_edi_arguments(scale_parser)
    scale_parser.set_defaults(func=scale)

    undeploy_parser = subparsers.add_parser('undeploy',
                                            description='undeploy model deployment')
    undeploy_parser.add_argument('model_id',
                                 type=str, help='model ID')
    undeploy_parser.add_argument('--model-version',
                                 type=str, help='model version')
    undeploy_parser.add_argument('--grace-period',
                                 default=0,
                                 type=int, help='removal grace period')
    undeploy_parser.add_argument('--ignore-not-found',
                                 action='store_true', help='ignore if cannot found pod')
    undeploy_parser.add_argument('--local',
                                 action='store_true',
                                 help='un-deploy local deployed model. Incompatible with --grace-period')
    legion.external.edi.add_arguments_for_wait_operation(undeploy_parser)
    legion.edi.security.add_edi_arguments(undeploy_parser)
    undeploy_parser.set_defaults(func=undeploy)

    # --------- LOCAL SECTION -----------
    sandbox_parser = subparsers.add_parser('create-sandbox', description='create sandbox')
    sandbox_parser.add_argument('--image',
                                type=str,
                                default=legion.core.config.SANDBOX_PYTHON_TOOLCHAIN_IMAGE,
                                help='explicitly set toolchain python image')
    sandbox_parser.add_argument('--force-recreate',
                                action='store_true',
                                help='recreate sandbox if it already existed')
    sandbox_parser.set_defaults(func=sandbox)

    # --------- UTILS SECTION -----------
    list_dependencies_parser = subparsers.add_parser('list-dependencies', description='list package dependencies')
    list_dependencies_parser.set_defaults(func=list_dependencies)

    config_parser = subparsers.add_parser('config', description='manipulate config')
    config_subparsers = config_parser.add_subparsers()

    config_set_parser = config_subparsers.add_parser('set', description='set configuration variable')
    config_set_parser.add_argument('key', type=str, help='variable name')
    config_set_parser.add_argument('value', type=str, help='variable value')
    config_set_parser.set_defaults(func=config_set)

    config_get_parser = config_subparsers.add_parser('get', description='get configuration variable')
    config_get_parser.add_argument('key', type=str, help='variable name')
    config_get_parser.add_argument('--show-secrets', action='store_true', help='show tokens and passwords')
    config_get_parser.set_defaults(func=config_get)

    config_get_all_parser = config_subparsers.add_parser('get-all', description='get all configuration variables')
    config_get_all_parser.add_argument('--show-secrets', action='store_true', help='show tokens and passwords')
    config_get_all_parser.add_argument('--with-system', action='store_true', help='show with system variables')
    config_get_all_parser.set_defaults(func=config_get_all)

    config_path_parser = config_subparsers.add_parser('path', description='get configuration location')
    config_path_parser.set_defaults(func=config_path)

    # --------- END OF SECTIONS -----------

    return parser, subparsers
