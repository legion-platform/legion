# Legion

Legion is a command line interface for manipulating with models.

## Usage
```bash
usage: legion [-h] [--verbose]
              {build,deploy,undeploy,inspect,pyserve,pyserve-dummy} ...

DRun Command-Line Interface

positional arguments:
  {build,deploy,undeploy,inspect,pyserve,pyserve-dummy}

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose log output

```

### legion build
```bash
usage: legion build [-h] [--model-type MODEL_TYPE]
                    [--python-package PYTHON_PACKAGE]
                    [--base-docker-image BASE_DOCKER_IMAGE]
                    [--docker-image-tag DOCKER_IMAGE_TAG]
                    model_file model_id

build model into new docker image

positional arguments:
  model_file            serialized model file name
  model_id              alpha-numeric identifier of the model to publish

optional arguments:
  -h, --help            show this help message and exit
  --model-type MODEL_TYPE
                        drun-python, tensorflow, mleap
  --python-package PYTHON_PACKAGE
                        path to drun-python package wheel
  --base-docker-image BASE_DOCKER_IMAGE
                        base docker image for new image
  --docker-image-tag DOCKER_IMAGE_TAG
                        docker image tag

```

### legion deploy
```bash
usage: legion deploy [-h] [--model-id MODEL_ID] [--docker-image DOCKER_IMAGE]
                     [--docker-network DOCKER_NETWORK]
                     [--grafana-server GRAFANA_SERVER]
                     [--grafana-user GRAFANA_USER]
                     [--grafana-password GRAFANA_PASSWORD]

deploys a model into a new container

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

```

### legion undeploy
```bash
usage: legion undeploy [-h] [--docker-network DOCKER_NETWORK]
                       [--grafana-server GRAFANA_SERVER]
                       [--grafana-user GRAFANA_USER]
                       [--grafana-password GRAFANA_PASSWORD]
                       model_id

kills all containers service the model

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

### legion inspect
```bash
usage: legion inspect [-h] [--docker-network DOCKER_NETWORK]

get information about docker network state

optional arguments:
  -h, --help            show this help message and exit
  --docker-network DOCKER_NETWORK
                        docker network

```

### legion pyserve
```bash
usage: legion pyserve [-h] [--consul-addr CONSUL_ADDR]
                      [--consul-port CONSUL_PORT] [--legion-addr LEGION_ADDR]
                      [--legion-port LEGION_PORT]
                      model_file model_id

serve a python model

positional arguments:
  model_file
  model_id

optional arguments:
  -h, --help            show this help message and exit
  --consul-addr CONSUL_ADDR
                        Consul Agent IP address
  --consul-port CONSUL_PORT
                        Consul Agent port
  --legion-addr LEGION_ADDR
  --legion-port LEGION_PORT

```

### legion pyserve-dummy
```bash
usage: legion pyserve-dummy [-h] [--consul-addr CONSUL_ADDR]
                            [--consul-port CONSUL_PORT]
                            [--legion-addr LEGION_ADDR]
                            [--legion-port LEGION_PORT]

serve a dummy python model

optional arguments:
  -h, --help            show this help message and exit
  --consul-addr CONSUL_ADDR
                        Consul Agent IP address
  --consul-port CONSUL_PORT
                        Consul Agent port
  --legion-addr LEGION_ADDR
  --legion-port LEGION_PORT

```