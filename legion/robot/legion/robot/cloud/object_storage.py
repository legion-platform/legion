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
Various Object Storage backends
"""

import abc
import typing

import boto3
from google.cloud import storage


class ObjectStorage(metaclass=abc.ABCMeta):
    """
    Base ObjectStorage
    """

    @abc.abstractmethod
    def list_files(self, prefix: str = None, limit: int = None) -> typing.List[str]:
        """
        Get bucket files

        :param prefix: filter prefix
        :param limit: response keys limit
        :return: list of file names
        """
        pass

    @abc.abstractmethod
    def read_file(self, file_name: str) -> str:
        """
        Get file content

        :param file_name: file path in bucket
        :return: file content
        """
        pass


class AWS_S3(ObjectStorage):
    """
    AWS S3 client
    """

    def __init__(self, bucket_name: str):
        """
        Init client
        """
        self._bucket_name = bucket_name
        self._client = boto3.client('s3')  # type: boto3.S3.Client

    def list_files(self, prefix=None, limit=None) -> typing.List[str]:
        """
        Get bucket files

        :param prefix: filter prefix
        :param limit: response keys limit
        :return: list of file names
        """
        kwargs = {}

        if limit:
            kwargs['MaxKeys'] = int(limit)

        response = self._client.list_objects(Bucket=self._bucket_name,
                                             Prefix=prefix)
        if 'Contents' not in response:
            return []

        files = sorted((item for item in response['Contents']), key=lambda x: x['LastModified'])

        return [file['Key'] for file in files]

    def read_file(self, file_name: str) -> str:
        """
        Get file content

        :param file_name: file path in bucket
        :return: file content
        """
        try:
            obj = self._client.get_object(Bucket=self._bucket_name, Key=file_name)
            return obj['Body'].read().decode('utf-8')
        except self._client.exceptions.NoSuchKey:
            raise Exception('File {} not found in bucket {}'.format(file_name, self._bucket_name))


class GCP_CloudStorage(ObjectStorage):
    """
    GCP Cloud Storage client
    """

    def __init__(self, bucket_name: str):
        """
        Init client
        """
        client = storage.Client()

        self._bucket = client.get_bucket(bucket_name)

    def list_files(self, prefix: str = None, limit: int = None) -> typing.List[str]:
        """
        Get bucket files

        :param prefix: filter prefix
        :param limit: response keys limit
        :return: list of file names
        """
        return list(map(lambda f: f.name, self._bucket.list_blobs(prefix=prefix, max_results=limit)))

    def read_file(self, file_name: str) -> str:
        """
        Get file content

        :param file_name: file path in bucket
        :return: file content
        """
        return self._bucket.get_blob(file_name).download_as_string().decode('utf-8')


def build_client(cloud_type: str, bucket: str) -> ObjectStorage:
    """
    Get file content

    :param cloud_type: aws or gcp
    :param bucket: bucket name
    :return: client for specific cloud
    """
    if cloud_type == "aws":
        return AWS_S3(bucket)
    elif cloud_type == "gcp":
        return GCP_CloudStorage(bucket)
    else:
        raise ValueError('Cloud type parameter must be "gcp"" or "aws"')
