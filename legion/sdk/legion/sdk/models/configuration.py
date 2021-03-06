# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from legion.sdk.models.base_model_ import Model
from legion.sdk.models.common_configuration import CommonConfiguration  # noqa: F401,E501
from legion.sdk.models.training_configuration import TrainingConfiguration  # noqa: F401,E501
from legion.sdk.models import util


class Configuration(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, common: CommonConfiguration=None, training: TrainingConfiguration=None):  # noqa: E501
        """Configuration - a model defined in Swagger

        :param common: The common of this Configuration.  # noqa: E501
        :type common: CommonConfiguration
        :param training: The training of this Configuration.  # noqa: E501
        :type training: TrainingConfiguration
        """
        self.swagger_types = {
            'common': CommonConfiguration,
            'training': TrainingConfiguration
        }

        self.attribute_map = {
            'common': 'common',
            'training': 'training'
        }

        self._common = common
        self._training = training

    @classmethod
    def from_dict(cls, dikt) -> 'Configuration':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Configuration of this Configuration.  # noqa: E501
        :rtype: Configuration
        """
        return util.deserialize_model(dikt, cls)

    @property
    def common(self) -> CommonConfiguration:
        """Gets the common of this Configuration.

        Common secretion of configuration  # noqa: E501

        :return: The common of this Configuration.
        :rtype: CommonConfiguration
        """
        return self._common

    @common.setter
    def common(self, common: CommonConfiguration):
        """Sets the common of this Configuration.

        Common secretion of configuration  # noqa: E501

        :param common: The common of this Configuration.
        :type common: CommonConfiguration
        """

        self._common = common

    @property
    def training(self) -> TrainingConfiguration:
        """Gets the training of this Configuration.

        Configuration describe training process  # noqa: E501

        :return: The training of this Configuration.
        :rtype: TrainingConfiguration
        """
        return self._training

    @training.setter
    def training(self, training: TrainingConfiguration):
        """Sets the training of this Configuration.

        Configuration describe training process  # noqa: E501

        :param training: The training of this Configuration.
        :type training: TrainingConfiguration
        """

        self._training = training
