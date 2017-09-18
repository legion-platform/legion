import os
import tempfile
import docker
from jinja2 import Environment, PackageLoader, select_autoescape

from traitlets import HasTraits, Unicode, default


class BuildInfo(HasTraits):

    version = Unicode()

    @default('version')
    def default_version(self):
        return "UNKNOWN"


def build_docker_image(config_file, ):
    docker_client = docker.from_env()


def deploy_model(args):
    tmpdir = tempfile.tempdir

    (folder, model_filename) = os.path.split(args.model_file)

    instance_cfg = {
        'MODEL_ID': args.model_id,
        'MODEL_FILE': model_filename
    }

    env = Environment(
        loader=PackageLoader('legion', 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    return

def undeploy_model(args):
    return
