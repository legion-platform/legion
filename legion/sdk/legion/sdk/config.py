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
legion env names
"""
import configparser
import os
from pathlib import Path
import logging

# Get list of all variables
ALL_VARIABLES = {}

_LOGGER = logging.getLogger()

_INI_FILE_TRIED_TO_BE_LOADED = False
_INI_FILE_CONTENT: configparser.ConfigParser = None
_INI_FILE_DEFAULT_CONFIG_PATH = Path.home().joinpath('.legion/config')
_DEFAULT_INI_SECTION = 'general'
MODEL_JWT_TOKEN_SECTION = 'model_tokens'


def reset_context():
    """
    Reset configuration context

    :return: None
    """
    global _INI_FILE_TRIED_TO_BE_LOADED
    global _INI_FILE_CONTENT

    _INI_FILE_TRIED_TO_BE_LOADED = False
    _INI_FILE_CONTENT = None


def get_config_file_path():
    """
    Return the config path.
    LEGION_CONFIG environment can override path value

    :return: Path -- config path
    """
    config_path_from_env = os.getenv('LEGION_CONFIG')

    return Path(config_path_from_env) if config_path_from_env else _INI_FILE_DEFAULT_CONFIG_PATH


def _load_config_file():
    """
    Load configuration file if it has not been loaded. Update _INI_FILE_TRIED_TO_BE_LOADED, _INI_FILE_CONTENT

    :return: None
    """
    global _INI_FILE_TRIED_TO_BE_LOADED

    if _INI_FILE_TRIED_TO_BE_LOADED:
        return

    config_path = get_config_file_path()
    _INI_FILE_TRIED_TO_BE_LOADED = True

    _LOGGER.debug('Trying to load configuration file {}'.format(config_path))

    try:
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(str(config_path))

            global _INI_FILE_CONTENT
            _INI_FILE_CONTENT = config

            _LOGGER.debug('Configuration file {} has been loaded'.format(config_path))
        else:
            _LOGGER.debug('Cannot find configuration file {}'.format(config_path))
    except Exception as exc:
        _LOGGER.exception('Cannot read config file {}'.format(config_path), exc_info=exc)


def get_config_file_section(section=_DEFAULT_INI_SECTION, silent=False):
    """
    Get section from config file

    :param section: (Optional) name of section
    :type section: str
    :param silent: (Optional) ignore if there is no file
    :type silent: bool
    :return: dict[str, str] -- values from section
    """
    _load_config_file()
    if not _INI_FILE_CONTENT:
        if silent:
            return dict()
        else:
            raise Exception('Configuration file cannot be loaded')

    if not _INI_FILE_CONTENT.has_section(section):
        return {}

    return dict(_INI_FILE_CONTENT[section])


def get_config_file_variable(variable, section=_DEFAULT_INI_SECTION):
    """
    Get variable by name from specific (or default) section

    :param variable: Name of variable
    :type variable: str
    :param section: (Optional) name of section
    :type section: str
    :return: str or None -- value
    """
    if not variable:
        return None

    _load_config_file()
    if not _INI_FILE_CONTENT:
        return None

    return _INI_FILE_CONTENT.get(section, variable, fallback=None)


def update_config_file(section=_DEFAULT_INI_SECTION, **new_values):
    """
    Update config file with new values

    :param section: (Optional) name of section to update
    :type section: str
    :param new_values: new values
    :type new_values: dict[str, str]
    :return: None
    """
    global _INI_FILE_TRIED_TO_BE_LOADED
    global _INI_FILE_CONTENT

    _load_config_file()
    config_path = get_config_file_path()

    content = _INI_FILE_CONTENT if _INI_FILE_CONTENT else configparser.ConfigParser()

    config_path.parent.mkdir(mode=0o775, parents=True, exist_ok=True)
    config_path.touch(mode=0o600, exist_ok=True)

    if not content.has_section(section):
        content.add_section(section)

    for key, value in new_values.items():
        content.set(section, key, value)

    with config_path.open('w') as config_file:
        content.write(config_file)

    _INI_FILE_TRIED_TO_BE_LOADED = True
    _INI_FILE_CONTENT = content

    reinitialize_variables()

    _LOGGER.debug('Configuration file {} has been updated'.format(config_path))


def _load_variable(name, cast_type=None, configurable_manually=True):
    """
    Load variable from config file, env. Cast it to desired type.

    :param name: name of variable
    :type name: str
    :param cast_type: (Optional) function to cast
    :type cast_type: Callable[[str], any]
    :param configurable_manually: (Optional) could this variable be configured manually or not
    :type configurable_manually: bool
    :return: Any -- variable value
    """
    value = None

    # 1st level - configuration file
    if configurable_manually:
        conf_value = get_config_file_variable(name)
        if conf_value:
            value = conf_value

    # 2nd level - env. variable
    env_value = os.environ.get(name)
    if env_value:
        value = env_value

    return cast_type(value) if value is not None else None


class ConfigVariableInformation:
    """
    Object holds information about variable (name, default value, casting function, description and etc.)
    """

    def __init__(self, name, default, cast_func, description, configurable_manually):
        """
        Build information about variable

        :param name: name of variable
        :type name: str
        :param default: default value
        :type default: Any
        :param cast_func: cast function
        :type cast_func: Callable[[str], any]
        :param description: description
        :type description: str
        :param configurable_manually: is configurable manually
        :type configurable_manually: bool
        """
        self._name = name
        self._default = default
        self._cast_func = cast_func
        self._description = description
        self._configurable_manually = configurable_manually

    @property
    def name(self):
        """
        Get name of variable

        :return: str -- name
        """
        return self._name

    @property
    def default(self):
        """
        Get default variable value

        :return: Any -- default value
        """
        return self._default

    @property
    def cast_func(self):
        """
        Get cast function (from string to desired type)

        :return: Callable[[str], any] -- casting function
        """
        return self._cast_func

    @property
    def description(self):
        """
        Get human-readable description

        :return: str -- description
        """
        return self._description

    @property
    def configurable_manually(self):
        """
        Is this variable human-configurabe?

        :return: bool -- is human configurable
        """
        return self._configurable_manually


def cast_bool(value):
    """
    Convert string to bool

    :param value: string or bool
    :type value: str or bool
    :return: bool
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    return value.lower() in ['true', '1', 't', 'y', 'yes']


