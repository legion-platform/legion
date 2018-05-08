# RESTful API
Each model automatically registers on Edge server with his own url prefix based on model id.
Edge server host name contains **enclave** name.

URL prefix schema is: `http://edge-ENCLAVE.cluster-domain/api/model/MODEL_ID/`.

For example, for an **income** model in **company-a** enclave of **legion-dev** cluster,
URL should be [http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/](http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/).

## API methods
### /info [GET]
Get information about a model in enclave (name, version, input parameters).

For example, for an **income** model in **company-a** tenant of **legion-dev** cluster,
URL should be [http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/info](http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/info).

### /invoke [GET / POST]
Invoke a model with passed input parameters.

There are two model types:
* *typed* - they have strongly defined parameters types and names, which names and types can be found in **info** endpoint;
* *untyped* - they don't have strongly defined parameters, due to its complex composite types.

Input parameters should be passed as GET parameters in URL or as POST request body.

For example, for an **income** model in **company-a** tenant of **legion-dev** cluster,
URL should be [http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/invoke](http://edge-company-a.legion-dev.epm.kharlamov.biz/api/model/income/invoke).
Parameters can be sent with GET or POST HTTP methodsю

#### Sending parameters via GET method
```
GET /api/model/income/invoke?age=12 HTTP/1.1
Host: edge-company-a.legion-dev.epm.kharlamov
```

#### Sending parameters via POST method
```
POST /api/model/income/invoke HTTP/1.1
Host: edge-company-a.legion-dev.epm.kharlamov
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="age"

12
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

## Sending files as an invocation parameter
Files can be used as input parameters for a model invocation.

For example, **nine.png** file can be passed as a parameter to an **image_recognize** model in **company-a** using **curl** utilit:
```
curl -F "image=@examples/sklearn_demos/nine.png;filename=image"  http://edge-company-a.legion-dev.epm.kharlamov/api/model/image_recognize/invoke
```