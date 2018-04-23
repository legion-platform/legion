#!/usr/bin/env python
#
#    Copyright 2017 EPAM Systems
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

import sys
import os
import argparse
import logging
import time
from jinja2 import Environment, FileSystemLoader
import legion.utils
import legion.containers.k8s

ROOT_LOGGER = logging.getLogger()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='K8S Template Renderer')
    parser.add_argument('--verbose', "-v", help='verbose log output',
                        action='store_true')

    parser.add_argument('--template', '-t', type=str, help='Template file path', required=True)
    parser.add_argument('--output', '-o', type=str, help='Output file path', required=True)
    parser.add_argument('--command', '-c', type=str, default='',
                        help='Command to reload configuration', required=False)
    parser.add_argument('--once', '-n', action='store_true',
                        help='Render template Once', required=False)
    parser.add_argument('--pause', '-p', help='Pause length, in seconds', type=int,
                        default=5, required=False)

    # --------- END OF SECTIONS -----------
    args = parser.parse_args(sys.argv[1:])

    v = vars(args)

    if args.verbose or legion.utils.string_to_bool(os.getenv('VERBOSE', '')):
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR

    ROOT_LOGGER.setLevel(log_level)

    j2_env = Environment(
        loader=FileSystemLoader([os.getcwd(), os.path.dirname(os.path.abspath(__file__))])
    )

    j2_template = j2_env.get_template(args.template)

    while True:
        values = legion.containers.k8s.find_all_models_deployments()
        with open(args.output, 'w') as output_file:
            logging.debug('Output file path: %s' % output_file.name)
            output_file.write(j2_template.render(values))

        if args.command:
            os.system(args.command)

        if args.once:
            break
        else:
            time.sleep(args.pause)