from interface import Interface, implements
import pandas


class IMLModel(Interface):
    """
        Definition of an interface for ML model usable for the engine
    """

    def description(self):
        """
        :return: dictionary with model description
        """
        pass

    def apply(self, input_vector):
        """
        applies the model to the provided input_vector
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
        assert apply_func is not None
        assert prepare_func is not None
        assert column_types is not None

        self.apply_func = apply_func
        self.column_types = column_types
        self.prepare_func = prepare_func
        self.version = version

    def apply(self, input_vector):
        df = self.to_df(input_vector)

        df = self.prepare_func(df)

        return self.apply_func(df)

    def description(self):
        return {'version': self.version,
                'input_params': dict(map(lambda t: (t[0], str(t[1])), self.column_types.items()))}

    def to_df(self, input_dict):
        vectorized = {k: [v] for k, v in input_dict.items()}

        df = pandas.DataFrame(vectorized, columns=input_dict.keys())

        # TODO Proper error reporting in response
        assert df.shape[0] == 1

        df_cols = df.columns.values.tolist()

        types = {k: v for k, v in self.column_types.items() if k in df_cols}

        return df.astype(types)


class DummyModel(implements(IMLModel)):
    """
    A dummy model for testing. Returns input_dict['result'] as output
    """

    def transform(self, input_dict):
        return input_dict

    def description(self):
        return {'version': 'dummy'}

    def apply(self, input_vector):
        return {'result': input_vector['result']}


