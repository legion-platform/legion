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

import boto3

import legion_test.utils


class S3:
    """
    AWS S3 client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    S3_LISTING_REQUEST_LIMIT = 1000
    WAIT_FILE_TIME = 10
    WAIT_FILE_ITERATIONS = 12

    def __init__(self):
        """
        Init client
        """
        self._bucket = None  # type: str
        self._client = boto3.client('s3')  # type: boto3.S3.Client

    def choose_bucket(self, bucket):
        """
        Choose S3 bucket

        :param bucket: bucket name
        :type bucket: str
        :return: None
        """
        self._bucket = bucket

    def _check_queryable(self):
        """
        Check that bucket has been selected

        :return: None
        """
        if not self._bucket:
            raise Exception('Bucket has not been selected')

    def list_buckets(self):
        """
        Get list of buckets

        :return: list[str] -- list of bucket names
        """
        response = self._client.list_buckets()
        return [item['name'] for item in response['Buckets']]

    def get_files_in_bucket(self, prefix=None, marker=None, limit=None):
        """
        Get bucket files

        :param prefix: filter prefix
        :type prefix: str
        :param marker: key to start listing
        :type marker: str
        :param limit: response keys limit
        :type limit: int
        :return: list[str] -- list of file names
        """
        self._check_queryable()

        kwargs = {}
        if marker:
            kwargs['Marker'] = marker
        if limit:
            kwargs['MaxKeys'] = int(limit)

        response = self._client.list_objects(Bucket=self._bucket,
                                             Prefix=prefix)
        if 'Contents' not in response:
            return []

        files = sorted((item for item in response['Contents']), key=lambda x: x['LastModified'])

        return [file['Key'] for file in files]

    def check_file_exists_in_bucket(self, file):
        """
        Check that file exists in bucket

        :param file: file path
        :type file: str
        :return: None
        """
        self._check_queryable()
        try:
            self._client.get_object(Bucket=self._bucket, Key=file)
        except self._client.exceptions.NoSuchKey:
            raise Exception('File {} not found in bucket {}'.format(file, self._bucket))

    def get_file_content_from_bucket(self, file):
        """
        Get file contents

        :param file: file path
        :type file: str
        :return: None
        """
        self._check_queryable()
        try:
            obj = self._client.get_object(Bucket=self._bucket, Key=file)
            return obj['Body'].read().decode('utf-8')
        except self._client.exceptions.NoSuchKey:
            raise Exception('File {} not found in bucket {}'.format(file, self._bucket))

    @staticmethod
    def join_bucket_paths(*items):
        """
        Build bucket path

        :param items: list[str] -- path items
        :return: str -- path
        """
        return '/'.join(item.strip('/ ') for item in items)

    @staticmethod
    def get_S3_paths_with_lag(*paths, **kwargs):
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
        lag_as_delta = datetime.timedelta(hours=lag_as_date.hour, minutes=lag_as_date.minute, seconds=lag_as_date.second)
        times = [
            datetime.datetime.utcnow(),
            datetime.datetime.utcnow() - lag_as_delta
        ]
        result = [
            particular_time.strftime(S3.join_bucket_paths(*paths))
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
        :param required_count: required count of lines (will be casted to int). \
                               If 0 - all lines from first scan will be returned
        :type required_count: str
        :param return_first_line: return only first line
        :type return_first_line: bool
        :return: dict -- return first line content if return_first_line else \
                         required lines in list[dict] format
        """
        required_count = int(required_count)

        def check_function():
            all_data = []
            for prefix in prefixes:
                print('Analyzing prefix {}'.format(prefix))
                all_files = self.get_files_in_bucket(prefix=prefix,
                                                    limit=self.S3_LISTING_REQUEST_LIMIT)
                for file in all_files:
                    print('Analyzing file {}'.format(file))
                    content = self.get_file_content_from_bucket(file)
                    for line in content.splitlines():
                        if needle_substring in line:
                            data = json.loads(line)
                            all_data.append(data)
                            if len(all_data) >= required_count and required_count != 0:
                                return all_data

            if len(all_data) > 0 and required_count == 0:
                return all_data

        result = legion_test.utils.wait_until(check_function,
                                              self.WAIT_FILE_TIME, self.WAIT_FILE_ITERATIONS)
        if not result:
            raise Exception('{} log line(s) with {!r} has not been found'.format(required_count, needle_substring))
        if return_first_line:
            return result[0]
        else:
            return result
