#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
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
