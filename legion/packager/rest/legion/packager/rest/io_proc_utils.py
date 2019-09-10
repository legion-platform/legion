#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import os.path
import stat
import logging
import subprocess
import zipfile

from legion.packager.rest.constants import RESOURCES_FOLDER

LOGGER = logging.getLogger(__name__)


def make_executable(path: str) -> None:
    """
    Make file executable

    :param path: path to file
    :type path: str
    :return: None
    """
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging instance

    :param verbose: use verbose output
    :type verbose: bool
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(format='[legion][%(levelname)5s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                        level=log_level)


def run(*args: str, cwd=None, stream_output: bool = True):
    """
    Run system command and stream / capture stdout and stderr

    :param args: Commands to run (list). E.g. ['cp, '-R', '/var/www', '/www']
    :type args: :py:class:`typing.List[str]`
    :param cwd: (Optional). Program working directory. Current is used if not provided.
    :type cwd: str
    :param stream_output: (Optional). Flag that enables streaming child process output to stdout and stderr.
    :return: typing.Union[int, typing.Tuple[int, str, str]] -- exit_code (for stream_output mode)
             or exit_code + stdout + stderr.
    """
    args_line = ' '.join(args)
    logging.info(f'Running command "{args_line}"')

    cmd_env = os.environ.copy()
    if stream_output:
        child = subprocess.Popen(args, env=cmd_env, cwd=cwd, universal_newlines=True,
                                 stdin=subprocess.PIPE)
        exit_code = child.wait()
        if exit_code != 0:
            raise Exception("Non-zero exitcode: %s" % exit_code)
        return exit_code
    else:
        child = subprocess.Popen(
            args, env=cmd_env, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, universal_newlines=True)
        (stdout, stderr) = child.communicate()
        exit_code = child.wait()
        if exit_code != 0:
            raise Exception("Non-zero exit code: %s\n\nSTDOUT:\n%s\n\nSTDERR:%s" %
                            (exit_code, stdout, stderr))
        return exit_code, stdout, stderr


def load_template(template_name) -> str:
    """
    Load template from resources folder

    :param template_name: name of template
    :type template_name: str
    :return: str -- template file content
    """
    logging.info(f'Loading template file {template_name} from {RESOURCES_FOLDER}')
    template_path = os.path.join(RESOURCES_FOLDER, template_name)
    with open(template_path, 'r') as template_stream:
        return template_stream.read()


def remove_directory(path):
    """
    Remove directory and all subdirectories or file

    :param path: path to directory or file
    :type path: str
    :return: None
    """
    try:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

            os.rmdir(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            raise Exception('Not a directory or file: %s' % path)
    finally:
        pass


def create_zip_archive(source_folder: str, archive_name: str, target_folder: str):
    """
    Create ZIP archive named <archive_name> in <target_folder> from folder <source_folder>

    :param source_folder: source folder
    :type source_folder: str
    :param archive_name: name of result archive (only file name, without folder)
    :type archive_name: str
    :param target_folder: target folder name (where archive will be placed)
    :type target_folder: str
    :return: str -- path to final archive
    """
    target_path = os.path.join(target_folder, archive_name)
    source_folder = os.path.abspath(source_folder)

    # Create archive
    zip_file = zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(source_folder):
        for file in files:
            local_path = os.path.join(root, file)
            arcname = local_path.replace(source_folder, '').lstrip(os.path.sep)
            zip_file.write(local_path, arcname=arcname)
    zip_file.close()

    return target_path