def reinitialize_variables():
    """
    Reinitialize variables due to new ENV variables

    :return: None
    """
    for value_information in ALL_VARIABLES.values():
        explicit_value = _load_variable(value_information.name,
                                        value_information.cast_func,
                                        value_information.configurable_manually)
        value = explicit_value if explicit_value is not None else value_information.default

        globals()[value_information.name] = value


class ConfigVariableDeclaration:
    """
    Class that builds declaration of variable (and returns it's value as an instance)
    """

    def __new__(cls, name, default=None, cast_func=str, description=None, configurable_manually=True):
        """
        Create new instance

        :param name: name of variable
        :type name: str
        :param default: (Optional) default variable value [will not be passed to cast_func]
        :type default: Any
        :param cast_func: (Optional) cast function for variable value
        :type cast_func: Callable[[str], any]
        :param description: (Optional) human-readable variable description
        :type description: str
        :param configurable_manually: (Optional) can be modified by config file or CLI
        :type configurable_manually: bool
        :return: Any -- default or explicit value
        """
        information = ConfigVariableInformation(name, default, cast_func, description, configurable_manually)

        explicit_value = _load_variable(name, cast_func, configurable_manually)
        value = explicit_value if explicit_value is not None else default
        ALL_VARIABLES[information.name] = information
        return value


# Verbose tracing
DEBUG = ConfigVariableDeclaration('DEBUG', False, cast_bool,
                                  'Enable verbose program output',
                                  True)

# Model building information
BUILD_NUMBER = ConfigVariableDeclaration('BUILD_NUMBER', 0, int,
                                         'Number of current build. It is used in model saving (during training)',
                                         False)
