from argparse import Namespace
import logging
import time
import tempfile
import os
import glob
from unittest.mock import patch

import docker
import docker.errors

import legion.config
import legion.containers.docker
import legion.io
import legion.model.client
import legion.serving.pyserve as pyserve
import legion.model.model_id
from legion.model import ModelClient
from legion.utils import remove_directory
import legion.edi.deploy as deploy

LOGGER = logging.getLogger(__name__)


def deploy_model(args):
    """
    Deploy model to docker host

    :param args: command arguments with .model_id, .model_file, .docker_network
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Container` new instance
    """
    client = legion.containers.docker.build_docker_client(args)
    network_id = legion.containers.docker.find_network(client, args)

    if args.model_id and args.docker_image:
        print('Use only --model-id or --docker-image')
        exit(1)
    elif not args.model_id and not args.docker_image:
        print('Use with --model-id or --docker-image')
        exit(1)

    current_containers = legion.containers.docker.get_stack_containers_and_images(client, network_id)

    if args.model_id:
        for image in current_containers['model_images']:
            model_name = image.labels.get('com.epam.legion.model.id', None)
            if model_name == args.model_id:
                image = image
                model_id = model_name
                break
        else:
            raise Exception('Cannot found image for model_id = %s' % (args.model_id,))
    elif args.docker_image:
        try:
            image = client.images.get(args.docker_image)
        except docker.errors.ImageNotFound:
            print('Cannot find %s locally. Pulling' % args.docker_image)
            image = client.images.pull(args.docker_image)

        model_id = image.labels.get('com.epam.legion.model.id', None)
        if not model_id:
            raise Exception('Cannot detect model_id in image')
    else:
        raise Exception('Provide model-id or docker-image')

    # Detect current existing containers with models, stop and remove them
    LOGGER.info('Founding containers with model_id=%s', model_id)

    for container in current_containers['models']:
        model_name = container.labels.get('com.epam.legion.model.id', None)
        if model_name == model_id:
            LOGGER.info('Stopping container #%s', container.short_id)
            container.stop()
            LOGGER.info('Removing container #%s', container.short_id)
            container.remove()

    container_labels = legion.containers.docker.generate_docker_labels_for_container(image)

    ports = {}
    if args.expose_model_port is not None:
        exposing_port = args.expose_model_port
        ports['%d/tcp' % os.getenv(*legion.config.LEGION_PORT)] = exposing_port

    LOGGER.info('Starting container with image #%s for model %s', image.short_id, model_id)
    container = client.containers.run(image,
                                      network=network_id,
                                      stdout=True,
                                      stderr=True,
                                      detach=True,
                                      ports=ports,
                                      labels=container_labels)

    print('Successfully created docker container %s for model %s' % (container.short_id, model_id))
    return container


def get_latest_distribution():
    """
    Get path to latest distribution file

    :return: str -- path to file
    """
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist'))
    if not os.path.exists(dist_dir):
        raise Exception('Cannot find dist dir: %s' % dist_dir)

    list_of_files = glob.glob('%s/*.whl' % (dist_dir,))
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def patch_environ(values, flush_existence=False):
    """
    Patch environment with values

    :param values: new values
    :type values: dict[str, str]
    :param flush_existence: flush (clear before overwrite) or not
    :type flush_existence: bool
    :return: unittest2.mock.patch result
    """
    if flush_existence:
        new_values = values
    else:
        new_values = os.environ.copy()
        new_values.update(values)

    return patch('os.environ', new_values)


