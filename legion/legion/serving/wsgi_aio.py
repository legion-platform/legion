#!/usr/bin/env python
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
Entry point for WSGI server with AIO support
Example of usage: gunicorn legion.wsgi_aio:aioapp -k aiohttp.worker.GunicornWebWorker
"""

try:
    import docker_bootup
except ImportError:
    pass

from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from legion.serving.pyserve import init_application


def make_aiohttp_app():
    """
    Create aiohttp application

    :return: :py:class:`aiohttp.web.Application`
    """
    application = init_application()
    wsgi_handler = WSGIHandler(application)
    aioapp_instance = web.Application()
    aioapp_instance.router.add_route('*', '/{path_info:.*}', wsgi_handler)
    return aioapp_instance


aioapp = make_aiohttp_app()
