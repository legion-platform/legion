"""
Models (base, interfaces and proxies)
"""

from drun.types import build_df
from interface import Interface, implements
import logging

LOGGER = logging.getLogger('deploy')


class IMLModel(Interface):
    """
    Definition of an interface for ML model usable for the engine
    """

    @property
    def description(self):
        """
        Get model description
        :return: dictionary with model description
        """
        return None

    def apply(self, input_vector):
        """
        Apply the model to the provided input_vector
        :param input_vector: the input vector
        :return: an arbitrary JSON serializable object
        """
        pass


class ScipyModel(implements(IMLModel)):
    """
    A simple model using Pandas DF for internal representation.
    Useful for Sklearn/Scipy based model export
    """

    def __init__(self, apply_func, prepare_func, column_types, version='Unknown'):
        """
        Build simple SciPy model
        :param apply_func: callable object
        for calculation f(input_dict) -> output
        :param prepare_func: callable object for
        prepare input data f(unprocessed_input_dict) -> input_dict
        :param column_types: dict of column name => type
        :param version: numeric/string version of model
        """
        assert apply_func is not None
        assert prepare_func is not None
        assert column_types is not None

        self.apply_func = apply_func
        self.column_types = column_types
        self.prepare_func = prepare_func
        self.version = version

    def apply(self, input_vector):
        """
        Calculate result of model execution
        :param input_vector: dict of input data
        :return: dict of output data
        """
        data_frame = build_df(self.column_types, input_vector)

        LOGGER.info('Running prepare with DataFrame: %r' % data_frame)
        data_frame = self.prepare_func(data_frame)

        LOGGER.info('Applying function with DataFrame: %r' % data_frame)
        return self.apply_func(data_frame)

    @property
    def description(self):
        """
        Get model description
        :return: dictionary with model description
        """
        return {
            'version': self.version,
            'input_params': {k: v.description_for_api for (k, v) in self.column_types.items()}
        }


class DummyModel(implements(IMLModel)):
    """
    A dummy model for testing. Returns input_dict['result'] as output
    """

    def transform(self, input_dict):
        """
        Pre-process input dictionary
        :param input_dict: dict with input data
        :return: processed dict with data
        """
        return input_dict

    @property
    def description(self):
        """
        Get model description
        :return: dictionary with model description
        """
        return {'version': 'dummy'}

    def apply(self, input_vector):
        """
        Calculate result of model execution
        :param input_vector: dict of input data
        :return: dict of output data
        """
        return {'result': input_vector['result']}
