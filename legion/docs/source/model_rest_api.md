# RESTful API
Each model automatically registers on Edge server with his own url prefix based on model id.
Edge server host name contains **enclave** name.

URL prefix schema is: `http://edge-ENCLAVE.host/api/model/MODEL_ID/`.

For example, for an **income* model in *enclave-a**.
it will be [http://edge-enclave-a.host/api/model/income/](http://edge-enclave-a.host/api/model/income/).

## API methods
### /info [GET]
Get information about a model in enclave (name, version, input).

For example, for an **income** model in **enclave-a**.
 [http://edge-enclave-a.host/api/model/income/info](http://edge-encalve-a.host/api/model/income/info).

### /invoke [GET / POST]
Invoke a model with passed input parameters.

Input fields should be passed as GET parameters in URI or as form-data fields.

For example, for an **income** model in **enclave-a**.
 [http://edge-enclave-a.host/api/model/income/invoke](http://edge-enclave-a.host/api/model/income/invoke).
```
POST /api/model/income/invoke HTTP/1.1
Host: edge-enclave-a.host
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="age"

12
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

## Sending files as an invocation parameter
Files can be used as input parameters for a model invocation.
*curl* utilit can be used to send a file to a model.

For example, to pass **nine.png** to an **image_recognize** model in **enclave-a**:
```
curl -F "image=@examples/sklearn_demos/nine.png;filename=image"  http://edge-enclave-a.host/api/model/image_recognize/invoke
```