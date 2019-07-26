# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from legion.sdk.models.base_model_ import Model
from legion.sdk.models import util


class ModelDeploymentTarget(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, md_name: str=None, weight: int=None):  # noqa: E501
        """ModelDeploymentTarget - a model defined in Swagger

        :param md_name: The md_name of this ModelDeploymentTarget.  # noqa: E501
        :type md_name: str
        :param weight: The weight of this ModelDeploymentTarget.  # noqa: E501
        :type weight: int
        """
        self.swagger_types = {
            'md_name': str,
            'weight': int
        }

        self.attribute_map = {
            'md_name': 'mdName',
            'weight': 'weight'
        }

        self._md_name = md_name
        self._weight = weight

    @classmethod
    def from_dict(cls, dikt) -> 'ModelDeploymentTarget':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ModelDeploymentTarget of this ModelDeploymentTarget.  # noqa: E501
        :rtype: ModelDeploymentTarget
        """
        return util.deserialize_model(dikt, cls)

    @property
    def md_name(self) -> str:
        """Gets the md_name of this ModelDeploymentTarget.

        Model Deployment name  # noqa: E501

        :return: The md_name of this ModelDeploymentTarget.
        :rtype: str
        """
        return self._md_name

    @md_name.setter
    def md_name(self, md_name: str):
        """Sets the md_name of this ModelDeploymentTarget.

        Model Deployment name  # noqa: E501

        :param md_name: The md_name of this ModelDeploymentTarget.
        :type md_name: str
        """

        self._md_name = md_name

    @property
    def weight(self) -> int:
        """Gets the weight of this ModelDeploymentTarget.

        The proportion of traffic to be forwarded to the Model Deployment.  # noqa: E501

        :return: The weight of this ModelDeploymentTarget.
        :rtype: int
        """
        return self._weight

    @weight.setter
    def weight(self, weight: int):
        """Sets the weight of this ModelDeploymentTarget.

        The proportion of traffic to be forwarded to the Model Deployment.  # noqa: E501

        :param weight: The weight of this ModelDeploymentTarget.
        :type weight: int
        """

        self._weight = weight
