try:
    import docker_bootup
except ImportError:
    pass

from jupyter_core.application import JupyterApp

import sys

sys.exit(JupyterApp.launch_instance(
    argv=[
        'notebook',
        '--allow-root'
    ]))
