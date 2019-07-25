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
Robot test library - EDI
"""
import argparse
import itertools

from legion.sdk.clients import training


class EDI:
    """
    EDI client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self, edi_url, edi_token):
        """
        Init client
        """
        self._training_client = training.build_client(argparse.Namespace(edi=edi_url, token=edi_token))

    def prepare_stub_args(self, args):
        """
        Transform dict parameters to flat string
        :param args: args
        :return: argument string
        """
        if not args:
            return ""

        return " ".join(str(x) for x in itertools.chain(*args.items()))

    def get_model_training(self, mt_name):
        """
        Get Model Training
        :param mt_name: Model Training Name
        :return: Model Training
        """
        return self._training_client.get(mt_name)

    def delete_model_training(self, mt_name):
        """
        Delete Model training
        :param mt_name: Model Training Name
        """
        self._training_client.delete(mt_name)
