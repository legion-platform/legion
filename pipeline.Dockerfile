FROM python:3.6

ENV DOCKERVERSION=18.03.1-ce

RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
  && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 \
                 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKERVERSION}.tgz

RUN apt-get update && apt-get install -y software-properties-common \
	&& echo 'deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main' >> /etc/apt/sources.list \
	&& apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367 \
	&& apt-get update \
	&& curl -sL https://deb.nodesource.com/setup_8.x | bash - \
	&& apt-get install -y build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev maven git ansible nodejs \
	&& apt-get clean all

RUN pip install Sphinx sphinx_rtd_theme sphinx-autobuild recommonmark pydocstyle twine boto boto3 awscli

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
RUN cd /src/legion_airflow \
	&& cp /src/legion/legion/version.py /src/legion_airflow/legion_airflow/version.py \
	&& pip install -r requirements/base.txt \
	&& pip install -r requirements/test.txt \
	&& python setup.py sdist \
	&& python setup.py bdist_wheel \
	&& python setup.py develop
	
