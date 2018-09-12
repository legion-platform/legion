FROM python:3.6-alpine

RUN apk add --update docker alpine-sdk libressl-dev libffi-dev zlib-dev jpeg-dev maven git ansible nodejs npm

RUN pip install Sphinx sphinx_rtd_theme sphinx-autobuild recommonmark pydocstyle twine boto boto3 awscli \

ADD legion /src/legion
RUN cd /src/legion \
	&& pip install -r requirements/base.txt \
	&& pip install -r requirements/test.txt \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel \
	&& python setup.py develop

ADD legion_test /src/legion_test
RUN cp /src/legion/legion/version.py /src/legion_test/legion_test/version.py \
	&& cd /src/legion_test \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel \
	&& python setup.py develop

ADD legion_airflow /src/legion_airflow
RUN cd /src/legion_airflow
	&& cp /src/legion/legion/version.py /src/legion_airflow/legion_airflow/version.py \
	&& pip install -r requirements/base.txt \
	&& pip install -r requirements/test.txt \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel \
	&& python setup.py develop
	
