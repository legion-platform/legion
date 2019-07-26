# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from legion.sdk.models.base_model_ import Model
from legion.sdk.models import util


class TokenRequest(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, expiration_date: str=None, role_name: str=None):  # noqa: E501
        """TokenRequest - a model defined in Swagger

        :param expiration_date: The expiration_date of this TokenRequest.  # noqa: E501
        :type expiration_date: str
        :param role_name: The role_name of this TokenRequest.  # noqa: E501
        :type role_name: str
        """
        self.swagger_types = {
            'expiration_date': str,
            'role_name': str
        }

        self.attribute_map = {
            'expiration_date': 'expiration_date',
            'role_name': 'role_name'
        }

        self._expiration_date = expiration_date
        self._role_name = role_name

    @classmethod
    def from_dict(cls, dikt) -> 'TokenRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The TokenRequest of this TokenRequest.  # noqa: E501
        :rtype: TokenRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def expiration_date(self) -> str:
        """Gets the expiration_date of this TokenRequest.

        Explicitly set expiration date for token  # noqa: E501

        :return: The expiration_date of this TokenRequest.
        :rtype: str
        """
        return self._expiration_date

    @expiration_date.setter
    def expiration_date(self, expiration_date: str):
        """Sets the expiration_date of this TokenRequest.

        Explicitly set expiration date for token  # noqa: E501

        :param expiration_date: The expiration_date of this TokenRequest.
        :type expiration_date: str
        """

        self._expiration_date = expiration_date

    @property
    def role_name(self) -> str:
        """Gets the role_name of this TokenRequest.

        Role name  # noqa: E501

        :return: The role_name of this TokenRequest.
        :rtype: str
        """
        return self._role_name

    @role_name.setter
    def role_name(self, role_name: str):
        """Sets the role_name of this TokenRequest.

        Role name  # noqa: E501

        :param role_name: The role_name of this TokenRequest.
        :type role_name: str
        """

        self._role_name = role_name
