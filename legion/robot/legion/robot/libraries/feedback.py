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
"""
Robot test library - AWS S3
"""
import datetime
import json

from legion.robot.cloud import object_storage
from legion.robot.utils import wait_until


def join_bucket_paths(*items):
    """
    Build bucket path

    :param items: list[str] -- path items
    :return: str -- path
    """
    return '/'.join(item.strip('/ ') for item in items)


class Feedback:
    """
    AWS S3 client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    S3_LISTING_REQUEST_LIMIT = 1000
    WAIT_FILE_TIME = 10
    WAIT_FILE_ITERATIONS = 12

    def __init__(self, cloud_type, bucket, cluster_name):
        """
        Init client
        """
        self._client = object_storage.build_client(cloud_type, bucket, cluster_name)

    @staticmethod
    def get_paths_with_lag(*paths, **kwargs):
        """
        Get list of S3 locations from time-base pattern parts with possible lag.

        :param paths: list of patters that have to be joined
        :type paths: List[str]
        :param lag: (Optional) possible time lag (in HH:MM format). By default 01:00 - 1 hour
        :type lag: str
        :return: List[str] -- list of s3 patterns
        """
        lag = kwargs.get('lag', '01:00')
        lag_as_date = datetime.datetime.strptime(lag, '%H:%M')
        lag_as_delta = datetime.timedelta(hours=lag_as_date.hour, minutes=lag_as_date.minute,
                                          seconds=lag_as_date.second)
        times = [
            datetime.datetime.utcnow(),
            datetime.datetime.utcnow() - lag_as_delta
        ]
        result = [
            particular_time.strftime(join_bucket_paths(*paths))
            for particular_time in times
        ]
        return result

    def find_log_lines_with_content(self, prefixes, needle_substring, required_count, return_first_line):
        """
        Find line with content

        :param prefixes: s3 location prefixes
        :type prefixes: List[str]
        :param needle_substring: needle substring
        :type needle_substring: str
        :param required_count: required count of lines (will be casted to int).
                               If 0 - all lines from first scan will be returned
        :type required_count: str
        :param return_first_line: return only first line
        :type return_first_line: bool
        :return: dict -- return first line content if return_first_line else
                         required lines in list[dict] format
        """
        required_count = int(required_count)

        def check_function():
            all_data = []
            for prefix in prefixes:
                print('Analyzing prefix {}'.format(prefix))
                all_files = self._client.list_files(prefix=prefix,
                                                    limit=self.S3_LISTING_REQUEST_LIMIT)
                for file in all_files:
                    print('Analyzing file {}'.format(file))
                    content = self._client.read_file(file)
                    for line in content.splitlines():
                        if needle_substring in line:
                            data = json.loads(line)
                            all_data.append(data)
                            if len(all_data) >= required_count != 0:
                                return all_data

            if all_data and required_count == 0:
                return all_data

        result = wait_until(check_function, self.WAIT_FILE_TIME, self.WAIT_FILE_ITERATIONS)
        if not result:
            raise Exception('{} log line(s) with {!r} has not been found'.format(required_count, needle_substring))
        if return_first_line:
            return result[0]
        else:
            return result
