#
#    Copyright 2018 EPAM Systems
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
legion k8s definitions functions
"""
import logging
import json

import legion.config
import legion.containers.headers

STATUS_OK = 'ok'
STATUS_FAIL = 'fail'
STATUS_WARN = 'warning'

LOGGER = logging.getLogger(__name__)


class ModelIdVersion:
    """
    Holder for model ID and version
    """

    def __init__(self, model_id, model_version):
        """
        Build model ID and version holder

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        """
        self._id = model_id
        self._version = model_version

    @property
    def id(self):
        """
        Get model ID

        :return: str -- model ID
        """
        return self._id

    @property
    def version(self):
        """
        Get model version

        :return: str -- model version
        """
        return self._version

    def __eq__(self, other):
        """
        Check equation of self object with another by fields

        :param other: another object
        :type other: :py:class:`legion.k8s.definitions.ModelIdVersion`
        :return: bool -- result of equation
        """
        return self.id == other.id and self.version == other.version

    def __repr__(self):
        """
        Get str representation for repr function

        :return: str -- string representation
        """
        return '{}({}, {})'.format(self.__class__.__name__,
                                   self.id, self.version)

    def __hash__(self):
        """
        Build hash of object

        :return: int -- hash of object
        """
        return hash((self.id, self.version))

    __str__ = __repr__


class ModelDeploymentDescription:
    """
    Holder for model deployment description
    """

    MODE_CLUSTER = 'cluster'
    MODE_LOCAL = 'local'

    def __init__(self,
                 status,
                 model, version,
                 image,
                 scale, ready_replicas,
                 deploy_mode,
                 namespace=None,
                 container_id=None,
                 local_port=None,
                 model_api_ok=None, model_api_info=None):
        """
        Construct model deployment description

        :param status: status of model deployment
        :type status: str
        :param model: model ID
        :type model: str
        :param version: model version
        :type version: str
        :param image: model image
        :type image: str
        :param scale: model scale
        :type scale: int
        :param ready_replicas: already ready model replicas
        :type ready_replicas: int
        :param deploy_mode: deploy mode
        :type deploy_mode: str
        :param namespace: (Optional) model namespace (for cluster deploy mode)
        :type namespace: str or None
        :param container_id: (Optional) ID of container (for local deploy mode)
        :type container_id: str
        :param local_port: (Optional) local listen port (for local deploy mode)
        :type local_port: int
        :param model_api_ok: (Optional) model API state from EDGE invocation
        :type model_api_ok: bool or None
        :param model_api_info: (Optional) model API info from EDGE invocation
        :type model_api_info: dict or None
        """
        self._status = status
        self._model = model
        self._version = version
        self._image = image
        self._scale = scale
        self._ready_replicas = ready_replicas
        self._deploy_mode = deploy_mode
        self._namespace = namespace
        self._container_id = container_id
        self._local_port = local_port
        self._model_api_ok = model_api_ok
        self._model_api_info = model_api_info

    @staticmethod
    def build_from_model_service(model_service, model_api_ok=None, model_api_info=None):
        """
        Build from existed model service

        :param model_service: model service
        :type model_service: :py:class:`legion.k8s.services.ModelService`
        :param model_api_ok: (Optional) model API state from EDGE invocation
        :type model_api_ok: bool or None
        :param model_api_info: (Optional) model API info from EDGE invocation
        :type model_api_info: dict or None
        :return: :py:class:`legion.k8s.definitions.ModelDeploymentDescription` -- built model deployment
        """
        return ModelDeploymentDescription(
            status=model_service.status,
            model=model_service.id,
            version=model_service.version,
            image=model_service.image,
            scale=model_service.desired_scale,
            ready_replicas=model_service.scale,
            deploy_mode=ModelDeploymentDescription.MODE_CLUSTER,
            namespace=model_service.namespace,
            model_api_ok=model_api_ok,
            model_api_info=model_api_info,
        )

    @staticmethod
    def build_from_docker_container_info(docker_container_info, model_api_ok=None, model_api_info=None):
        """
        Build from existed model service

        :param docker_container_info: model service
        :type docker_container_info: :py:class:`docker.models.containers.Container`
        :param model_api_ok: (Optional) model API state from EDGE invocation
        :type model_api_ok: bool or None
        :param model_api_info: (Optional) model API info from EDGE invocation
        :type model_api_info: dict or None
        :return: :py:class:`legion.k8s.definitions.ModelDeploymentDescription` -- built model deployment
        """
        is_working = docker_container_info.status == 'running'
        local_port = None
        binded_ports = docker_container_info.attrs['NetworkSettings']['Ports']
        for name, info in binded_ports.items():
            if name.startswith('{}/'.format(legion.config.LEGION_PORT)):
                if not info:
                    LOGGER.debug('Port {} has not been bound for container {}'.format(legion.config.LEGION_PORT,
                                                                                      docker_container_info.id))
                else:
                    local_port = int(info[0]['HostPort'])

                break

        if not local_port:
            LOGGER.debug('Cannot find port {} for container {}'.format(legion.config.LEGION_PORT,
                                                                       docker_container_info.id))

        return ModelDeploymentDescription(
            status=STATUS_OK if is_working else STATUS_FAIL,
            model=docker_container_info.labels[legion.containers.headers.DOMAIN_MODEL_ID],
            version=docker_container_info.labels[legion.containers.headers.DOMAIN_MODEL_VERSION],
            image=docker_container_info.image.id,
            scale=1 if is_working else 0,
            ready_replicas=1 if is_working else 0,
            deploy_mode=ModelDeploymentDescription.MODE_LOCAL,
            container_id=docker_container_info.id,
            local_port=local_port,
            model_api_ok=model_api_ok,
            model_api_info=model_api_info,
        )

    @property
    def id_and_version(self):
        """
        Build key from model id and model version

        :return: :py:class:`legion.k8s.definitions.ModelIdVersion`
        """
        return ModelIdVersion(self.model, self.version)

    @property
    def status(self):
        """
        Get model status

        :return: str -- model status [STATUS_OK, STATUS_FAIL, STATUS_WARN]
        """
        return self._status

    @property
    def model(self):
        """
        Get model ID

        :return: str -- model ID
        """
        return self._model

    @property
    def version(self):
        """
        Get model version

        :return: str -- model version
        """
        return self._version

    @property
    def image(self):
        """
        Get model image

        :return: str -- model image
        """
        return self._image

    @property
    def scale(self):
        """
        Get model scale

        :return: int -- model scale
        """
        return self._scale

    @property
    def ready_replicas(self):
        """
        Get actual ready replicas

        :return: int -- actual ready replicas
        """
        return self._ready_replicas

    @property
    def deploy_mode(self):
        """
        Get model deploy mode (cluster or local)

        :return: str -- deploy mode
        """
        return self._deploy_mode

    @property
    def namespace(self):
        """
        Get namespace in which model has been deployed (for cluster deploy mode)

        :return: str -- model namespace
        """
        return self._namespace

    @property
    def container_id(self):
        """
        Get ID of local container deployment (for local deploy mode)

        :return: str -- Docker container ID
        """
        return self._container_id

    @property
    def local_port(self):
        """
        Get local listened port (for local deploy mode)

        :return: int -- Local port
        """
        return self._local_port

    @property
    def model_api_ok(self):
        """
        Get model API status from model invocation

        :return: str or None -- model API status
        """
        return self._model_api_ok

    @property
    def model_api_info(self):
        """
        Get info about model from model API

        :return: dict -- model info
        """
        return self._model_api_info

    def as_dict(self):
        """
        Get current object as a JSON-serializable dict

        :return: dict[str, Any] -- current object status
        """
        return {
            'status': self._status,
            'model': self._model,
            'version': self._version,
            'image': self._image,
            'scale': self._scale,
            'ready_replicas': self._ready_replicas,
            'deploy_mode': self._deploy_mode,
            'namespace': self._namespace,
            'container_id': self._container_id,
            'local_port': self._local_port,
            'model_api_ok': self._model_api_ok,
            'model_api_info': self._model_api_info
        }

    def __eq__(self, other):
        """
        Compare with other object

        :param other: other object
        :type other: Any
        :return: bool -- is equal
        """
        return isinstance(other, ModelDeploymentDescription) and all([
            getattr(self, field) == getattr(other, field)
            for field in (
                'status', 'model', 'version',
                'image', 'scale', 'ready_replicas',
                'deploy_mode', 'namespace', 'container_id', 'local_port'
            )
        ])

    @staticmethod
    def build_from_json(json_dict):
        """
        Build ModelDeploymentDescription from JSON dict

        :param json_dict: result of deserialization serialized .as_dict response
        :type json_dict: dict[str, Any]
        :return: :py:class:`legion.k8s.definitions.ModelDeploymentDescription` -- built model deployment
        """
        if isinstance(json_dict['model_api_info'], bytes):
            json_dict['model_api_info'] = json.loads(json_dict['model_api_info'])
        return ModelDeploymentDescription(**json_dict)

    def __repr__(self):
        """
        Get string representation of object

        :return: str -- string representation
        """
        args = ",".join(repr(arg) for arg in [
            self.status, self.model, self.version, self.image,
            self.scale, self.ready_replicas, self.deploy_mode,
            self.namespace, self.container_id, self.local_port,
            self.model_api_ok, self.model_api_info
        ])
        return "ModelDeploymentDescription({})".format(args)

    __str__ = __repr__
