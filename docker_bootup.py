import os
import sys

print("Executing docker dev bootup")

SUBPROJECT_DIRS = ['/opt/project/drun', '/opt/project/jupyter']

sys.path.extend(SUBPROJECT_DIRS)

# Patching up environment for subprocesses (needed for Jupyter kernels)
os.environ['PYTHONPATH'] = ':'.join(SUBPROJECT_DIRS)

print("sys.path:", sys.path)

try:
    host = os.environ['PYDEVD_HOST']
    port = os.environ['PYDEVD_PORT']
    print("PYDEVD_HOST:", host)
    print("PYDEVD_PORT:", port)
    if host != "" and port != "":
        import pydevd

        pydevd.settrace(
            host=host,
            port=int(port),
            suspend=False,
            patch_multiprocessing=True)
except Exception as e:
    print('Unable to connect to pydevd. Ignoring...', e)
