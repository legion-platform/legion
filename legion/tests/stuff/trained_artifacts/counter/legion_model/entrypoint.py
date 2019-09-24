import functools
from typing import Tuple, List, Dict, Any, Optional, Type

COUNTER = 0


def init() -> str:
    """
    Initialize model and return prediction type

    :return: prediction type (matrix or objects)
    """
    print('init')

    return 'matrix'


def predict_on_matrix(input_matrix: List[List[Any]], provided_columns_names: Optional[List[str]] = None) \
        -> Tuple[List[List[Any]], Tuple[str, ...]]:
    """
    Make prediction on a Matrix of values

    :param input_matrix: data for prediction
    :param provided_columns_names: (Optional). Name of columns for provided matrix.
    :return: result matrix and result column names
    """
    global COUNTER
    COUNTER += 1

    return [[COUNTER]], ('result',)


@functools.lru_cache()
def info() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Get input and output schemas

    :return: OpenAPI specifications. Each specification is assigned as (input / output)
    """
    input_sample = [
        {
            'name': "a",
            'type': "string",
            'required': True,
            'example': "1"
        },
        {
            'name': "b",
            'type': "string",
            'example': "2"
        }
    ]
    output_sample = [
        {
            'name': "integer",
            'type': "string",
            'required': True,
            'example': '42'
        }
    ]

    return input_sample, output_sample


def get_output_json_serializer() -> Optional[Type]:
    """
    Returns JSON serializer to be used in output

    :return: JSON serializer
    """
    return None