class ModelServeTestBuild:
    """
    Context manager for building and testing models with pyserve
    """

    def __init__(self, model_id, model_version, model_builder):
        """
        Create context

        :param model_id: id of model (uses for building model and model client)
        :type model_id: str
        :param model_version: version of model (passes to model builder)
        :param model_builder: str
        """
        self._model_id = model_id
        self._model_version = model_version
        self._model_builder = model_builder

        self._temp_directory = tempfile.mkdtemp()
        self._model_path = os.path.join(self._temp_directory, 'temp.model')

        self.application = None
        self.client = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """
        try:
            print('Building model file {} v {}'.format(self._model_id, self._model_version))
            legion.model.model_id._model_id = self._model_id
            legion.model.model_id._model_initialized_from_function = True
            self._model_builder(self._model_path, self._model_version)
            print('Model file has been built')

            print('Creating pyserve')
            additional_environment = {
                legion.config.REGISTER_ON_GRAFANA[0]: 'false',
                legion.config.MODEL_ID[0]: self._model_id,
                legion.config.MODEL_FILE[0]: self._model_path
            }
            with patch_environ(additional_environment):
                self.application = pyserve.init_application(None)
                self.application.testing = True
                self.client = self.application.test_client()

            return self
        except Exception as build_exception:
            self.__exit__(exception=build_exception)

    def __exit__(self, *args, exception=None):
        """
        Exit from context with cleaning fs temp directory, temporary container and image

        :param args: list of arguements
        :return: None
        """
        print('Removing temporary directory')
        remove_directory(self._temp_directory)

        if exception:
            raise exception


class ModelTestDeployment:
    """
    Context manager for building and testing models
    Hides build and deploy process and provides model client
    """

    def __init__(self, model_id, model_version, model_builder, wheel):
        """
        Create context

        :param model_id: id of model (uses for building model and model client)
        :type model_id: str
        :param model_version: version of model (passes to model builder)
        :param model_builder: str
        :param wheel: path to actual package wheel
        :type wheel: str
        """
        self._model_id = model_id
        self._model_version = model_version
        self._model_builder = model_builder
        self._wheel = wheel
        self._docker_client = legion.containers.docker.build_docker_client(None)

        self._temp_directory = tempfile.mkdtemp()
        self._model_path = os.path.join(self._temp_directory, 'temp.model')

        self.image = None
        self.container = None
        self.container_id = None
        self.model_port = None
        self.client = None

    def __enter__(self):
        """
        Enter into context

        :return: self
        """
        try:
            print('Building model file {} v {}'.format(self._model_id, self._model_version))
            legion.model.model_id.init(self._model_id)
            self._model_builder(self._model_path, self._model_version)
            print('Model file has been built')

            print('Building model image {} v {}'.format(self._model_id, self._model_version))
            args = Namespace(
                model_file=self._model_path,
                model_id=None,
                base_docker_image=None,
                docker_network=None,
                python_package=self._wheel,
                python_package_version=None,
                python_repository=None,
                docker_image_tag=None,
                serving=deploy.VALID_SERVING_WORKERS[1],
                push_to_registry=None
            )
            self.image = deploy.build_model(args)
            print('Model image has been built')

            print('Deploying model {} v {}'.format(self._model_id, self._model_version))
            additional_environment = {
                legion.config.REGISTER_ON_GRAFANA[0]: 'false',
            }
            with patch_environ(additional_environment):
                args = Namespace(
                    model_id=self._model_id,
                    docker_image=None,
                    docker_network=None,
                    grafana_server=None,
                    grafana_user=None,
                    grafana_password=None,
                    expose_model_port=0
                )
                self.container = deploy_model(args)
                self.container_id = self.container.id
            print('Model image has been deployed')

            wait = 3
            print('Waiting {} sec'.format(wait))
            time.sleep(wait)
            self.container = self._docker_client.containers.get(self.container_id)
            if self.container.status != 'running':
                try:
                    logs = self.container.logs().decode('utf-8')

                    print('--- CONTAINER LOGS ---')
                    print(logs)
                except Exception:
                    print('Cannot get logs of container')

                raise Exception('Invalid container state: {}'.format(self.container.status))
            print('OK')

            print('Detecting bound ports')
            ports_information = [item for sublist in self.container.attrs['NetworkSettings']['Ports'].values()
                                 for item in sublist]
            ports_information = [int(x['HostPort']) for x in ports_information]
            print('Detected ports: {}'.format(', '.join(str(port) for port in ports_information)))

            if len(ports_information) != 1:
                raise Exception('Should be only one bound port')
            self.model_port = ports_information[0]
            print('Model port: {}'.format(self.model_port))

            print('Building client')
            url = 'http://{}:{}'.format('localhost', self.model_port)
            print('Target URI is {}'.format(url))
            self.client = ModelClient(self._model_id, url)

            print('Getting model information')
            self.model_information = self.client.info()

            return self
        except Exception as build_exception:
            self.__exit__(build_exception)

    def __exit__(self, *args):
        """
        Exit from context with cleaning fs temp directory, temporary container and image

        :param args: list of arguements
        :return: None
        """
        print('Removing temporary directory')
        remove_directory(self._temp_directory)

        if self.container:
            try:
                print('Finding container')
                container = self._docker_client.containers.get(self.container.id)
                try:
                    logs = self.container.logs().decode('utf-8')

                    print('--- CONTAINER LOGS ---')
                    print(logs)
                except Exception as log_get_exception:
                    print('Cannot get logs of container: {}'.format(log_get_exception))
                print('Stopping container')
                container.stop()
                print('Removing container')
                container.remove()
            except Exception as removing_exception:
                print('Cannot remove container: {}'.format(removing_exception))

        if self.image:
            try:
                print('Removing image')
                self._docker_client.images.remove(self.image.id)
            except Exception as removing_exception:
                print('Cannot remove image: {}'.format(removing_exception))

        if args[0]:
            raise args[0]
