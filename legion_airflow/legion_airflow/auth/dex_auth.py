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

import flask_login
from flask_login import (current_user,
                         logout_user,
                         login_required,
                         login_user)
from flask import flash

from flask import url_for, redirect

from airflow import settings, models
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

admin_group = None
if conf.has_option('webserver', 'dex_group_admin'):
    admin_group = conf.get('webserver', 'dex_group_admin')

profiler_group = None
if conf.has_option('webserver', 'dex_group_profiler'):
    profiler_group = conf.get('webserver', 'dex_group_profiler')


class AuthenticationError(Exception):
    """Authentication error is raised on authentication failure."""

    pass


class DexUser(object):
    """Dex user details."""

    def __init__(self, email: str, name: str,
                 is_superuser: bool=False, is_data_profiler: bool=False):
        """Init DexUser instance.
        :param email: User email
        :param name: User full name
        :param is_superuser: If user has Superuser role
        :param is_data_profiler: If user has Data Profiler role
        """
        self._email = email
        self._name = name
        self._is_superuser = is_superuser
        self._is_data_profiler = is_data_profiler

    def name(self):
        """User full name"""
        return self._name

    def email(self):
        """User email"""
        return self._email

    @staticmethod
    def is_active():
        """Indicate if user is active. Required by flask_login."""
        return True

    @staticmethod
    def is_authenticated():
        """Indicate if user is authenticated. Required by flask_login."""
        return True

    @staticmethod
    def is_anonymous():
        """Indicate if user is anonymous. Required by flask_login."""
        return False

    def is_superuser(self):
        """Access all the things."""
        return self._is_superuser

    def data_profiling(self):
        """Provide access to data profiling tools."""
        return self._is_data_profiler

    def get_id(self):
        """Return the current user id as required by flask_login"""
        return self._email


@login_manager.user_loader
def load_user(user_id):
    """Reload a user from the session. The function you set should
    take a user ID (a ``unicode``) and return a
    user object, or ``None`` if the user does not exist.
    :param user_id: User ID
    :return user object, or ``None`` if the user does not exist
    :rtype DexUser
    """
    LOG.debug("Loading user %s", user_id)
    if not user_id or user_id == 'None':
        return None

    session = settings.Session()
    user = session.query(models.User).\
        filter(models.User.email == user_id).first()
    session.expunge_all()
    session.commit()
    session.close()
    if user:
        return DexUser(user.email, user.username, user.superuser, True)


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
            'JWT header is invalid or absent.', mimetype='text/plain',
            status=401)
        return response

    name = jwt_obj.get('name')
    email = jwt_obj.get('email')
    groups = jwt_obj.get('groups')

    is_superuser = False
    is_data_profiler = False

    if admin_group or profiler_group:
        if admin_group in groups:
            is_superuser = True
        elif profiler_group in groups:
            is_data_profiler = True
        else:
            response = Response(
                "Access denied for user '{}'" % email,
                mimetype='text/plain', status=401)
            return response
    else:
        is_superuser = True
        is_data_profiler = True

    session = settings.Session()
    user = session.query(models.User).filter(
        models.User.email == email).first()

    if not user:
        user = models.User(
            username=name,
            email=email,
            superuser=is_superuser)
    else:
        user.superuser = is_superuser

    session.merge(user)
    session.commit()
    flask_login.login_user(DexUser(email, name, is_superuser, is_data_profiler))
    session.commit()
    session.close()
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
