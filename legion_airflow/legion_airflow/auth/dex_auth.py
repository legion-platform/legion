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
"""Authentication backend for Dex used in Apache Airflow."""

from __future__ import unicode_literals

from sys import version_info

import flask_login  # pylint: disable=E0401
from flask_login import current_user, logout_user, login_required, login_user  # pylint: disable=W0611,E0401

from flask import flash

from flask import url_for, redirect

from airflow.utils.log.logging_mixin import LoggingMixin
from airflow import configuration as conf

from werkzeug.http import wsgi_to_bytes
from werkzeug.wrappers import Response

import jwt

login_manager = flask_login.LoginManager()
login_manager.login_view = 'airflow.login'  # Calls login() below
login_manager.login_message = None

LOG = LoggingMixin().log
PY3 = version_info[0] == 3


class DexUser(object):
    """Dex user details."""

    def __init__(self, username: str, email: str, is_superuser: bool = False,
                 is_data_profiler: bool = False):
        """Init DexUser instance.
        :param user: User model
        """
        self._username = username
        self._email = email
        self._is_superuser = is_superuser
        self._is_data_profiler = is_data_profiler

    def name(self):
        """User full name"""
        return self._username

    def email(self):
        """User email"""
        return self._email

    def get_id(self):
        """Return the current user id as required by flask_login"""
        return self._email

    @staticmethod
    def is_active():
        """Check if user is active. Required by flask_login."""
        return True

    @staticmethod
    def is_authenticated():
        """Check if user is authenticated. Required by flask_login"""
        return True

    @staticmethod
    def is_anonymous():
        """Check if user is anonymous. Required by flask_login"""
        return False

    def data_profiling(self):
        """Check if user has access to data profiling tools"""
        return self._is_data_profiler

    def is_superuser(self):
        """Check if user has access to all the things"""
        return self._is_superuser


@login_manager.header_loader
def load_user_from_header(auth_header):
    """Reload a user data from the header.
    :param auth_header: Authorization header
    :return user object, or ``None`` if header is invalid
    :rtype DexUser
    """
    jwt_obj = parse_jwt_header(auth_header)

    if not jwt_obj:
        return None

    name = jwt_obj.get('name', '')
    email = jwt_obj.get('email', '')
    groups = jwt_obj.get('groups', [])

    admin_groups = []
    if conf.has_option('webserver', 'dex_group_admin') and \
            conf.get('webserver', 'dex_group_admin'):
        admin_groups = conf.get('webserver', 'dex_group_admin').split(' ')

    profiler_groups = []
    if conf.has_option('webserver', 'dex_group_profiler') and \
            conf.get('webserver', 'dex_group_profiler'):
        profiler_groups = conf.get('webserver', 'dex_group_profiler').split(' ')

    admin_email = None
    if conf.has_option('webserver', 'dex_admin_email'):
        admin_email = conf.get('webserver', 'dex_admin_email')

    is_superuser = False
    is_data_profiler = False

    if admin_groups or profiler_groups:
        if admin_email and admin_email == email:  # if the user is a Admin
            is_superuser = True
            is_data_profiler = True
        else:
            for group in groups:
                if group in admin_groups:
                    is_superuser = True
                if group in profiler_groups:
                    is_data_profiler = True
    else:
        is_superuser = True
        is_data_profiler = True

    return DexUser(name, email, is_superuser, is_data_profiler)


def login(self, request):
    """Login a user. A function is executed on a new user session.
    Analyze request, parse JWT and create a new user object.
    :param self: required parameter for flask_login
    :param request: a request object
    :type request: Request
    """
    if current_user.is_authenticated():
        flash("You are already logged in")
        return redirect(url_for('admin.index'))

    auth_header = request.headers.get('Authorization')
    jwt_obj = parse_jwt_header(auth_header)

    if not jwt_obj:
        response = Response(
            'JWT header is invalid or absent.', mimetype='text/plain')
        return response

    name = jwt_obj.get('name', '')
    email = jwt_obj.get('email', '')
    groups = jwt_obj.get('groups', [])

    admin_group = None
    if conf.has_option('webserver', 'dex_group_admin'):
        admin_group = conf.get('webserver', 'dex_group_admin')

    profiler_group = None
    if conf.has_option('webserver', 'dex_group_profiler'):
        profiler_group = conf.get('webserver', 'dex_group_profiler')

    admin_email = None
    if conf.has_option('webserver', 'dex_admin_email'):
        admin_email = conf.get('webserver', 'dex_admin_email')

    is_superuser = False
    is_data_profiler = False

    if admin_group or profiler_group:
        if admin_email and admin_email == email:  # if the user is a Admin
            is_superuser = True
            is_data_profiler = True
        elif admin_group and admin_group in groups:
            is_superuser = True
        elif profiler_group and profiler_group in groups:
            is_data_profiler = True
        else:
            response = Response(
                "Access denied for user '{}'".format(email),
                mimetype='text/plain')
            return response
    else:
        is_superuser = True
        is_data_profiler = True

    flask_login.login_user(DexUser(name, email, is_superuser, is_data_profiler))
    return redirect(request.args.get("next") or url_for("admin.index"))


def parse_jwt_header(value):
    """Parse an HTTP bearer authorization header transmitted by the web
    browser.  Try to parse this JWT token, return parsed object
    or None if header is invalid.

    :param value: the authorization header to parse.
    :return: parsed JWT token as a dict object or `None`.
    """
    if not value:
        return None
    value = wsgi_to_bytes(value)
    try:
        auth_type, auth_info = value.split(None, 1)
        auth_type = auth_type.lower()
    except ValueError:
        return
    if auth_type == b'bearer':
        return jwt.decode(auth_info, algorithms=['RS256'], verify=False)
