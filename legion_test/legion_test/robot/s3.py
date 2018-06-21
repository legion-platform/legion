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
import boto3


class S3:
    """
    AWS S3 client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

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

