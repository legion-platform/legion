==============
Model Feedback
==============

**Model Feedback** provides a view of performance over all stages of model lifecycle.

The mechanism is simple:

1. Ask Deploy for prediction (with or without ``Request-Id`` provided)
2. Send Feedback to Legion about the prediction (with ``Request-Id`` returned from previous step)
3. Legion stores the prediction and feedback to a configurable location

.. important::

   This flow requires ``feedback`` to be enabled in ``values.yaml`` during Helm chart install

Protocol
--------

1. If prediction is requested without Request-ID: ``Request-ID`` header with random ID is added to the request. Otherwise, Request-ID is not generated.
2. Request and response are stored on configured external storage (eg. S3, GCS)
3. User sends Model Feedback as an argument to the feedback endpoint. (Feedback can be arbitrary JSON.)
5. All Feedback is persisted on external storage and can be used by models during subsequent Trains.


Worked example (without Request-ID)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make prediction request to EDGE:

.. code-block:: bash

    curl -X POST -vv "${BASE_URL}/model/${ROUTE}/api/model/invoke" \
    -H "Authorization: Bearer ${JWT}" \
    -d 'age=35' \
    -d 'capital-gain=14084' \
    -d 'capital-loss=0' \
    -d 'education=Bachelors' \
    -d 'education-num=13' \
    -d 'fnlwgt=77516' \
    -d 'hours-per-week=40' \
    -d 'marital-status=Married-civ-spouse' \
    -d 'native-country=United-States' \
    -d 'occupation=Exec-managerial' \
    -d 'race=White' \
    -d 'relationship=Not-in-family' \
    -d 'sex=Male' \
    -d 'workclass=Private'

The response contains a generated ``Request-Id`` header.

.. code-block:: txt

    RESPONSE

.. todo::

    Add example of response

Requests and responses are persisted in two buckets on S3. (File name ~= ``/request_response/income/1.1/year=2019/month=07/day=24/2019072414_4.json``)

The first file contains meta-information about request and response:

.. code-block:: json

    {
        "request_id": "85252432-8d26-9b5f-bed3-e9ceeafc688c",
        "request_get_args": {},
        "response_status": "200",
        "request_host": "edge.legion-test.epm.kharlamov.biz",
        "model_endpoint": "default",
        "model_version": "1.1",
        "request_http_method": "POST",
        "request_http_headers": {
            ":scheme": "http",
            "accept": "*/*",
            "knative-serving-namespace": "legion",
            ":authority": "edge.legion-test.epm.kharlamov.biz",
            ":path": "/api/model/invoke",
            ":method": "POST",
            "user-agent": "python-requests/2.22.0",
            "x-b3-traceid": "1bd630537a9a54c9d3997150ca540d01",
            "x-request-id": "85252432-8d26-9b5f-bed3-e9ceeafc688c",
            "x-b3-sampled": "1",
            "x-envoy-external-address": "1.1.1.1",
            "x-forwarded-host": "edge.legion-test.epm.kharlamov.biz",
            "x-original-uri": "/model/sklearn-income/api/model/invoke",
            "content-type": "application/x-www-form-urlencoded",
            "x-forwarded-port": "443",
            "accept-encoding": "gzip, deflate",
            "knative-serving-revision": "sklearn-income-5jrrp",
            "x-envoy-original-path": "/model/sklearn-income/api/model/invoke",
            "x-real-ip": "1.1.1.1",
            "x-envoy-decorator-operation": "sklearn-income-5jrrp.legion.svc.cluster.local:80/model/sklearn-income/api*",
            "x-istio-attributes": "==",
            "x-forwarded-for": "1.1.1.1,1.1.1.1",
            "content-length": "257",
            "x-forwarded-proto": "http",
            "x-scheme": "https",
            "x-b3-spanid": "d3997150ca540d01"
        },
        "request_post_args": {
            "native-country": "United-States",
            "sex": "Male",
            "education": "Bachelors",
            "hours-per-week": "40",
            "workclass": "Private",
            "race": "White",
            "relationship": "Husband",
            "marital-status": "Married-civ-spouse",
            "occupation": "Exec-managerial",
            "age": "35",
            "fnlwgt": "77516",
            "capital-gain": "14084",
            "capital-loss": "0",
            "education-num": "13"
        },
        "request_uri": "/model/sklearn-income/api/model/invoke",
        "response_http_headers": {
            "content-type": "application/json",
            "model-endpoint": "default",
            "model-name": "income",
            "model-version": "1.1",
            "server": "istio-envoy",
            ":status": "200",
            "content-length": "18",
            "x-envoy-upstream-service-time": "67",
            "connection": "close",
            "date": "Wed, 24 Jul 2019 14:53:55 GMT",
            "request-id": "85252432-8d26-9b5f-bed3-e9ceeafc688c"
        },
        "model_name": "income",
        "time": "2019-07-24 14:53:55 +0000"
    }

