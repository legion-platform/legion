# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from legion.sdk.models.base_model_ import Model
from legion.sdk.models.model_deployment_target import ModelDeploymentTarget  # noqa: F401,E501
from legion.sdk.models import util


class ModelRouteSpec(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, mirror: str=None, model_deployments: List[ModelDeploymentTarget]=None, url_prefix: str=None):  # noqa: E501
        """ModelRouteSpec - a model defined in Swagger

        :param mirror: The mirror of this ModelRouteSpec.  # noqa: E501
        :type mirror: str
        :param model_deployments: The model_deployments of this ModelRouteSpec.  # noqa: E501
        :type model_deployments: List[ModelDeploymentTarget]
        :param url_prefix: The url_prefix of this ModelRouteSpec.  # noqa: E501
        :type url_prefix: str
        """
        self.swagger_types = {
            'mirror': str,
            'model_deployments': List[ModelDeploymentTarget],
            'url_prefix': str
        }

        self.attribute_map = {
            'mirror': 'mirror',
            'model_deployments': 'modelDeployments',
            'url_prefix': 'urlPrefix'
        }

        self._mirror = mirror
        self._model_deployments = model_deployments
        self._url_prefix = url_prefix

    @classmethod
    def from_dict(cls, dikt) -> 'ModelRouteSpec':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ModelRouteSpec of this ModelRouteSpec.  # noqa: E501
        :rtype: ModelRouteSpec
        """
        return util.deserialize_model(dikt, cls)

    @property
    def mirror(self) -> str:
        """Gets the mirror of this ModelRouteSpec.

        Mirror HTTP traffic to a another Model deployment in addition to forwarding the requests to the model deployments.  # noqa: E501

        :return: The mirror of this ModelRouteSpec.
        :rtype: str
        """
        return self._mirror

    @mirror.setter
    def mirror(self, mirror: str):
        """Sets the mirror of this ModelRouteSpec.

        Mirror HTTP traffic to a another Model deployment in addition to forwarding the requests to the model deployments.  # noqa: E501

        :param mirror: The mirror of this ModelRouteSpec.
        :type mirror: str
        """

        self._mirror = mirror

    @property
    def model_deployments(self) -> List[ModelDeploymentTarget]:
        """Gets the model_deployments of this ModelRouteSpec.

        A http rule can forward traffic to Model Deployments.  # noqa: E501

        :return: The model_deployments of this ModelRouteSpec.
        :rtype: List[ModelDeploymentTarget]
        """
        return self._model_deployments

    @model_deployments.setter
    def model_deployments(self, model_deployments: List[ModelDeploymentTarget]):
        """Sets the model_deployments of this ModelRouteSpec.

        A http rule can forward traffic to Model Deployments.  # noqa: E501

        :param model_deployments: The model_deployments of this ModelRouteSpec.
        :type model_deployments: List[ModelDeploymentTarget]
        """

        self._model_deployments = model_deployments

    @property
    def url_prefix(self) -> str:
        """Gets the url_prefix of this ModelRouteSpec.

        URL prefix for model  For example: /custom/test Prefix must start with slash \"/feedback\" and \"/model\" are reserved for internal usage  # noqa: E501

        :return: The url_prefix of this ModelRouteSpec.
        :rtype: str
        """
        return self._url_prefix

    @url_prefix.setter
    def url_prefix(self, url_prefix: str):
        """Sets the url_prefix of this ModelRouteSpec.

        URL prefix for model  For example: /custom/test Prefix must start with slash \"/feedback\" and \"/model\" are reserved for internal usage  # noqa: E501

        :param url_prefix: The url_prefix of this ModelRouteSpec.
        :type url_prefix: str
        """

        self._url_prefix = url_prefix
