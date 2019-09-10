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
import functools
import json
import os

import legion_model.entrypoint
from flask import Flask, jsonify, Response, request

REQUEST_ID = 'x-request-id'
MODEL_REQUEST_ID = 'request-id'
MODEL_NAME = 'Model-Name'
MODEL_VERSION = 'Model-Version'

app = Flask(__name__)
SUPPORTED_PREDICTION_MODE = legion_model.entrypoint.init()

LEGION_MODEL_NAME = "LEGION_MODEL_NAME"
LEGION_MODEL_VERSION = "LEGION_MODEL_VERSION"


def build_error_response(message):
    return Response(response=json.dumps({'message': message}), status=500, mimetype='application/json')


@functools.lru_cache()
def get_json_output_serializer():
    if hasattr(legion_model.entrypoint, 'get_output_json_serializer'):
        return legion_model.entrypoint.get_output_json_serializer()
    else:
        return None


@app.route('/api/model/info', methods=['GET'])
def info():
    # Consider, if model does not provide info endpoint
    # TODO: Refactor this
    input_schema, output_schema = legion_model.entrypoint.info()
    return jsonify({
        "swagger": "2.0",
        "info": {
            "description": "This is a EDI server.",
            "title": "Model API",
            "termsOfService": "http://swagger.io/terms/",
            "contact": {},
            "license": {
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html"
            },
            "version": "1.0"
        },
        "schemes": [
            "https"
        ],
        "host": "",
        "basePath": "",
        "paths": {
            "/api/model/info": {
                "get": {
                    "description": "Return a swagger info about model",
                    "consumes": [],
                    "produces": [
                        "application/json"
                    ],
                    "summary": "Info",
                    "responses": {
                        "200": {
                            "description": "Info",
                            "type": "object"
                        }
                    }
                }
            },
            "/api/model/invoke": {
                "post": {
                    "description": "Execute prediction",
                    "consumes": [
                        "application/json"
                    ],
                    "produces": [
                        "application/json"
                    ],
                    "summary": "Prediction",
                    "parameters": [
                        {
                            "in": "header",
                            "name": "Authorization",
                            "type": "string",
                            "required": False,
                            "description": "Bearer token",
                            "default": "Bearer ***"
                        },
                        {
                            "in": "body",
                            "name": "PredictionParameters",
                            "required": True,
                            "schema": {
                                "properties": {
                                    "columns": {
                                        "example": [name for name, _ in input_schema.items()],
                                        "items": {
                                            "type": "string"
                                        },
                                        "type": "array"
                                    },
                                    "data": {
                                        "items": {
                                            "items": {
                                                "type": "number"
                                            },
                                            "type": "array"
                                        },
                                        "type": "array",
                                        "example": [[0.0 for _, _ in input_schema.items()]],
                                    }
                                },
                                "type": "object"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Results of prediction",
                            "name": "PredictionResponse",
                            "properties": {
                                "prediction": {
                                    "example": [[0.0 for _, _ in output_schema.items()]],
                                    "items": {
                                        "type": "number"
                                    },
                                    "type": "array",
                                },
                                "columns": {
                                    "example": [name for name, _ in output_schema.items()],
                                    "items": {
                                        "type": "string"
                                    },
                                    "type": "array"
                                }
                            }
                        },
                        "type": "object"
                    }
                }
            }
        }
    })


@app.route('/healthcheck', methods=['GET'])
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


@app.route('/api/model/invoke', methods=['POST'])
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

    resp = Response(response=response_json, status=200, mimetype='application/json')

    resp.headers[MODEL_NAME] = os.getenv(LEGION_MODEL_NAME)
    resp.headers[MODEL_VERSION] = os.getenv(LEGION_MODEL_VERSION)

    request_id = request.headers.get(MODEL_REQUEST_ID) or request.headers.get(REQUEST_ID)
    if request_id:
        resp.headers[MODEL_REQUEST_ID] = request_id

    return resp
