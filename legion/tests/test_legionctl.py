import argparse
import logging
import os
import unittest
from unittest import mock
from unittest.mock import patch
from pathlib import Path

import urllib3
import legion.core.config
from legion.edi import security
from legion.cli import build_model, config_set, config_get, config_get_all

from legion_test_utils import patch_config, gather_stdout_stderr


class TestBuildModel(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_model_file_not_exist(self):
        build_model_args = argparse.Namespace(model_file='/file/not/exists')

        with self.assertRaisesRegex(Exception,
                                    f'Cannot find model binary {build_model_args.model_file}'):
            build_model(build_model_args)

    def test_download_model_file_by_wrong_url(self):
        build_model_args = argparse.Namespace(model_file='http://file.not/exists')

        with self.assertRaisesRegex(Exception, urllib3.util.parse_url(build_model_args.model_file).host):
            build_model(build_model_args)


def build_legionctl_config_location(temp_folder):
    return Path(os.path.join(temp_folder.path, 'legion.conf'))


def build_legionctl_config_env(temp_folder):
    return {'_INI_FILE_DEFAULT_CONFIG_PATH': build_legionctl_config_location(temp_folder)}


class TestLogin(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        legion.core.config.reset_context()

    def test_override_default_config_path(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            new_config_path = Path('some/path')

            with patch.dict(os.environ, {'LEGION_CONFIG': str(new_config_path)}):
                self.assertEqual(legion.core.config.get_config_file_path(), new_config_path)

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_config_security_creation(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            build_model_args = argparse.Namespace(token='test-token', edi='http://test.edi/url')

            security.login(build_model_args)

            self.assertTrue(build_legionctl_config_location(tempfs).exists(), 'Config file was not created')

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_config_security_options(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            token = 'test-token'
            edi = 'http://test.edi/url'
            build_model_args = argparse.Namespace(token=token, edi=edi)

            security.login(build_model_args)

            self.assertEqual(legion.core.config.EDI_URL, edi)
            self.assertEqual(legion.core.config.EDI_TOKEN, token)

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            token = 'test-token'
            edi = 'http://test.edi/url'
            build_model_args = argparse.Namespace(token=token, edi=edi)

            security.login(build_model_args)
            legion.core.config.reinitialize_variables()

            self.assertEqual(legion.core.config.EDI_URL, edi)
            self.assertEqual(legion.core.config.EDI_TOKEN, token)

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options_config_not_exist(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):

            legion.core.config.reinitialize_variables()

            self.assertIsNone(legion.core.config.EDI_URL)
            self.assertIsNone(legion.core.config.EDI_TOKEN)

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options_broken_config(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):

            legion.core.config._INI_FILE_DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            legion.core.config._INI_FILE_DEFAULT_CONFIG_PATH.touch(exist_ok=True)

            with legion.core.config._INI_FILE_DEFAULT_CONFIG_PATH.open('w') as f:
                f.write('some garbage')

            legion.core.config.reinitialize_variables()

            self.assertIsNone(legion.core.config.EDI_URL)
            self.assertIsNone(legion.core.config.EDI_TOKEN)

    def test_config_length(self):
        self.assertGreater(len(legion.core.config.ALL_VARIABLES), 0)


class TestSet(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        legion.core.config.reset_context()

        self.key = 'SOME_KEY'
        self.value = 'SOME_VALUE'
        self.args = argparse.Namespace(key=self.key, value=self.value)

    def tearDown(self):
        if legion.core.config.ALL_VARIABLES.get(self.key):
            del legion.core.config.ALL_VARIABLES[self.key]

    def test_config_set_valid_param(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            self.assertIsNone(legion.core.config.ALL_VARIABLES.get(self.key))
            legion.core.config.ConfigVariableDeclaration(self.key)
            config_set(self.args)
            self.assertEqual(legion.core.config.ALL_VARIABLES[self.key].name, self.key)
            self.assertEqual(getattr(legion.core.config, self.key), self.value)

    def test_config_set_not_configurable_manually(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            self.assertIsNone(legion.core.config.ALL_VARIABLES.get(self.key))
            legion.core.config.ConfigVariableDeclaration(self.key, configurable_manually=False)
            with self.assertRaises(Exception):
                config_set(self.args)

    def test_config_set_variable_not_exists(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            self.assertIsNone(legion.core.config.ALL_VARIABLES.get(self.key))
            with self.assertRaises(SystemExit):
                config_set(self.args)


class TestGet(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        legion.core.config.reset_context()
        self.key = None

    def tearDown(self):
        if legion.core.config.ALL_VARIABLES.get(self.key):
            del legion.core.config.ALL_VARIABLES[self.key]

    def test_config_get_valid_param(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            self.key = 'SOME_KEY'
            value = 'SOME_VALUE'
            args = argparse.Namespace(key=self.key, value=value, show_secrets=False)
            legion.core.config.ConfigVariableDeclaration(self.key)
            config_set(args)
            with gather_stdout_stderr() as (stdout, _):
                config_get(args)
            self.assertTrue(value in stdout.getvalue())

    def test_config_get_show_secrets(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            self.key = 'SOME_PASSWORD'
            value = 'HARD_PASSWORD'
            args = argparse.Namespace(key=self.key, value=value, show_secrets=False)
            legion.core.config.ConfigVariableDeclaration(self.key)
            config_set(args)

            with gather_stdout_stderr() as (stdout, _):
                config_get(args)
            self.assertTrue(value not in stdout.getvalue())

            args.show_secrets = True
            with gather_stdout_stderr() as (stdout, _):
                config_get(args)
            self.assertTrue(value in stdout.getvalue())

    def test_config_get_variable_not_exists(self):
        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            args = argparse.Namespace(key='NON_VALID_KEY', value='ANOTHER_VALUE')
            with self.assertRaises(SystemExit):
                config_get(args)


class TestGetAll(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        legion.core.config.reset_context()

    def test_config_get_all_valid_param(self):
        configurable_key = 'CONFIGURABLE_KEY'
        configurable_value = 'SOME_VALUE'
        configurable_args = argparse.Namespace(key=configurable_key, value=configurable_value,
                                               configurable_manually=True)
        legion.core.config.ConfigVariableDeclaration(configurable_key)

        secret_key = 'SOME_SECRET_PASSWORD'
        secret_value = 'HARD_PASSWORD'
        secret_args = argparse.Namespace(key=secret_key, value=secret_value)
        legion.core.config.ConfigVariableDeclaration(secret_key, configurable_manually=True)

        with legion.utils.TemporaryFolder(change_cwd=True) as tempfs, \
                patch_config(build_legionctl_config_env(tempfs)):
            config_set(configurable_args)
            config_set(secret_args)

            args = argparse.Namespace(with_system=True, show_secrets=False)
            with gather_stdout_stderr() as (stdout, _):
                config_get_all(args)
            output = stdout.getvalue()
            self.assertTrue(configurable_key in output)
            self.assertTrue(configurable_value in output)
            self.assertTrue(secret_key in output)
            self.assertTrue(secret_value not in output)
            self.assertTrue('System variables' in output)

            args.with_system = False
            with gather_stdout_stderr() as (stdout, _):
                config_get_all(args)
            output = stdout.getvalue()
            self.assertTrue(configurable_key in output)
            self.assertTrue(configurable_value in output)
            self.assertTrue(secret_key in output)
            self.assertTrue(secret_value not in output)
            self.assertTrue('System variables' not in output)

            args.show_secrets = True
            with gather_stdout_stderr() as (stdout, _):
                config_get_all(args)
            output = stdout.getvalue()
            self.assertTrue(configurable_key in output)
            self.assertTrue(configurable_value in output)
            self.assertTrue(secret_key in output)
            self.assertTrue(secret_value in output)
            self.assertTrue('System variables' not in output)


if __name__ == '__main__':
    unittest.main()
