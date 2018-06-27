from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def root():
    return jsonify(demo=True)


@app.route('/api/model/<model>/info', methods=['GET', 'POST'])
def model_info(model):
    return jsonify(
        version=1.0,
        use_df=False,
        input_params={'b': {'numpy_type': 'int64', 'type': 'Integer'},
                      'a': {'numpy_type': 'int64', 'type': 'Integer'}}
    )


@app.route('/api/model/<model>/invoke', methods=['GET', 'POST'])
def model_invoke(model):
    return jsonify(result=42.0)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
