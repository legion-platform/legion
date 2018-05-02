# Legion

Legion is a command line interface for manipulating with models.

## Usage
```bash
usage: legionctl [-h] [--verbose]
              {build,deploy-local,undeploy-local,inspect-local,deploy,inspect,scale,undeploy,pyserve} ...

legion Command-Line Interface

positional arguments:
  {build,deploy-local,undeploy-local,inspect-local,deploy,inspect,scale,undeploy,pyserve}

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose log output

```

### legionctl build
```bash
usage: legionctl build [-h] [--model_id MODEL_ID] [--model-type MODEL_TYPE]
                       [--python-package PYTHON_PACKAGE]
                       [--python-package-version PYTHON_PACKAGE_VERSION]
                       [--python-repository PYTHON_REPOSITORY]
                       [--base-docker-image BASE_DOCKER_IMAGE]
                       [--docker-image-tag DOCKER_IMAGE_TAG]
                       [--push-to-registry PUSH_TO_REGISTRY] [--with-deploy]
                       [--serving SERVING]
                       model_file

build model into new docker image

positional arguments:
  model_file            serialized model file name
  model_id

optional arguments:
  -h, --help            show this help message and exit
  --model-id            alpha-numeric identifier of the model to publish
  --model-type MODEL_TYPE
                        legion-python, tensorflow, mleap
  --python-package PYTHON_PACKAGE
                        path to legion-python package wheel
  --python-package-version PYTHON_PACKAGE_VERSION
                        version of python package
  --python-repository PYTHON_REPOSITORY
                        package server with legion package
  --base-docker-image BASE_DOCKER_IMAGE
                        base docker image for new image
  --docker-image-tag DOCKER_IMAGE_TAG
                        docker image tag
  --push-to-registry PUSH_TO_REGISTRY
                        docker registry address
  --with-deploy         deploy after build
  --serving SERVING     serving worker

```

### legionctl deploy
```bash
usage: legionctl deploy [-h] [--image-for-k8s IMAGE_FOR_K8S] [--scale SCALE]
                        [--edi EDI] [--user USER] [--password PASSWORD]
                        [--token TOKEN] [--no-wait]
                        [--wait-timeout WAIT_TIMEOUT]
                        image

deploys a model into a kubernetes cluster

positional arguments:
  image                 docker image

optional arguments:
  -h, --help            show this help message and exit
  --image-for-k8s IMAGE_FOR_K8S
                        docker image for kubernetes deployment
  --scale SCALE         count of instances
  --edi EDI             EDI server host
  --user USER           EDI server user
  --password PASSWORD   EDI server password
  --token TOKEN         EDI server token
  --no-wait             wait until pods will be ready
  --wait-timeout WAIT_TIMEOUT
                        timeout in s. for wait (if no-wait is off). Infinite
                        if 0

```

### legionctl deploy-local
```bash
usage: legionctl deploy-local [-h] [--model-id MODEL_ID]
                              [--docker-image DOCKER_IMAGE]
                              [--docker-network DOCKER_NETWORK]
                              [--grafana-server GRAFANA_SERVER]
                              [--grafana-user GRAFANA_USER]
                              [--grafana-password GRAFANA_PASSWORD]
                              [--expose-model-port EXPOSE_MODEL_PORT]

deploys a model into a new container (local docker)

optional arguments:
  -h, --help            show this help message and exit
  --model-id MODEL_ID   model id
  --docker-image DOCKER_IMAGE
                        docker sha256 image
  --docker-network DOCKER_NETWORK
                        docker network
  --grafana-server GRAFANA_SERVER
                        Grafana server
  --grafana-user GRAFANA_USER
                        Grafana user
  --grafana-password GRAFANA_PASSWORD
                        Grafana password
  --expose-model-port EXPOSE_MODEL_PORT
                        Expose model at specific port

```

### legionctl undeploy
```bash
usage: legionctl deploy-local [-h] [--model-id MODEL_ID]
                              [--docker-image DOCKER_IMAGE]
                              [--docker-network DOCKER_NETWORK]
                              [--grafana-server GRAFANA_SERVER]
                              [--grafana-user GRAFANA_USER]
                              [--grafana-password GRAFANA_PASSWORD]
                              [--expose-model-port EXPOSE_MODEL_PORT]

deploys a model into a new container (local docker)

optional arguments:
  -h, --help            show this help message and exit
  --model-id MODEL_ID   model id
  --docker-image DOCKER_IMAGE
                        docker sha256 image
  --docker-network DOCKER_NETWORK
                        docker network
  --grafana-server GRAFANA_SERVER
                        Grafana server
  --grafana-user GRAFANA_USER
                        Grafana user
  --grafana-password GRAFANA_PASSWORD
                        Grafana password
  --expose-model-port EXPOSE_MODEL_PORT
                        Expose model at specific port

```

### legionctl undeploy-local
```bash
usage: legionctl undeploy-local [-h] [--docker-network DOCKER_NETWORK]
                                [--grafana-server GRAFANA_SERVER]
                                [--grafana-user GRAFANA_USER]
                                [--grafana-password GRAFANA_PASSWORD]
                                model_id

kills all containers service the model (local docker)

positional arguments:
  model_id              identifier of the model

optional arguments:
  -h, --help            show this help message and exit
  --docker-network DOCKER_NETWORK
                        docker network
  --grafana-server GRAFANA_SERVER
                        Grafana server
  --grafana-user GRAFANA_USER
                        Grafana user
  --grafana-password GRAFANA_PASSWORD
                        Grafana password

```

### legionctl inspect
```bash
usage: legionctl inspect [-h] [--edi EDI] [--user USER] [--password PASSWORD]
                         [--token TOKEN] [--filter FILTER]
                         [--format {colorized,column}]

get information about currently deployed models

optional arguments:
  -h, --help            show this help message and exit
  --edi EDI             EDI server host
  --user USER           EDI server user
  --password PASSWORD   EDI server password
  --token TOKEN         EDI server token
  --filter FILTER       Model ID filter
  --format {colorized,column}
                        output format

```

### legion pyserve
```bash
usage: legionctl pyserve [-h] [--model_file MODEL_FILE] [--model-id MODEL_ID]
                         [--consul-addr CONSUL_ADDR]
                         [--consul-port CONSUL_PORT]
                         [--legion-addr LEGION_ADDR]
                         [--legion-port LEGION_PORT] [--debug DEBUG]
                         [--register-on-consul REGISTER_ON_CONSUL]
                         [--legion-autodiscover LEGION_AUTODISCOVER]

serve a python model

optional arguments:
  -h, --help            show this help message and exit
  --model_file MODEL_FILE
  --model-id MODEL_ID
  --consul-addr CONSUL_ADDR
                        Consul Agent IP address
  --consul-port CONSUL_PORT
                        Consul Agent port
  --legion-addr LEGION_ADDR
  --legion-port LEGION_PORT
  --debug DEBUG
  --register-on-consul REGISTER_ON_CONSUL
  --legion-autodiscover LEGION_AUTODISCOVER

```
