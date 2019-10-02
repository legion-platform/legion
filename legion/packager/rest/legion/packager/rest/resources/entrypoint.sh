#!/usr/bin/env bash

# Starting of Gunicorn server with Legion's HTTP handler

PATH={{ path }}:$PATH \
MODEL_LOCATION={{ model_location }} \
    {{ gunicorn_bin }} \
    --pythonpath {{ pythonpath }}/ \
    --timeout {{ timeout }} \
    -b {{ host }}:{{ port }} \
    -w {{ workers }} \
    --threads {{ threads }} \
    {{ wsgi_handler }}
