"""
DRun utils functional
"""

import socket
import tempfile
import os


def detect_ip():
    """
    Get current machine IP address
    :return: str IP address
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    addr = sock.getsockname()[0]
    sock.close()
    return addr


def escape(unescaped_string):
    """
    Escape string (replace .:& with -)
    :param unescaped_string: str source string
    :return: str escaped string
    """
    return unescaped_string.replace('.', '-').replace(':', '-').replace('&', '-')


class TemporaryFolder:
    """
    Temporary folder representation with context manager (temp. directory deletes of context exit)
    """

    def __init__(self, *args, **kwargs):
        """
        Build temp. folder representation using tempfile.mkdtemp
        :param args: tuple tempfile.mkdtemp args
        :param kwargs: dict tempfile.mkdtemp kwargs
        """
        self._path = tempfile.mkdtemp(*args, **kwargs)

    @property
    def path(self):
        """
        Get path to temp. folder
        :return: str path
        """
        return self._path

    def remove(self):
        """
        Try to remove temporary folder (without exceptions)
        :return: None
        """
        try:
            for root, dirs, files in os.walk(self.path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        finally:
            pass

    def __enter__(self):
        """
        Return self on context enter
        :return: TemporaryFolder
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Call remove on context exit
        :param type: -
        :param value: -
        :param traceback: -
        :return: None
        """
        self.remove()


class Colors:
    """
    Terminal colors
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
