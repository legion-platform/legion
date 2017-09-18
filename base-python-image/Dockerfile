FROM library/ubuntu:16.04

ADD requirements.txt /root/requirements.txt

# Theano requires C++ compiler to produce effective code
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    g++ apt-utils python-dev python-pip python-setuptools file wget



RUN pip install --upgrade pip \
    && pip install -r /root/requirements.txt

WORKDIR /app
