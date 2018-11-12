FROM python:3.6

RUN apt-get update && apt-get install -y software-properties-common \
	&& apt-get install -y build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev git \
	&& apt-get clean all

RUN pip install --disable-pip-version-check --upgrade pip==9.0.3 pipenv==2018.10.13

# Install requirements for legion package
ADD legion/requirements/Pipfile /src/legion/requirements/Pipfile
ADD legion/requirements/Pipfile.lock /src/legion/requirements/Pipfile.lock
RUN cd /src/requirements/legion && pipenv install --system --dev

# Install requirements for legion_test package
ADD legion_test/requirements/Pipfile /src/legion_test/requirements/Pipfile
ADD legion_test/requirements/Pipfile.lock /src/legion_test/Prequirements/ipfile.lock
RUN cd /src/requirements/legion_test && pipenv install --system --dev

# Install requirements for legion_airflow package
ADD legion_airflow/requirements/Pipfile /src/requirements/legion_airflow/Pipfile
ADD legion_airflow/requirements/Pipfile.lock /src/requirements/legion_airflow/Pipfile.lock
RUN cd /src/requirements/legion_airflow && pipenv install --system --dev

# Install additional tools for build purposes
RUN pip install Sphinx==1.8.0 sphinx_rtd_theme==0.4.1 sphinx-autobuild==0.7.1 recommonmark==0.4.0 twine==1.11.0 ansible==2.6.4 awscli==1.16.19

# Add sources


ADD legion /src/legion
RUN cd /src/legion \
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
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel