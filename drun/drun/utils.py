import socket


def detect_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    addr = s.getsockname()[0]
    s.close()
    return addr


def escape(s):
    return s.replace('.', '-').replace(':', '-').replace('&', '-')
