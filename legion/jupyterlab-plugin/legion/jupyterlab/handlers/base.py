#
#    Copyright 2019 EPAM Systems
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
Declaration of base back-end handler
"""
import json

from notebook.base.handlers import APIHandler


# pylint: disable=W0223
class BaseLegionHandler(APIHandler):
    """
    Base handler for Legion plugin back-end
    """

    def __init__(self, *args, **kwargs):
        """
        Construct base handler w/o state & logger

        :param args: additional args (is passed to parent)
        :param kwargs: additional k-v args (is passed to parent)
        """
        super().__init__(*args, **kwargs)
        self.state = None
        self.logger = None
        self.templates = None

    def initialize(self, state, logger, templates, **kwargs):
        """
        Initialize base handler

        :param state: state of plugin back-end
        :param logger: logger to log data to
        :param kwargs: additional arguments
        :return: None
        """
        self.state = state
        self.logger = logger
        self.templates = templates
        self.logger.debug('%s initialized', self.__class__.__name__)

    def finish_with_json(self, data=None):
        """
        Finish request (response to client) with JSON

        :param data: JSON-serializable object
        :type data: any
        :return: None
        """
        self.finish(json.dumps(data))
