#
#    Copyright 2018 IQVIA. All Rights Reserved.
#
"""K8S Connections hook package."""
import os
import json

from airflow import LoggingMixin
from airflow.hooks.base_hook import BaseHook
from airflow.models import Connection

from legion.k8s import K8SSecretStorage


class K8SSecretHook(BaseHook):
    """Hook for looking connections/credentials in K8S first than Airflow."""\

    LOG = LoggingMixin().log
    CONNECTIONS_SECRET = 'airflow-connections'

    @classmethod
    def get_connection(cls, conn_id: str):
        """
        Return connection by connection id.

        :param conn_id: connection id
        :type conn_id: str
        :return: :py:class:`airflow.models.Connection` -- connection
        """
        namespace = os.environ.get('NAMESPACE')
        try:
            secret = K8SSecretStorage.retrive(storage_name=cls.CONNECTIONS_SECRET, k8s_namespace=namespace)
            if conn_id in secret.data:
                conn_data = secret.data.get(conn_id)
                if conn_data:
                    conn = json.loads(conn_data)
                    cls.LOG.info("Return connection {} from K8S secret {}".format(conn_id, cls.CONNECTIONS_SECRET))
                    return Connection(conn_id=conn['conn_id'], conn_type=conn['conn_type'], host=conn['host'],
                                      login=conn['login'], password=conn['password'], schema=conn['schema'],
                                      port=conn['port'], extra=conn['extra'])
            else:
                cls.LOG.info("{} not found in K8S secrets {}".format(conn_id, cls.CONNECTIONS_SECRET))
        except Exception as ex:
            cls.LOG.error("Can't read {} from K8S secret because of {}".format(conn_id, str(ex)))
        return super().get_connection(conn_id)
