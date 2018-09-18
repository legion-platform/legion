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
import typing

LEGION_SYSTEM_LABEL = 'legion.system'
LEGION_SYSTEM_VALUE = 'yes'
LEGION_COMPONENT_LABEL = 'legion.component'
LEGION_COMPONENT_NAME_MODEL = 'model'
LEGION_COMPONENT_NAME_EDI = 'edi'
LEGION_COMPONENT_NAME_API = 'edge'
LEGION_COMPONENT_NAME_GRAFANA = 'grafana'
LEGION_COMPONENT_NAME_GRAPHITE = 'graphite'

LEGION_API_SERVICE_PORT = 'api'

ENCLAVE_NAMESPACE_LABEL = 'enclave'

INGRESS_DASHBOARD_NAME = 'kubernetes-dashboard'
INGRESS_GRAFANA_NAME = 'legion-core-grafana'

STATUS_OK = 'ok'
STATUS_FAIL = 'fail'
STATUS_WARN = 'warning'

EVENT_ADDED = 'ADDED'
EVENT_MODIFIED = 'MODIFIED'
EVENT_DELETED = 'DELETED'

LOAD_DATA_ITERATIONS = 5
LOAD_DATA_TIMEOUT = 2

ModelContainerMetaInformation = typing.NamedTuple('ModelContainerMetaInformation', [
    ('k8s_name', str),
    ('model_id', str),
    ('model_version', str),
    ('kubernetes_labels', typing.Dict[str, str]),
    ('kubernetes_annotations', typing.Dict[str, str]),
])


class ModelIdVersion:
    """
    Holder for model ID and version
    """

    def __init__(self, id, version):
        """
        Build model ID and version holder

        :param id: model ID
        :type id: str
        :param version: model version
        :type version: str
        """
        self._id = id
        self._version = version

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

    def __init__(self,
                 status,
                 model, version,
                 image,
                 scale, ready_replicas,
                 namespace,
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
        :param namespace: model namespace
        :type namespace: str
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
        self._namespace = namespace
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
            namespace=model_service.namespace,
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
    def namespace(self):
        """
        Get model namespace

        :return: str -- model namespace
        """
        return self._namespace

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
            'namespace': self._namespace,
            'model_api_ok': self._model_api_ok,
            'model_api_info': self._model_api_info
        }

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
            self.scale, self.ready_replicas, self.namespace,
            self.model_api_ok, self.model_api_info
        ])
        return "ModelDeploymentDescription({})".format(args)

    __str__ = __repr__
