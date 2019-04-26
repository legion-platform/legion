FROM python:3.5-alpine3.9

RUN apk --update add ttf-dejavu graphviz git

RUN    pip install --upgrade pip \
    && pip install \
              sphinx==1.8.0 \
              sphinx_rtd_theme==0.4.1 \
              sphinx-autobuild==0.7.1 \
              recommonmark==0.5.0 \
              sphinx-markdown-tables==0.0.9 \
              git+https://github.com/brechtm/rinohtype.git@40a63c4e5ad7550f62b6860f1812cb67cafb9dc7


ADD containers/docs-builder/generate.sh /
RUN chmod +x /generate.sh