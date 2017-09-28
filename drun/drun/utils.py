"""
DRun utils functional
"""

import socket


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
