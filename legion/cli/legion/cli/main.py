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
CLI entrypoint
"""

import click
from legion.cli.parsers.config import config_group
from legion.cli.parsers.connection import connection
from legion.cli.parsers.deployment import deployment
from legion.cli.parsers.model import model
from legion.cli.parsers.packaging import packaging
from legion.cli.parsers.packaging_integration import packaging_integration
from legion.cli.parsers.bulk import bulk
from legion.cli.parsers.route import route
from legion.cli.parsers.sandbox import sandbox
from legion.cli.parsers.security import login, logout
from legion.cli.parsers.template import template
from legion.cli.parsers.toolchain_integration import toolchain_integration
from legion.cli.parsers.training import training
from legion.cli.utils.abbr import AbbreviationGroup
from legion.cli.utils.logger import configure_logging


@click.group(cls=AbbreviationGroup)
@click.option('--verbose/--no-verbose', default=False)
def main(verbose=False):
    """
    Legion CLI
    """
    configure_logging(verbose)


main.add_command(config_group)
main.add_command(connection)
main.add_command(deployment)
main.add_command(model)
main.add_command(packaging)
main.add_command(packaging_integration)
main.add_command(bulk)
main.add_command(route)
main.add_command(sandbox)
main.add_command(template)
main.add_command(toolchain_integration)
main.add_command(training)
main.add_command(login)
main.add_command(logout)

if __name__ == '__main__':
    main()
