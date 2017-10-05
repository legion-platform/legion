FROM library/ubuntu:16.04

ADD requirements.txt /root/requirements.txt

# Theano requires C++ compiler to produce effective code
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    g++ apt-utils python3-dev python3-pip python3-setuptools file wget git \
    libtiff5-dev libjpeg8-dev zlib1g-dev \
    tcl8.6-dev tk8.6-dev python-tk python3-tk \
    libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev \
    tcl8.6-dev tk8.6-dev python-tk python3-tk



RUN pip3 install --upgrade pip \
    && pip3 install -r /root/requirements.txt

WORKDIR /app