BUILD_ID = ConfigVariableDeclaration('BUILD_ID', None, str,
                                     'ID of current build. It is used in model saving (during training)',
                                     False)
BUILD_URL = ConfigVariableDeclaration('BUILD_URL', None, str,
                                      'URL of current build. It is used in model saving (during training)',
                                      False)
BUILD_TAG = ConfigVariableDeclaration('BUILD_TAG', None, str,
                                      'TAG of current build. It is used in model saving (during training)',
                                      False)

GIT_COMMIT = ConfigVariableDeclaration('GIT_COMMIT', None, str,
                                       'Git commit of source code. It is used in model saving (during training)',
                                       False)
GIT_BRANCH = ConfigVariableDeclaration('GIT_BRANCH', None, str,
                                       'Git branch of source code. It is used in model saving (during training)',
                                       False)

JOB_NAME = ConfigVariableDeclaration('JOB_NAME', None, str,
                                     'Name of train job [Jenkins]. It is used in model saving (during training)',
                                     False)
NODE_NAME = ConfigVariableDeclaration('NODE_NAME', None, str,
                                      'Name of node [Jenkins]. It is used in model saving (during training)',
                                      False)

MODEL_DOCKER_BUILDER_URL = ConfigVariableDeclaration('MODEL_DOCKER_BUILDER_URL', 'http://127.0.0.1:8080', str,
                                                     'URL of the docker builder sidecar', False)

# Model invocation testing
MODEL_SERVER_URL = ConfigVariableDeclaration('MODEL_SERVER_URL', '', str, 'Default url of model server', True)

MODEL_PREFIX_URL = ConfigVariableDeclaration('MODEL_PREFIX_URL', '', str, 'Default prefix url of model server', True)

MODEL_HOST = ConfigVariableDeclaration('MODEL_HOST', '', str, 'Default host of model server', True)

MODEL_DEPLOYMENT_NAME = ConfigVariableDeclaration('MODEL_DEPLOYMENT_NAME', '', str, 'Model deployment name', True)

MODEL_ROUTE_NAME = ConfigVariableDeclaration('MODEL_ROUTE_NAME', '', str, 'Model deployment name', True)

MODEL_JWT_TOKEN = ConfigVariableDeclaration('MODEL_JWT_TOKEN', False, str,
                                            'Model jwt token for access to the model', True)

# Building and serving
MODEL_FILE = ConfigVariableDeclaration('MODEL_FILE', None, str,
                                       'Binary model file location. It is used in model building',
                                       False)

# Training metrics
MODEL_CLUSTER_TRAIN_METRICS_ENABLED = ConfigVariableDeclaration(
    'MODEL_CLUSTER_TRAIN_METRICS_ENABLED', False, cast_bool, 'Send model metrics on train', False
)
MODEL_LOCAL_METRIC_STORE = ConfigVariableDeclaration(
    'MODEL_LOCAL_METRIC_STORE', '.legion/build_metric_store.json', str,
    'File name where model build metric are saved', True
)
METRICS_HOST = ConfigVariableDeclaration('METRICS_HOST', 'graphite', str,
                                         'Host that gets train metrics. It is used during model training', False)
METRICS_PORT = ConfigVariableDeclaration('METRICS_PORT', 9125, int,
                                         'Port that gets train metrics. It is used during model training', False)

# API for models
LEGION_ADDR = ConfigVariableDeclaration('LEGION_ADDR', '0.0.0.0', str,
                                        'Address to listen Legion model endpoint',
                                        False)
LEGION_PORT = ConfigVariableDeclaration('LEGION_PORT', 5000, str,
                                        'Port to listen Legion model endpoint',
                                        False)

# API for services
LEGION_API_ADDR = ConfigVariableDeclaration('LEGION_API_ADDR', '0.0.0.0', str,
                                            'Address to listen Legion service endpoint',
                                            False)
