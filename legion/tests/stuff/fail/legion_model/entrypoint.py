import functools
import typing


def init():
    """
    Initialize model and return prediction type

    :return: str -- prediction type (matrix or objects)
    """
    print('init')

    return 'matrix'


def predict_on_matrix(input_matrix, provided_columns_names=None):
    """
    Make prediction on a Matrix of values

    :param input_matrix: data for prediction
    :type input_matrix: List[List[Any]]
    :param provided_columns_names: (Optional). Name of columns for provided matrix.
    :type provided_columns_names: typing.Optional[typing.List[str]]
    :return: typing.Tuple[List[List[Any]]], typing.Tuple[str, ...] -- result matrix and result column names
    """

    raise Exception(f'Expected error')


@functools.lru_cache()
def info() -> typing.Tuple[typing.Dict[str, dict], typing.Dict[str, dict]]:
    """
    Get input and output schemas

    :return: OpenAPI specifications. Each specification is assigned as (input / output)
    """
    input_sample = {
        "a": {
            'name': "a",
            'type': "string",
            'required': True
        },
        "b": {
            'name': "b",
            'type': "string",
            'required': True
        }
    }
    output_sample = {
        'result': {
            'name': "integer",
            'type': "string",
            'required': True
        },
    }

    return input_sample, output_sample


def get_output_json_serializer() -> typing.Optional[type]:
    """
    Returns JSON serializer to be used in output

    :return: type -- JSON serializer
    """
    return None
