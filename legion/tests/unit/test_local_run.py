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
import os
import stat
import sys
import logging

from docker import errors as docker_errors
import unittest2

# Extend PYTHONPATH in order to import test tools and models
from legion.cli.main import build_parser
from legion.cli.parsers.local import sandbox
from legion.sdk.containers import headers
from legion.sdk import utils as legion_utils
from legion.sdk.containers.docker import build_docker_client, get_docker_container_id_from_cgroup_line
from legion.sdk.utils import ensure_function_succeed

sys.path.extend(os.path.dirname(__file__))

import legion_test_utils


def build_activate_script_path(root):
    """
    Build activate script path

    :param root:
    :return:
    """
    return os.path.abspath(os.path.join(root, 'legion-activate.sh'))


def lookup_for_parser_defaults(parser_name):
    """
    Get default values for parser

    :param parser_name: name of parser, e.g. login
    :type parser_name: str
    :return: :py:class:`argparse.Namespace` -- default values
    """
    _, subparsers = build_parser()

    parser = subparsers.choices.get(parser_name, None)
    if not parser:
        raise Exception('Cannot find parser for command {!r}'.format(parser_name))

    args = parser.parse_args([])
    return args


CONTAINER_INTERPRETER = 'python3'
CONTAINER_IMAGE_ID_LINE = headers.STDERR_PREFIX + headers.IMAGE_ID_LOCAL


class TestLocalRun(unittest2.TestCase):
    _multiprocess_can_split_ = True

    @classmethod
    def setUpClass(cls):
        """
        Enable logs on tests start, setup connection context

        :return: None
        """
        logging.basicConfig(level=logging.DEBUG)

    def test_create_env(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)
            self.assertTrue(os.path.exists(desired_path), 'File {} does not exist'.format(desired_path))

    def test_recreate_env(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)
            self.assertTrue(os.path.exists(desired_path), 'File {} does not exist'.format(desired_path))

            with legion_test_utils.gather_stdout_stderr() as (stdout, _):
                create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
                create_sandbox_args.force_recreate = True
                sandbox(create_sandbox_args)
                self.assertNotIn('already existed', stdout.getvalue())
                self.assertNotIn('ignoring creation of sandbox', stdout.getvalue())

                self.assertIn('Sandbox has been created!', stdout.getvalue())
                self.assertIn('To activate run', stdout.getvalue())

    def test_recreate_env_negative(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)
            self.assertTrue(os.path.exists(desired_path), 'File {} does not exist'.format(desired_path))

            with legion_test_utils.gather_stdout_stderr() as (stdout, _):
                create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
                sandbox(create_sandbox_args)
                self.assertIn('already existed', stdout.getvalue())
                self.assertIn('ignoring creation of sandbox', stdout.getvalue())

                self.assertNotIn('Sandbox has been created!', stdout.getvalue())
                self.assertNotIn('To activate run', stdout.getvalue())

    def test_activate_file_permissions(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)
            self.assertTrue(os.path.exists(desired_path), 'File {} does not exist'.format(desired_path))

            permission = os.stat(desired_path).st_mode
            print('Activate file has access permission: {0:o}'.format(permission))
            self.assertEqual(permission & stat.S_IEXEC, stat.S_IEXEC, 'Activate file has wrong permission')

    def test_activate_file_content(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)
            self.assertTrue(os.path.exists(desired_path), 'File {} does not exist'.format(desired_path))

            with open(desired_path, 'r') as stream:
                content = stream.read()

            self.assertTrue(content.startswith('#!/usr/bin/env bash'), 'Shebang does not found')
            self.assertIn('docker run -ti --rm ', content, 'Docker run with -ti and --rm not found')

    def test_enter_exit_sandbox(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)

            docker_client = build_docker_client()

            with legion_test_utils.ManagedProcessContext([desired_path], shell=True) as context:
                context.wait_stream_output('# $')
                context.mark_streams_finished()

                context.write_to_stdin('cat /proc/self/cgroup')
                context.wait_streams_changed()
                context.wait_stream_output('# $')
                cgroup_lines = context.get_stream_changed_data()[len(context.last_stdin_command):].splitlines()
                cgroup_lines = cgroup_lines[:-1]
                longest_line = max(cgroup_lines, key=len)

                container_id = get_docker_container_id_from_cgroup_line(longest_line)

                # Verify that this is correct container
                docker_client.containers.get(container_id)

            def check_container_removed():
                try:
                    print(container_id)
                    docker_client.containers.get(container_id)
                    return False
                except docker_errors.NotFound:
                    return True

            self.assertTrue(ensure_function_succeed(check_container_removed, 10, 1, boolean_check=True),
                            'Local-run container {!r} has not been removed'.format(container_id))

    def test_build_math_model_python_script(self):
        with legion_utils.TemporaryFolder(change_cwd=True) as tempfs:
            create_sandbox_args = lookup_for_parser_defaults('create-sandbox')
            sandbox(create_sandbox_args)

            desired_path = build_activate_script_path(tempfs.path)

            docker_client = build_docker_client()

            legion_utils.copy_directory_contents(legion_test_utils.get_mocked_model_path('math_model'), tempfs.path)

            with legion_test_utils.ManagedProcessContext([desired_path], shell=True) as context:
                context.wait_stream_output('# $')
                context.mark_streams_finished()

                context.write_to_stdin(CONTAINER_INTERPRETER + ' run.py')
                context.wait_streams_changed()
                context.wait_stream_output('# $')

                self.assertIn('X-Legion-Save-Status:OK', context.get_stream_changed_data())
                context.mark_streams_finished()

                context.write_to_stdin('legionctl build')
                context.wait_streams_changed()
                context.wait_stream_output('# $', retries=120)

                data = context.get_stream_changed_data()
                self.assertIn(CONTAINER_IMAGE_ID_LINE, data, 'Cannot find model id in output')

                line_with_image_id = next(line for line
                                          in data.splitlines()
                                          if line.startswith(CONTAINER_IMAGE_ID_LINE))

                image_id = line_with_image_id.rsplit(':', maxsplit=1)[1]
                docker_client.images.get(image_id)

        with legion_test_utils.ModelLocalContainerExecutionContext(image_id) as context:
            self.assertDictEqual(context.model_information, {
                'endpoints': {
                    'sum': {
                        'input_params': False,
                        'name': 'sum',
                        'use_df': False,
                    },
                    'mul': {
                        'input_params': False,
                        'name': 'mul',
                        'use_df': False,
                    }
                },
                'model_name': 'test-math',
                'model_version': '1.0'
            }, 'invalid model information')

            self.assertEqual(context.client.invoke(a=10, b=20, endpoint='sum')['result'], 30,
                             'invalid invocation result')
            self.assertEqual(context.client.invoke(a=40, b=2, endpoint='mul')['result'], 80,
                             'invalid invocation result')
            self.assertListEqual(
                context.client.batch([{'a': 10, 'b': 10}, {'a': 20, 'b': 30}], endpoint='sum'),
                [
                    {
                        'result': 20,
                    },
                    {
                        'result': 50,
                    }
                ],
                'invalid batch invocation result'
            )
            self.assertListEqual(
                context.client.batch([{'a': 2, 'b': 15}, {'a': 1, 'b': 20}], endpoint='mul'),
                [
                    {
                        'result': 30,
                    },
                    {
                        'result': 20,
                    }
                ],
                'invalid batch invocation result'
            )


if __name__ == '__main__':
    unittest2.main()
