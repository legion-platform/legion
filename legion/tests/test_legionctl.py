import argparse
import logging
import unittest

import urllib3
from build.lib.legion.edi.deploy import build_model


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


if __name__ == '__main__':
    unittest.main()
