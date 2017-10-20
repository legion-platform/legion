# Restful API
Each model automatically registers on server with his own url prefix based on model id.

URL prefix schema is: `http://parallels/api/model/MODEL_ID/`.

For example, for model income 
it will be [http://parallels/api/model/income/](http://parallels/api/model/income/).

## API methods
### /info [GET]
Get information about model (name, version, input).

For example [http://parallels/api/model/income/info](http://parallels/api/model/income/info).

### /invoke [GET / POST]
Calculate model result.

Input fields should be passed as GET parameters in URI or as form-data fields.

For example [http://parallels/api/model/income/invoke](http://parallels/api/model/income/invoke).
```
POST /api/model/income/invoke HTTP/1.1
Host: parallels
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="age"

12
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

## Sending files
For sending files from command line you may use 
```
curl -F "image=@examples/sklearn_demos/nine.png;filename=image"  http://parallels/api/model/image_recognize/invoke
```