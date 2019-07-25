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
import argparse
import logging
import sys

from legion.cli import version
from legion.cli.parsers import security, config, local, model, vcs, training, deployment, cloud, route
from legion.sdk import config as legion_config


def configure_logging(args):
    """
    Set appropriate log level

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    if args.verbose or legion_config.DEBUG:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        stream=sys.stderr)


def build_parser():  # pylint: disable=R0915
    """
    Build parser for CLI

    :return: (:py:class:`argparse.ArgumentParser`, py:class:`argparse._SubParsersAction`)  -- CLI parser for LegionCTL
    """
    parser = argparse.ArgumentParser(description='legion Command-Line Interface')
    parser.add_argument('--verbose',
                        help='verbose log output',
                        action='store_true')
    parser.add_argument('--version',
                        help='get package version',
                        action='store_true')
    subparsers = parser.add_subparsers()

    security.generate_parsers(subparsers)
    config.generate_parsers(subparsers)
    local.generate_parsers(subparsers)
    model.generate_parsers(subparsers)
    vcs.generate_parsers(subparsers)
    training.generate_parsers(subparsers)
    deployment.generate_parsers(subparsers)
    route.generate_parsers(subparsers)
    cloud.generate_parsers(subparsers)

    return parser, subparsers


def main():
    """
    CLI entrypoint method
    :return:
    """
    parser, _ = build_parser()
    args = parser.parse_args(sys.argv[1:])

    v = vars(args)

    configure_logging(args)
    root_logger = logging.getLogger()

    root_logger.debug('CLI parameters: %s', args)

    try:
        if args.version:
            print(version.__version__)
        else:
            if 'func' in v:
                args.func(args)
            else:
                parser.print_help()
                sys.exit(1)
    except Exception as exception:
        root_logger.exception(exception)
        sys.exit(2)


if __name__ == '__main__':
    main()