LEGION_API_PORT = ConfigVariableDeclaration('LEGION_API_PORT', 5001, int,
                                            'Port to listen Legion service endpoint',
                                            False)

# EDI endpoint
EDI_URL = ConfigVariableDeclaration('EDI_URL', None, str,
                                    'URL of EDI server',
                                    True)
EDI_TOKEN = ConfigVariableDeclaration('EDI_TOKEN', None, str,
                                      'Token for EDI server authorisation',
                                      True)
EDI_REFRESH_TOKEN = ConfigVariableDeclaration('EDI_REFRESH_TOKEN', None, str,
                                              'Refresh token',
                                              True)
EDI_ACCESS_TOKEN = ConfigVariableDeclaration('EDI_ACCESS_TOKEN', None, str,
                                             'Access token',
                                             True)
EDI_ISSUING_URL = ConfigVariableDeclaration('EDI_ISSUING_URL', None, str,
                                            'URL for refreshing and issuing tokens',
                                            True)

LOCAL_DEFAULT_RESOURCE_PREFIX = ConfigVariableDeclaration('LOCAL_DEFAULT_RESOURCE_PREFIX', None, str,
                                                          'Prefix for building local model binary storage path',
                                                          False)

# Images registry
MODEL_IMAGES_REGISTRY_HOST = ConfigVariableDeclaration('MODEL_IMAGES_REGISTRY_HOST', None, str,
                                                       'Default registry for EDI server',
                                                       False)

# Configuration about storing built docker images
DOCKER_REGISTRY = ConfigVariableDeclaration('DOCKER_REGISTRY', None, str,
                                            'Name of default nexus registry for saving built models', True)
DOCKER_REGISTRY_USER = ConfigVariableDeclaration('DOCKER_REGISTRY_USER', None, str,
                                                 'Docker API user (for saving built model images)', True)
DOCKER_REGISTRY_PASSWORD = ConfigVariableDeclaration('DOCKER_REGISTRY_PASSWORD', None, str,
                                                     'Docker API password (for saving built model images)', True)
DOCKER_REGISTRY_PROTOCOL = ConfigVariableDeclaration('DOCKER_REGISTRY_PROTOCOL', 'https', str,
                                                     'Docker registry protocol: https/http', True)

# EDI server configuration
CLUSTER_CONFIG_PATH = ConfigVariableDeclaration('CLUSTER_CONFIG_PATH', None, str,
                                                'Path to cluster config file for EDI service',
                                                False)
CLUSTER_SECRETS_PATH = ConfigVariableDeclaration('CLUSTER_SECRETS_PATH', None, str,
                                                 'Path to cluster secrets folder for EDI service',
                                                 False)
JWT_CONFIG_PATH = ConfigVariableDeclaration('JWT_CONFIG_PATH', None, str,
                                            'Path to JWT config folder',
                                            False)

# EDI and Model invocation configuration control
FLASK_APP_SETTINGS_FILES = ConfigVariableDeclaration('FLASK_APP_SETTINGS_FILES', None, str,
                                                     'Path to flask\'s configuration file',
                                                     False)

# Model deploying configuration
MODEL_INSTANCE_SERVICE_ACCOUNT_NAME = ConfigVariableDeclaration('MODEL_INSTANCE_SERVICE_ACCOUNT_NAME', 'model', str,
                                                                'Name of K8S ServiceAccount for model instances',
                                                                False)

# Model execution control
MODEL_PROPERTIES_CACHE_TTL = ConfigVariableDeclaration('MODEL_PROPERTIES_CACHE_TTL', 10, int,
                                                       'TTL of in-memory model properties cache',
                                                       False)

# Kubernetes API
NAMESPACE = ConfigVariableDeclaration('NAMESPACE', 'legion', str,
                                      'Name of kubernetes namespace inside Pod',
                                      False)

POD_NAME = ConfigVariableDeclaration('POD_NAME', None, str, 'Current pod name', False)

