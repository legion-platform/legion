import argparse
import configparser
import logging
import os
import unittest
from unittest import mock
from unittest.mock import patch
from pathlib import Path

import urllib3
from legion.edi import security
from legion.edi.deploy import build_model


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


TEST_DEFAULT_CONFIG_PATH = Path.cwd().joinpath('.legion/config')


@patch.object(security, '_DEFAULT_CONFIG_PATH', TEST_DEFAULT_CONFIG_PATH)
class TestLogin(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

        self._remove_config()

    def tearDown(self):
        self._remove_config()

    def _get_config(self):
        config = configparser.ConfigParser()
        config.read(TEST_DEFAULT_CONFIG_PATH)

        return dict(config['security'])

    def _remove_config(self):
        if TEST_DEFAULT_CONFIG_PATH.parent.exists():
            if TEST_DEFAULT_CONFIG_PATH.exists():
                TEST_DEFAULT_CONFIG_PATH.unlink()

            TEST_DEFAULT_CONFIG_PATH.parent.rmdir()

    def test_default_config_path(self):
        self.assertEqual(security._get_config_location(), TEST_DEFAULT_CONFIG_PATH)

    def test_override_default_config_path(self):
        new_config_path = Path('some/path')

        with patch.dict(os.environ, {'LEGION_CONFIG': str(new_config_path)}):
            self.assertEqual(security._get_config_location(), new_config_path)

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_config_creation(self):
        build_model_args = argparse.Namespace(token='test-token', edi='http://test.edi/url')

        security.login(build_model_args)

        self.assertTrue(TEST_DEFAULT_CONFIG_PATH.exists(), 'Config file was not created')

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_config_options(self):
        token = 'test-token'
        edi = 'http://test.edi/url'
        build_model_args = argparse.Namespace(token=token, edi=edi)

        security.login(build_model_args)

        self.assertDictEqual(self._get_config(), {'host': edi, 'token': token},
                             'Options does not equal')

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options(self):
        token = 'test-token'
        edi = 'http://test.edi/url'
        build_model_args = argparse.Namespace(token=token, edi=edi)

        security.login(build_model_args)
        security_options = security.get_security_params_from_config()

        self.assertDictEqual(security_options, {'host': edi, 'token': token},
                             'Options does not equal')

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options_config_not_exist(self):
        security_options = security.get_security_params_from_config()

        self.assertDictEqual(security_options, {}, 'Options does not equal')

    @patch.object(security, '_check_credentials', mock.MagicMock())
    def test_get_security_options_broken_config(self):
        TEST_DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        TEST_DEFAULT_CONFIG_PATH.touch(exist_ok=True)

        with TEST_DEFAULT_CONFIG_PATH.open('w') as f:
            f.write('some garbage')

        security_options = security.get_security_params_from_config()

        self.assertDictEqual(security_options, {}, 'Options does not equal')


if __name__ == '__main__':
    unittest.main()
