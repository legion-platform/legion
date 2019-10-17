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
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService
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


class AzureBlobStorage(ObjectStorage):
    """
    Azure Blob storage client
    """

    def __init__(self, container_name: str, cluster_name: str):
        """
        Init client
        """
        self._bb_client = self.create_azure_bb_service(cluster_name)
        self._container_name = container_name

    def list_files(self, prefix: str = None, limit: int = None) -> typing.List[str]:
        """
        Get bucket files

        :param prefix: filter prefix
        :param limit: response keys limit
        :return: list of file names
        """
        return list(self._bb_client.list_blob_names(
            self._container_name,
            prefix=prefix,
            num_results=limit,
        ))

    def read_file(self, file_name: str) -> str:
        """
        Get file content

        :param file_name: file path in bucket
        :return: file content
        """
        return self._bb_client.get_blob_to_bytes(
            self._container_name,
            file_name,
        ).content.decode('utf-8')

    @staticmethod
    def create_azure_bb_service(cluster_name: str) -> BlockBlobService:
        """
        Configure BlockBlobService client.
        We assume that:
          * storage account has "cluster" tag with cluster name value.
          * resource group the same as cluster name
        :param cluster_name: cluster name
        :return: BlockBlobService client
        """
        sm_client: StorageManagementClient = get_client_from_cli_profile(StorageManagementClient)

        for storage_account in sm_client.storage_accounts.list():
            if storage_account.tags.get('cluster') == cluster_name and storage_account.tags.get('purpose') == 'Legion models storage': # pylint: disable=line-too-long
                sa_name = storage_account.name
                break
        else:
            raise ValueError(f'Cannot find a storage account for the cluster {cluster_name} name')

        # We assume that resource group name the same as cluster name
        sa_keys = sm_client.storage_accounts.list_keys(resource_group_name=cluster_name, account_name=sa_name)
        if not sa_keys.keys:
            raise ValueError(
                f'Cannot find keys for the {sa_name} storage account in the {cluster_name} resource group')

        return BlockBlobService(
            account_name=sa_name,
            account_key=sa_keys.keys[0].value,
        )


def build_client(cloud_type: str, bucket: str, cluster_name: str) -> ObjectStorage:
    """
    Get file content

    :param cluster_name: cluster name
    :param cloud_type: aws or gcp
    :param bucket: bucket name
    :return: client for specific cloud
    """
    if cloud_type == "aws":
        return AWS_S3(bucket)
    elif cloud_type == "gcp":
        return GCP_CloudStorage(bucket)
    elif cloud_type == "azure":
        return AzureBlobStorage(bucket, cluster_name)
    else:
        raise ValueError('Cloud type parameter must be "gcp"", "aws" or "azure"')