K8S_API_RETRY_NUMBER_MAX_LIMIT = ConfigVariableDeclaration('K8S_API_RETRY_NUMBER_MAX_LIMIT', 5, int,
                                                           'Count of retries for K8S API calls',
                                                           False)
K8S_API_RETRY_DELAY_SEC = ConfigVariableDeclaration('K8S_API_RETRY_DELAY_SEC', 3, int,
                                                    'Time wait before next retry to call K8S API',
                                                    False)

# Sandbox mode
SANDBOX_PYTHON_TOOLCHAIN_IMAGE = ConfigVariableDeclaration('SANDBOX_PYTHON_TOOLCHAIN_IMAGE',
                                                           'legion/python-toolchain:latest',
                                                           str, 'Default image for sandbox mode using python toolchain',
                                                           True)

SANDBOX_CREATE_SELF_REMOVING_CONTAINER = ConfigVariableDeclaration('SANDBOX_CREATE_SELF_REMOVING_CONTAINER', True,
                                                                   bool, 'Remove sandbox container after exit', True)

SANDBOX_DOCKER_MOUNT_PATH = ConfigVariableDeclaration('SANDBOX_DOCKER_MOUNT_PATH', '/var/run/docker.sock', str,
                                                      'Path to docker engine socket on host machine', True)

LOCAL_DEPLOY_HOSTNAME = ConfigVariableDeclaration('LOCAL_DEPLOY_HOSTNAME', 'http://localhost', str,
                                                  'Name of host on which local deployed models will be accessable',
                                                  True)

# Utils
TEMP_DIRECTORY = ConfigVariableDeclaration('TEMP_DIRECTORY', None, str,
                                           'Override system folder for temporary files',
                                           True)

# For using in tests scenarios
MODEL_NAME = ConfigVariableDeclaration('MODEL_NAME', None, str, 'Name of current model', False)

MODEL_VERSION = ConfigVariableDeclaration('MODEL_VERSION', None, str, 'Version of current model', False)

MODEL_K8S_MEMORY = ConfigVariableDeclaration('MODEL_K8S_MEMORY', '256Mi', str, 'Default k8s memory for a model', True)
MODEL_K8S_CPU = ConfigVariableDeclaration('MODEL_K8S_CPU', '256m', str, 'Default k8s cpu for a model', True)
REDUCE_MODEL_REQUESTS_BY = ConfigVariableDeclaration('REDUCE_MODEL_REQUESTS_BY', 33, int,
                                                     'Reduce k8s resource for model by specific percent', True)

# Auth
LEGIONCTL_OAUTH_CLIENT_ID = ConfigVariableDeclaration('LEGIONCTL_OAUTH_CLIENT_ID', 'legion-cli', str,
                                                      'Set OAuth2 Client id',
                                                      True)

LEGIONCTL_OAUTH_SCOPE = ConfigVariableDeclaration('LEGIONCTL_OAUTH_SCOPE',
                                                  'openid profile email offline_access groups', str,
                                                  'Set OAuth2 scope',
                                                  True)

LEGIONCTL_OAUTH_LOOPBACK_HOST = ConfigVariableDeclaration('LEGIONCTL_OAUTH_LOOPBACK_HOST',
                                                          '127.0.0.1', str,
                                                          'Target redirect for OAuth2 interactive authorization',
                                                          True)

LEGIONCTL_OAUTH_LOOPBACK_URL = ConfigVariableDeclaration('LEGIONCTL_OAUTH_LOOPBACK_URL',
                                                          '/oauth/callback', str,
                                                          'Target redirect url for OAuth2 interactive authorization',
                                                          True)

LEGIONCTL_OAUTH_TOKEN_ISSUING_URL = ConfigVariableDeclaration('LEGIONCTL_OAUTH_TOKEN_ISSUING_URL',
                                                              '', str,
                                                              'OAuth2 token issuing URL',
                                                              True)

LEGIONCTL_NONINTERACTIVE = ConfigVariableDeclaration('LEGIONCTL_NONINTERACTIVE', False,
                                                     bool, 'Disable any interaction (e.g. authorization)', True)
