# DRun


## Requirements
* Python 2.7 / 3.5 (with setuptools)
* Docker / Docker for Windows
* Docker Compose
* MacOS / Linux / Windows Subsystem for Linux

## Installation
* Clone repo ( `git clone https://github.com/akharlamov/drun-root` )
* Build docker image in directory base-python-image ( `cd base-python-image && docker build . && cd -` )
* Get latest installed image ID ( `docker images -q | head -n 1` )
* Add tag drun/base-python-image to image ( `docker tag <image id> drun/base-python-image` )
* For local installation add to hosts file
```
127.0.0.1 parallels
127.0.0.1 consul
127.0.0.1 jupyter
127.0.0.1 legion
127.0.0.1 grafana
```
* Install drun package ( `cd drun && sudo python3 setup.py develop && cd -` )
* In project root call `./stack -f docker-compose.dev.yml up`

## Usage
* Open http://parallels/jupyter
* Open DRun experimental notebook. Show how we export the model
* Run the notebook and export a model
* Deploy a container with model using
`legion deploy --model-id <id, for example: income> --model-file <file>`
* Go to consul http://consul:8500/ui/# and show model is registered
* Use Postman to show invocations through Restful API
* (optional) Go to grafana and show stats
* (optional) Show automatic dashboard creation

## Restful API
Each model automatically registers on server with his own url prefix based on model id.

URL prefix schema is: http://parallels/api/model/MODEL_ID/.
For example, for model income it will be http://parallels/api/model/income/.

### API methods
#### /info [GET]
Get information about model (name, version, input).
For example http://parallels/api/model/income/info.

#### /invoke [GET / POST]
Calculate model result.

Input fields should be passed as GET parameters in URI or as form-data fields.

For example http://parallels/api/model/income/invoke.
```
POST /api/model/income/invoke HTTP/1.1
Host: parallels
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="age"

12
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

## Additional
* For external docker installation set: `DOCKER_HOST="tcp://host:ip"` (for example `DOCKER_HOST="tcp://127.0.0.1:2375"`) enviroment variable.


