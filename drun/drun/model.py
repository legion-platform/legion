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

    def transform(self, input_dict):
        """
        Transforms a dictionary of input parameters into a format comprehensible by the model.apply().
        This may include type transformation, enrichment, and access to external sources.
        :param input_dict: the dictionary
        :return: an arbitrary object representing model's input vector.
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

    def __init__(self, apply, types, prepare, version):
        self.column_types = types
        self.prepare_func = prepare
        self.apply_func = apply
        self.version = version

    def transform(self, input_dict):
        df = self.to_df(input_dict)

        if self.prepare_func is not None:
            df = self.prepare_func(input_dict)

        return df

    def apply(self, input_vector):
        return self.apply_func(input_vector)

    def description(self):
        return {'version': self.version}

    def to_df(self, input_dict):
        col_names = input_dict.keys()

        if self.column_types is None:
            dtypes = self.deduce_dtypes()
        else:
            dtypes = self.column_types

        df = pandas.DataFrame(
            data=input_dict,
            columns=col_names,
            dtypes=dtypes
        )

        assert df.count() == 1

        return df

    def deduce_dtypes(self, names, dict):
        # TODO Implement type deduction
        raise NotImplementedError
        dtypes = []

        return dtypes


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


