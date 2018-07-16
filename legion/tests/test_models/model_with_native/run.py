import subprocess

from legion.model.model_id import init
import legion.io


init('native model')

installation_result = subprocess.run('apk add --update --no-cache mc',
                                     cwd='/', shell=True,
                                     stdout=subprocess.PIPE)
if installation_result.returncode != 0:
    raise Exception('Invalid result code {}: \n{}'.format(installation_result.returncode,
                                                          installation_result.stdout.decode('utf-8')))


def calculate(x):
    info = subprocess.run('mc --help', cwd='/', shell=True)
    return info.returncode


legion.io.export_untyped(lambda x: {'code': calculate(x)},
                         filename='native.model',
                         version='1.0')
