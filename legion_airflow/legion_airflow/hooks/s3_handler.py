#
#    Copyright 2018 EPAM Systems
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
            if remote_conn_id:
                return S3Hook(remote_conn_id)
            else:
                return S3Hook()
        except Exception:
            self.log.error(
                'Could not create an S3Hook with connection id "%s". '
                'Please make sure that airflow[s3] is installed and '
                'the S3 connection exists.', remote_conn_id
            )
            raise
