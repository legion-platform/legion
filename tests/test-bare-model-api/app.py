#
#   Copyright 2018 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/')
def root():
    return jsonify(demo=True)


@app.route('/healthcheck')
def healthcheck():
    return jsonify(demo=True)


@app.route('/api/model/<model>/<version>/info', methods=['GET', 'POST'])
def model_info(model, version):
    return jsonify(
        model_version=version,
        model_id=model,
        endpoints={
            'default': {
                'name': 'default',
                'use_df': False,
                'input_params': {'b': {'numpy_type': 'int64', 'type': 'Integer'},
                                 'a': {'numpy_type': 'int64', 'type': 'Integer'}}

            }
        }
    )


@app.route('/api/model/<model>/<version>/invoke', methods=['GET', 'POST'])
@app.route('/api/model/<model>/<version>/invoke/<endpoint>', methods=['GET', 'POST'])
def model_invoke(model, version, endpoint=None):
    arguments = request.form
    result = 42.0

    if 'str' in arguments and 'copies' in arguments:
        result = arguments['str'] * int(arguments['copies'])

    return jsonify(result=result)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
