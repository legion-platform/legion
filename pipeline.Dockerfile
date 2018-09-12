FROM python:3.6-alpine

RUN apk add --update docker alpine-sdk libressl-dev libffi-dev zlib-dev jpeg-dev maven git ansible nodejs npm

COPY legion/requirements/base.txt legion/requirements/test.txt /src/legion/requirements/
RUN pip install -r /src/legion/requirements/base.txt \
	&& pip install -r /src/legion/requirements/test.txt \
	&& pip install Sphinx sphinx_rtd_theme sphinx-autobuild recommonmark pydocstyle twine boto boto3 awscli \

COPY legion_test/setup.py /src/legion_test/setup.py
RUN cd /src/legion_test && python setup.py develop


