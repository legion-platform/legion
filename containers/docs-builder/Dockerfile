
FROM python:3-alpine

ENV LIBRARY_PATH=/lib:/usr/lib
RUN apk --update --no-cache add \
    bash \
    coreutils \
    git \
    make \
    ttf-dejavu \
    graphviz \
    build-base python3-dev jpeg-dev zlib-dev zip \
    && apk upgrade

COPY containers/docs-builder/requirements.txt \
     /requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /requirements.txt

ADD containers/docs-builder/generate.sh /
RUN chmod +x /generate.sh