import logging
import os
import shutil
import sys
import tempfile

import nbformat
import unittest2
from nbconvert.preprocessors import ExecutePreprocessor

import drun.io as drun


class TestSimpleModelEnd2End(unittest2.TestCase):

    def setUp(self):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

        self.sandboxdir = tempfile.mkdtemp('testcase')
        self.rundir = os.path.dirname(os.path.realpath(__file__))

        print("Rundir %s" % self.rundir)

    def run_notebook(self, notebook_filename):
        """Copy to a sandbox"""
        nb_dir, nb_name = os.path.split(notebook_filename)
        sandboxed_nb = os.path.join(self.sandboxdir, nb_name)

        shutil.copy2(notebook_filename, sandboxed_nb)

        with open(notebook_filename) as f:
            nb = nbformat.read(f, as_version=4)

            ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

            ep.extra_arguments = ['--Application.log_level=0']

            print("Executing notebook %s in %s" % (notebook_filename, self.sandboxdir))
            ep.preprocess(nb, {'metadata': {'path': self.sandboxdir}})

    def test_income_classification_it(self):

        """Executing the income_classification_it.ipynb notebook to produce a pickled model bundle"""
        notebook_path = os.path.join(self.rundir, 'income_classification_it.ipynb')
        self.run_notebook(notebook_path)

        self.assertTrue(os.path.exists('/tmp/model.dill'))

        model = drun.load_model('/tmp/model.dill')

    def tearDown(self):
#        os.removedirs(self.sandboxdir)
        return

if __name__ == '__main__':
    unittest2.main()
