# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from legion.sdk.models.base_model_ import Model
from legion.sdk.models import util


class HTTPResult(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, message: str=None):  # noqa: E501
        """HTTPResult - a model defined in Swagger

        :param message: The message of this HTTPResult.  # noqa: E501
        :type message: str
        """
        self.swagger_types = {
            'message': str
        }

        self.attribute_map = {
            'message': 'message'
        }

        self._message = message

    @classmethod
    def from_dict(cls, dikt) -> 'HTTPResult':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HTTPResult of this HTTPResult.  # noqa: E501
        :rtype: HTTPResult
        """
        return util.deserialize_model(dikt, cls)

    @property
    def message(self) -> str:
        """Gets the message of this HTTPResult.

        Success of error message  # noqa: E501

        :return: The message of this HTTPResult.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message: str):
        """Sets the message of this HTTPResult.

        Success of error message  # noqa: E501

        :param message: The message of this HTTPResult.
        :type message: str
        """

        self._message = message
