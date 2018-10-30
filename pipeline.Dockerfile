FROM python:3.6

RUN apt-get update && apt-get install -y software-properties-common \
	&& apt-get install -y build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev git \
	&& apt-get clean all

RUN pip install Sphinx==1.8.0 sphinx_rtd_theme==0.4.1 sphinx-autobuild==0.7.1 recommonmark==0.4.0 pydocstyle==2.1.1 twine==1.11.0 boto==2.49.0 boto3==1.7.28 ansible==2.6.4 awscli==1.16.19

ADD legion /src/legion
RUN cd /src/legion \
	&& pip install -r requirements/base.txt \
	&& pip install -r requirements/test.txt \
	&& python setup.py develop \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel

ADD legion_test /src/legion_test
RUN cp /src/legion/legion/version.py /src/legion_test/legion_test/version.py \
	&& cd /src/legion_test \
	&& python setup.py develop \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel

ADD legion_airflow /src/legion_airflow
RUN cd /src/legion_airflow \
	&& cp /src/legion/legion/version.py /src/legion_airflow/legion_airflow/version.py \
	&& pip install -r requirements/base.txt \
	&& pip install -r requirements/test.txt \
	&& python setup.py develop \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel
	
