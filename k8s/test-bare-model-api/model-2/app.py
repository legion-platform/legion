from flask import Flask, jsonify

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
    return jsonify(result=42.0)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
