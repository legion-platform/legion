#
#    Copyright 2018 IQVIA. All Rights Reserved.
#
"""S3 task handler wrapper."""
from airflow import configuration as conf
from airflow.utils.log.s3_task_handler import S3TaskHandler


class S3TaskHandlerWithIAM(S3TaskHandler):
    """
    S3TaskHandler with legion S3 hook which supports AWS IAM authentication.
    """

    def _build_hook(self):
        remote_conn_id = conf.conf.get('core', 'REMOTE_LOG_CONN_ID')
        try:
            from legion_airflow.hooks.s3_hook import S3Hook
            return S3Hook(remote_conn_id)
        except Exception as e:
            self.log.error(
                'Could not create an S3Hook with connection id "%s". '
                'Please make sure that airflow[s3] is installed and '
                'the S3 connection exists.', remote_conn_id
            )
            raise
