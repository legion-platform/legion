import socket
import requests


class Utils:

    @staticmethod
    def check_domain_exists(domain):
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror as exception:
            if exception.errno == -2:
                raise Exception('Unknown domain name: {}'.format(domain))
            else:
                raise

    @staticmethod
    def check_remote_file_exists(url, login=None, password=None):
        credentials = None
        if login and password:
            credentials = login, password

        response = requests.get(url,
                                stream=True,
                                verify=False,
                                auth=credentials)
        if response.status_code >= 400 or response.status_code < 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        response.close()