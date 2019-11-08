# Model API

Each model provides endpoints for obtaining information,
simple and batch call of models.

**Information in this section is outdated, please update**

**Model information**
----
  Fetching common information about model (id, version) and endpoints (their names, parameters).

* **URL**

  `/api/model/:model_id/:model_version/info`

* **Method:**

  `GET`

*  **URL Params**

   **Required:**

   `model_id=[str]`- ID of model

   `model_version=[str]`- version of model

* **Success Response:**

  Result consists of valid JSON object with common model information (id and version)
  and information about each endpoint.

  * **Strict model example (one endpoint)** <br />
    **Code:** 200 <br />
    **Content**
    ```json
    {
        "endpoints": {
            "default": {
                "input_params": {
                    "age": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    },
                    "capital-gain": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    },
                    "capital-loss": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    }
                },
                "name": "default",
                "use_df": true
            }
        },
        "id": "income",
        "version": "1.1"
    }
    ```

  * **Model example (strict abc endpoint, non strict def endpoint)** <br />
    **Code:** 200 <br />
    **Content**
    ```json
    {
        "endpoints": {
            "abc": {
                "input_params": {
                    "age": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    },
                    "capital-gain": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    },
                    "capital-loss": {
                        "numpy_type": "int64",
                        "type": "Integer"
                    }
                },
                "name": "abc",
                "use_df": true
            },
            "def": {
                "name": "def",
                "use_df": true
            }
        },
        "id": "income",
        "version": "1.1"
    }
    ```

* **Error Response:**

  500 will be returned on any server-side error

* **Sample Call:**

```bash
curl -X GET \
  https://edge-company-a.legion-test.epm.kharlamov.biz/api/model/test-summation/1.0/info
```

* **Notes:**

  02.07.2018, Kirill Makhonin


**Model invocation**
----
  Running prediction and getting result.

* **URL**

  `/api/model/:model_id/:model_version/invoke`

  `/api/model/:model_id/:model_version/invoke/:endpoint`

* **Method:**

  `GET` | `POST`

*  **URL Params**

   **Required:**

   `model_id=[str]`- ID of model

   `model_version=[str]`- version of model

   **Optional:**

   `endpoint=[str]` - name of endpoint, `default` if omitted

   `key=[str]` - argument for model invocation. Can be passed in URL params or in data params. List of required params can be gathered from model info (for strict models) or from model specification (for non strict models)

* **Data Params**

  `key=[str]` - argument for model invocation. Can be passed in URL params in case of using `GET` method or in data
  params in case of using `POST` method. List of required params can be gathered from model info (for strict models) or
  from model specification (for non strict models)

* **Success Response:**

  Successful invocation of model should return 200 code and valid JSON response (structure of response defined in a model code).

  * **Strict model example** <br />
    **Code:** 200 <br />
    **Content**
    ```json
    {
        "result": 3
    }
    ```

* **Error Response:**

  500 will be returned on any server-side error

* **Sample Call:**
  With params specified in GET:
  ```bash
  curl -X GET \
  'https://edge-company-a.legion-test.epm.kharlamov.biz/api/model/test-summation/1.0/invoke?a=20&b=23'
  ```

  With params specified in POST:
  ```bash
  curl -X POST \
  https://edge-company-a.legion-test.epm.kharlamov.biz/api/model/test-summation/1.0/invoke \
  -F a=15 \
  -F b=27
  ```

  With list params (only for non-strict models):
  ```bash
  curl -X POST \
  https://edge-company-a.legion-test.epm.kharlamov.biz/api/model/test-name-rate/1.0/invoke \
  -F 'name[]=Alex' \
  -F 'name[]=Oleg'
  ```

  With file:
  ```
  curl -F "image=@examples/sklearn_demos/nine.png;filename=image" \
  http://edge-company-a.legion-test.epm.kharlamov.biz/api/model/image_recognize/1.0/invoke
  ```

* **Notes:**

  You can invoke model with lists. In this case you should use non-strict model
  and send each list value with a key ending in `[]`. For example `movie[]=Titanic` and `movie[]=Clockwork orange`.

  Files should be send as form-data files with specified file names.

  02.07.2018, Kirill Makhonin


**Model batch invocation**
----
  Running many predictions and getting many results in one request.

* **URL**

  `/api/model/:model_id/:model_version/batch`

  `/api/model/:model_id/:model_version/batch/:endpoint`

* **Method:**

  `POST`

*  **URL Params**

   **Required:**

   `model_id=[str]`- ID of model

   `model_version=[str]`- version of model

   **Optional:**

   `endpoint=[str]` - name of endpoint, `default` if omitted

* **Data Params**

  Request should contain request body. Request body contains line for each model
  invocation. Each line should consists of valid GET parameters (encoded)

* **Success Response:**

  Successful batch invocation of model should return 200 code and valid JSON response.
  Response is a valid JSON array, each value of which is a response for
  model invocation.

  * **Code:** 200 <br />
    **Content:**
    ```json
    [
        {
            "result": 30
        },
        {
            "result": 40
        }
    ]
    ```

* **Error Response:**

  500 will be returned on any server-side error

* **Sample Call:**

  ```bash
  curl -X POST \
  https://edge-company-a.legion-test.epm.kharlamov.biz/api/model/test-summation/1.0/batch \
  -d 'a=10&b=20
  a=10&b=30'
  ```

* **Notes:**

  Files cannot be send in batch mode.

  02.07.2018, Kirill Makhonin


