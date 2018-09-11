FROM python:3.6-alpine

RUN apk add --update docker alpine-sdk libressl-dev libffi-dev zlib-dev jpeg-dev maven git

COPY legion/requirements/base.txt legion/requirements/test.txt /

RUN pip install -r /base.txt \
	&& pip install -r /test.txt \
	&& pip install --user Sphinx sphinx_rtd_theme sphinx-autobuild recommonmark pydocstyle twine \
	&& cd legion_test && python setup.py develop


