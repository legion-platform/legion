import subprocess

from legion.toolchain import model


model.init('native model', '1.0')

installation_result = subprocess.run('apt update && apt install -y mc',
                                     cwd='/', shell=True,
                                     stdout=subprocess.PIPE)
if installation_result.returncode != 0:
    raise Exception('Invalid result code {}: \n{}'.format(installation_result.returncode,
                                                          installation_result.stdout.decode('utf-8')))


def calculate(x):
    info = subprocess.run('mc --help', cwd='/', shell=True)
    return info.returncode


model.export_untyped(lambda x: {'code': calculate(x)})
model.save()
