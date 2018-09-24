#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
"""
Model functionality
"""
from .client import ModelClient, load_image
from .types import int8, uint8, int16, uint16, int32, uint32, int64, uint64
from .types import float32, float64
from .types import string, boolean, image

import legion.pymodel.model
import legion.k8s.properties
from legion.utils import normalize_name

MODEL_TYPES = [
    legion.pymodel.model.Model
]


# Global variable for storing model context
# This variable initializes by init() function
_model = None

# Global variable for storing properties for current model
# This variable initializes by set_properties() function that calls on model init or before model deploy
properties = None  # type: legion.k8s.properties.K8SPropertyStorage


def get_context():
    """
    Get current model context

    :return: object -- model context
    """
    return _model


def reset_context():
    """
    Drop current model context

    :return: None
    """
    global _model
    _model = None


def set_properties(new_properties):
    """
    Set new properties as a instance of legion.k8s.properties.K8SPropertyStorage class

    :param new_properties: new properties
    :type new_properties: :py:class:`legion.k8s.properties.K8SPropertyStorage`
    :return: None
    """
    global properties
    properties = new_properties


def reset_properties():
    """
    Reset properties

    :return: None
    """
    global properties
    properties = None


def init(model_id, model_version, model_type=legion.pymodel.model.Model.NAME):
    """
    Initialize new model context

    :param model_id: model name
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :param model_type: type of model, one of MODEL_TYPES names
    :type model_type: str
    :return: object -- instance of Model class
    """
    global _model

    if _model:
        raise Exception('Context already has been defined')

    model_id = normalize_name(model_id)
    if not model_id:
        raise Exception('Model name string length should be greater that 1 (after normalization)')

    builder = [m_type for m_type in MODEL_TYPES if m_type.NAME == model_type]

    if not builder:
        raise Exception('Cannot find model builder for type {}'.format(model_type))

    if len(builder) > 1:
        raise Exception('More then 1 builder have been found for type {}'.format(model_type))

    _model = builder[0](model_id, model_version)
    set_properties(_model.properties)

    return _model


def send_metric(metric, value):
    """
    Send build metric value

    :param metric: metric type or metric name
    :type metric: :py:class:`legion.metrics.Metric` or str
    :param value: metric value
    :type value: float or int
    :return: None
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.send_metric(metric, value)


def export_df(apply_func, input_data_frame, *, prepare_func=None, endpoint='default'):
    """
    Export simple Pandas DF based model as a bundle

    :param apply_func: an apply function DF->DF
    :type apply_func: func(x) -> y
    :param input_data_frame: pandas DF
    :type input_data_frame: :py:class:`pandas.DataFrame`
    :param prepare_func: a function to prepare input DF->DF
    :type prepare_func: func(x) -> y
    :param endpoint: (Optional) endpoint name, default is 'default'
    :type endpoint: str
    :return: model container
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.export_df(apply_func, input_data_frame, prepare_func=prepare_func, endpoint=endpoint)


def export(apply_func, column_types, *, prepare_func=None, endpoint='default'):
    """
    Export simple parameters defined model as a bundle

    :param apply_func: an apply function DF->DF
    :type apply_func: func(x) -> y
    :param column_types: result of deduce_param_types or prepared column information
    :type column_types: dict[str, :py:class:`legion.model.types.ColumnInformation`]
    :param prepare_func: a function to prepare input DF->DF
    :type prepare_func: func(x) -> y
    :param endpoint: (Optional) endpoint name, default is 'default'
    :type endpoint: str
    :return: model container
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.export(apply_func, column_types, prepare_func=prepare_func, endpoint=endpoint)


def export_untyped(apply_func, *, prepare_func=None, endpoint='default'):
    """
    Export simple untyped model as a bundle

    :param apply_func: an apply function DF->DF
    :type apply_func: func(x) -> y
    :param prepare_func: a function to prepare input DF->DF
    :type prepare_func: func(x) -> y
    :param endpoint: (Optional) endpoint name, default is 'default'
    :type endpoint: str
    :return: model container
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.export_untyped(apply_func, prepare_func=prepare_func, endpoint=endpoint)


def save(path=None):
    """
    Save model to path (or deduce path)

    :param path: (Optional) target save name
    :return: model container
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.save(path)


def define_property(name, initial_value):
    """
    Define model property

    :param name: property name
    :type name: str
    :param initial_value: initial property value
    :type initial_value: any
    :return: model container
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.define_property(name, initial_value)


def on_property_change(callback):
    """
    Set callback that will be called on each property update

    :param callback: callback on each model property update
    :type callback: :py:class:`Callable[[], None]`
    :return: None
    """
    if not _model:
        raise Exception('Context has not been defined')

    return _model.on_property_change(callback)
