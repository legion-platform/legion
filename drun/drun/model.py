"""
Models (base, interfaces and proxies)
"""

from interface import Interface, implements
import pandas


class IMLModel(Interface):
    """
    Definition of an interface for ML model usable for the engine
    """

    def description(self):
        """
        Get model description
        :return: dictionary with model description
        """
        pass

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
        data_frame = self.to_df(input_vector)

        data_frame = self.prepare_func(data_frame)

        return self.apply_func(data_frame)

    def description(self):
        """
        Get model description
        :return: dictionary with model description
        """
        return {'version': self.version,
                'input_params': dict(map(lambda t: (t[0], str(t[1])), self.column_types.items()))}

    def to_df(self, input_dict):
        """
        Convert dict to pandas DataFrame
        :param input_dict: dict of input data
        :return: pandas.DataFrame with input data
        """
        vectorized = {k: [v] for k, v in input_dict.items()}

        data_frame = pandas.DataFrame(vectorized, columns=input_dict.keys())

        # TODO Proper error reporting in response
        assert data_frame.shape[0] == 1

        df_cols = data_frame.columns.values.tolist()

        types = {k: v for k, v in self.column_types.items() if k in df_cols}

        return data_frame.astype(types)


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
