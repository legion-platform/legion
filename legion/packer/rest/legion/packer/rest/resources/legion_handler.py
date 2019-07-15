#
#    Copyright 2019 EPAM Systems
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
import json
import functools

from flask import Flask, jsonify, Response, request

import legion_model.entrypoint

app = Flask(__name__)
SUPPORTED_PREDICTION_MODE = legion_model.entrypoint.init()


def build_error_response(message):
    return Response(response=json.dumps({'message': message}), status=500, mimetype='application/json')


@functools.lru_cache()
def get_json_output_serializer():
    if hasattr(legion_model.entrypoint, 'get_output_json_serializer'):
        return legion_model.entrypoint.get_output_json_serializer()
    else:
        return None


@app.route('/', methods=['GET'])
def info():
    # Consider, if model does not provide info endpoint
    return jsonify(legion_model.entrypoint.info())


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': True})


def handle_prediction_on_matrix(parsed_data):
    matrix = parsed_data.get('data')
    columns = parsed_data.get('columns', None)

    if not matrix:
        return build_error_response('Matrix is not provided')

    try:
        prediction, columns = legion_model.entrypoint.predict_on_matrix(matrix, provided_columns_names=columns)
    except Exception as predict_exception:
        return build_error_response(f'Exception during prediction: {predict_exception}')

    response = {
        'prediction': prediction,
        'columns': columns
    }

    response_json = json.dumps(response, cls=get_json_output_serializer())
    return response_json


def handle_prediction_on_objects(parsed_data):
    return build_error_response('Can not handle this types of requests')


@app.route('/predict', methods=['POST'])
def predict():
    if not request.data:
        return build_error_response('Please provide data with this POST request')

    try:
        data = request.data.decode('utf-8')
    except UnicodeDecodeError as decode_error:
        return build_error_response(f'Can not decode POST data using utf-8 charset: {decode_error}')

    try:
        parsed_data = json.loads(data)
    except ValueError as value_error:
        return build_error_response(f'Can not parse input as JSON: {value_error}')

    if SUPPORTED_PREDICTION_MODE == 'matrix':
        response_json = handle_prediction_on_matrix(parsed_data)
    elif SUPPORTED_PREDICTION_MODE == 'objects':
        response_json = handle_prediction_on_objects(parsed_data)
    else:
        return build_error_response(f'Unknown model\'s return type: {SUPPORTED_PREDICTION_MODE}')

    if isinstance(response_json, Response):
        return response_json

    return Response(response=response_json, status=200, mimetype='application/json')
