=============
Feedback loop
=============

.. important::

   Described below requires ``feedback`` to be enabled in the HELM's chart configuration during deploy.


Feedback loop allows model's developers to get review how good models work from their users (3rd-party systems or users that ask for prediction).

1. When anybody asks model for prediction, ``Request-ID`` header with random generated value is added to request and response.

2. Generating of new value for ``Request-ID`` header is missing if value is present by requester (in request headers).

3. Request and response of the model are being stored on external storage service (such as AWS S3 or GCS, depending on configuration).

4. Later, when feedback about prediction could be made (e.g. action, that is predicted, appeared), another HTTP request should be sent.

5. All feedbacks are persisted on external storage service (depending on configuration) and can be used by models during next (re-) training phase (automatically, without any manual actions).


Feedback loop protocol
----------------------

As said before, in general, feedback loop consists of two steps:

1. Creation of prediction (with/without ``request-id`` defined in request)

2. Persisting of feedback (with ``request-id`` returned from previous step)

.. note::

    In examples below **BASE_URL**, **ROUTE** and **JWT** env variables are used. These variables should be set before execution of these chunks of code and they
    must point to existed EDGE endpoint, existed route name and use valid JWT token with appropriate role.

.. note::

    For sending of feedback JWT with any role name might be used.


Create a prediction without specific request id provided
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request to EDGE endpoint for prediction, that does not contain ``request-id`` header.

.. code:: bash

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

Response contains generated ``request-id`` header.

.. code:: txt

    RESPONSE

.. todo::

    Add example of response

These requests and responses are being persisted on external storage (e.g. on S3) in two files.

First file contains meta information about request and response (name is like ``/request_response/income/1.1/year=2019/month=07/day=24/2019072414_4.json``) in next format.

.. code:: json

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
            "x-istio-attributes": "CksKGGRlc3RpbmF0aW9uLnNlcnZpY2UuaG9zdBIvEi1za2xlYXJuLWluY29tZS01anJycC5sZWdpb24uc3ZjLmNsdXN0ZXIubG9jYWwKSQoXZGVzdGluYXRpb24uc2VydmljZS51aWQSLhIsaXN0aW86Ly9sZWdpb24vc2VydmljZXMvc2tsZWFybi1pbmNvbWUtNWpycnAKMgoYZGVzdGluYXRpb24uc2VydmljZS5uYW1lEhYSFHNrbGVhcm4taW5jb21lLTVqcnJwCikKHWRlc3RpbmF0aW9uLnNlcnZpY2UubmFtZXNwYWNlEggSBmxlZ2lvbgpPCgpzb3VyY2UudWlkEkESP2t1YmVybmV0ZXM6Ly9pc3Rpby1pbmdyZXNzZ2F0ZXdheS02ODVkOTY0OWZkLXRjcmx2LmlzdGlvLXN5c3RlbQ==",
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

Second file contains response chunks with same ``request-id`` (name is like ``/response_body/income/1.1/year=2019/month=07/day=24/2019072414_1.json``) in next format:

.. code:: json

    {
        "request_id": "85252432-8d26-9b5f-bed3-e9ceeafc688c",
        "model_endpoint": "default",
        "model_version": "1.1",
        "model_name": "income",
        "response_content": "{\n  \"result\": 1\n}\n",
        "time": "2019-07-24 14:03:00 +0000"
    }

Create a prediction with specific request id provided
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request to EDGE endpoint for prediction, that contains ``request-id`` header.

.. code:: bash

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

.. code:: txt

    RESPONSE

.. todo::

    Add example of response


These requests and responses are being persisted on external storage (e.g. on S3) as in a previous case.


Send feedback for prediction using JSON payload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request to EDGE endpoint for saving *feedback* of previous made prediction for model **income** version **1.1** with id **previous-prediction-id**.

.. code:: bash

    curl -X POST -vv "${BASE_URL}/feedback/model/" \
    -H "Authorization: Bearer ${JWT}" \
    -H "x-model-name: income" \
    -H "x-model-version: 1.1" \
    -H "Request-ID: previous-prediction-id" \
    -H 'Content-Type: application/json' \
    -d '{"truthful": 1}'

HTTP response code 200 should be returned if request has been parsed and has been sent to storage.

Also, next JSON structure should be returned:

- Field ``error`` equals to ``false``.

- Field ``registered`` equals to ``true``.

- Field ``message`` equals to data sent on storage.

Non 200 HTTP code indicates about parsing / persisting / another error.

Example response

.. code:: txt

    RESPONSE

.. todo::

    Add example of response


This **feedback** is being persisted on external storage (e.g. on S3) in partitioned file like ``/feedback/income/1.1/year=2019/month=07/day=23/2019072311_2.json`` in next format.

.. code:: json

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

Send feedback for prediction using URL parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request to EDGE endpoint for saving *feedback* of previous made prediction for model **income** version **1.1** with id **previous-prediction-id**.

.. code:: bash

    curl -X POST -vv "${BASE_URL}/feedback/model/?truthful=1" \
    -H "Authorization: Bearer ${JWT}" \
    -H "x-model-name: income" \
    -H "x-model-version: 1.1" \
    -H "Request-ID: previous-prediction-id"

Response

.. code:: txt

    RESPONSE

.. todo::

    Add example of response


This **feedback** is being persisted on external storage (e.g. on S3) in partitioned file like ``/feedback/income/1.1/year=2019/month=07/day=23/2019072311_2.json`` in next format.

.. code:: json

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