The second file contains the response body with the same ``Request-Id`` (File name ~= ``/response_body/income/1.1/year=2019/month=07/day=24/2019072414_1.json``)

.. code-block:: json

    {
        "request_id": "85252432-8d26-9b5f-bed3-e9ceeafc688c",
        "model_endpoint": "default",
        "model_version": "1.1",
        "model_name": "income",
        "response_content": "{\n  \"result\": 1\n}\n",
        "time": "2019-07-24 14:03:00 +0000"
    }

Worked example (with Request-ID)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make prediction request to EDGE:

.. code-block:: bash

    curl -X POST -vv "${BASE_URL}/model/${ROUTE}/api/model/invoke" \
    -H "Authorization: Bearer ${JWT}" \
    -H "Request-ID: my-example-request-id" \
    -d 'age=35' \
    -d 'capital-gain=14084' \
    -d 'capital-loss=0' \
    -d 'education=Bachelors' \
    -d 'education-num=13' \
    -d 'fnlwgt=77516' \
    -d 'hours-per-week=40' \
    -d 'marital-status=Married-civ-spouse' \
    -d 'native-country=United-States' \
    -d 'occupation=Exec-managerial' \
    -d 'race=White' \
    -d 'relationship=Not-in-family' \
    -d 'sex=Male' \
    -d 'workclass=Private'

Response contains sent ``request-id`` header.

.. code-block:: txt

    RESPONSE

.. todo::

    Add example of response


Request and response are persisted to S3, as in a previous case.


In both examples, we have obtained a prediction value and Request-ID.
We can use these facts to send back Model Feedback about the prediction (precision, area-under-curve, etc).
Legion will store the Feedback, Request, Response, and Prediction behind one unified interface for later use.

Worked Example - Send Feedback as Payload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send Model Feedback request:

.. code-block:: bash

    curl -X POST -vv "${BASE_URL}/feedback/model/" \
    -H "Authorization: Bearer ${JWT}" \
    -H "x-model-name: income" \
    -H "x-model-version: 1.1" \
    -H "Request-ID: previous-prediction-id" \
    -H 'Content-Type: application/json' \
    -d '{"truthful": 1}'

Note that the ``-d`` argument can pass arbitrary JSON.

A successful feedback request will have the following properties:

- HTTP response: 200
- Response field ``error`` is ``false``.
- Response field ``registered`` is ``true``.
- Response field ``message`` is what was sent to storage.

Example response

.. code-block:: txt

    RESPONSE

.. todo::

    Add example of response

File name ~= ``/feedback/income/1.1/year=2019/month=07/day=23/2019072311_2.json`` will have a format like this,
with feedback stored in the ``payload`` field:

.. code-block:: json

    {
        "request_id": "previous-prediction-id",
        "model_version": "1.1",
        "model_name": "income",
        "payload": {
            "json": {
                "truthful": "1"
            }
        },
        "time": "2019-07-23 12:40:16 +0000"
    }


Worked Example - Send Feedback as URL param
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send Model Feedback request:

.. code-block:: bash

    curl -X POST -vv "${BASE_URL}/feedback/model/?truthful=1" \
    -H "Authorization: Bearer ${JWT}" \
    -H "x-model-name: income" \
    -H "x-model-version: 1.1" \
    -H "Request-ID: previous-prediction-id"

Response

.. code-block:: txt

    RESPONSE

.. todo::

    Add example of response


File name ~= ``/feedback/income/1.1/year=2019/month=07/day=23/2019072311_2.json`` will have a format like this,
with feedback stored in the ``payload`` field:

.. code-block:: json

    {
        "request_id": "previous-prediction-id",
        "model_version": "1.1",
        "model_name": "income",
        "payload": {
            XXXX
        },
        "time": "2019-07-23 12:40:16 +0000"
    }

.. todo::

    Fix example
