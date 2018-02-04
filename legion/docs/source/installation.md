# Installation
Installation tested on Ubuntu 16.04 and Windows Subsystem for Linux (WSL).

## Requirements
* Python 3.5 with PIP
* Docker / Docker for Windows
* Docker-compose
* Docker-machine
* MacOS / Linux / Windows Subsystem for Linux

## Credential requirements
* Git SSH access key (private) for legion-root repository

## Installation process
* Clone repo ( `git clone https://github.com/akharlamov/legion-root` )
* Build docker image in directory base-python-image ( `./build.sh` )
* Add next lines to hosts file ( `/etc/hosts` )
```text
127.0.0.1 parallels
127.0.0.1 consul
127.0.0.1 jupyter
127.0.0.1 legion
127.0.0.1 grafana
127.0.0.1 jenkins
127.0.0.1 graphite
127.0.0.1 edge
127.0.0.1 consul
127.0.0.1 logstash
127.0.0.1 kibana
127.0.0.1 elasticsearch
```
* Install Linux dependencies
```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
     g++ apt-utils python3-dev python3-pip python3-setuptools file wget git \
     libtiff5-dev libjpeg8-dev zlib1g-dev \
     tcl8.6-dev tk8.6-dev python-tk python3-tk \
     libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev     
```
* Install python dependencies
```bash
sudo pip3 install wheel
sudo pip3 install -r legion-root/legion/requirements/base.txt
sudo pip3 install -r legion-root/legion/requirements/test.txt
```
* Install legion package and create wheel in legion-root/legion folder
```bash
sudo python3 setup.py develop
sudo python3 setup.py bdist_wheel
```
* Create docker-machine with local host (use *general driver*)
```bash
docker-machine create --driver generic --generic-ip-address 127.0.0.1 --generic-ssh-key ~/.ssh/id_rsa --generic-ssh-user user default
```
* Copy docker-machine keys
```bash
mkdir -p keys/docker/
cp -f ${DOCKER_CERT_PATH}/*.pem keys/docker/
cp -f ${DOCKER_CERT_PATH}/*.json keys/docker/
cp -f ${DOCKER_CERT_PATH}/*.pub keys/docker/
cp -f ${DOCKER_CERT_PATH}/*.pub keys/docker/
cp -f ${DOCKER_CERT_PATH}/../../certs/*.pem keys/docker/
chmod uga+r keys/docker/*
```
* Copy git ssh access key to *keys/git-deploy.key*
* Increase `vm.max_map_count` system variable up to 262144: add `vm.max_map_count=262144` to `/etc/sysctl.conf`
* Reboot machine