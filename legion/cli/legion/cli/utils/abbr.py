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
Abbreviation Group for click
"""
import click

ABBREVIATION = {
    "conn": "connection",
    "conf": "config",
    "dep": "deployment",
    "pack": "packaging",
    "pi": "packaging-integration",
    "temp": "template",
    "ti": "toolchain-integration",
    "train": "training"
}


class AbbreviationGroup(click.Group):
    """
    AbbreviationGroup
    """

    def get_command(self, ctx, cmd_name):
        """
        Override get command of click.Group
        :param ctx: click context
        :param cmd_name: group name
        :return: click Command
        """
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        return click.Group.get_command(self, ctx, ABBREVIATION.get(cmd_name))
