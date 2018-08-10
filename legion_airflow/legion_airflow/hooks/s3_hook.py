#
#    Copyright 2018 IQVIA. All Rights Reserved.
#
"""S3 hook package."""
import smart_open
import json
import boto3

from airflow.exceptions import AirflowException, AirflowConfigException

from airflow import configuration as conf
from airflow.hooks.base_hook import BaseHook


class S3Hook(BaseHook):
    """S3 hook."""

    STOP_FILE_POSTFIX = '.STOP'
    STOP_FILE_NAME = 'STOP'

    def __init__(self, conn_id: str, *args, **kwargs):
        """
        Initialize S3Hook.

        :param conn_id: connection id
        :type conn_id: str
        :param args: command arguments with .namespace
        :type args: :py:class:`argparse.Namespace`
        :param kwargs: extra kwargs
        :type kwargs: dict
        """
        self.sf = None
        self.conn_id = conn_id
        self._args = args
        self._kwargs = kwargs
        # get the connection parameters
        self.connection = self.get_connection(conn_id)
        self.extras = self.connection.extra_dejson
        self.aws_access_key_id = self.extras.get('aws_access_key_id', None)
        self.aws_secret_access_key = self.extras.get('aws_secret_access_key', None)
        self.key_prefix = self.extras.get('key_prefix', '')
        try:
            self.bucket_prefix = self.extras['bucket_prefix']
        except KeyError:
            raise AirflowException('Connection provides no bucket_prefix')
        try:
            self.bucket_path = conf.get('core', 's3_bucket_path')
        except AirflowConfigException:
            self.bucket_path = ''

    def get_uri(self, bucket, key):
        if key.startswith('s3://'):
            key = key[5:]
        path = [
            self.bucket_prefix, bucket,
            self.key_prefix, self.bucket_path, key
        ]
        return 's3://' + '/'.join(name.strip('/') for name in path if name)

    def open_file(self, bucket: str, key: str, mode: str = 'rb', encoding: str = 'utf-8'):
        """
        Open file to read/write.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :param mode: mode
        :type mode: str
        :param encoding: encoding
        :type encoding: str
        :return: s3 file
        """
        self.check_if_maintenance(bucket, key)
        uri = self.get_uri(bucket, key)
        return smart_open.smart_open(uri=uri, mode=mode,
                                     encoding=encoding,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key)

    def read_csv_file(self, bucket: str, key: str, encoding: str = 'utf-8', splitter: str = ',', quote: str = '"'):
        """
        Return CsvReader to read a file.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :param encoding: encoding
        :type encoding: str
        :param splitter: column splitter
        :type splitter: str
        :param quote: quote symbol
        :type quote: str
        :return: :py:class:`CsvReader` -- csv reader
        """
        return CsvReader(self.open_file(bucket, key, 'r', encoding), column_splitter=splitter, quote=quote)

    def read_json_file(self, bucket: str, key: str, encoding: str = 'utf-8'):
        """
        Return data as json file.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :param encoding: encoding
        :type encoding: str
        :return: :py:class:`json` -- content in json format
        """
        return json.load(self.open_file(bucket, key, 'r', encoding))

    def write_csv_file(self, bucket: str, key: str, encoding: str = 'utf-8', splitter: str = ',', quote: str = '"'):
        """
        Return CsvWriter to write a file.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :param encoding: encoding
        :type encoding: str
        :param splitter: column splitter
        :type splitter: str
        :param quote: quote symbol
        :type quote: str
        :return: :py:class:`CsvWriter` -- csv reader
        """
        return CsvWriter(self.open_file(bucket, key, 'w', encoding), column_splitter=splitter, quote=quote)

    def write_json_file(self, obj: object, bucket: str, key: str, encoding: str = 'utf-8'):
        """
        Save data as json file.

        :param obj: object to write
        :type obj: object
        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :param encoding: encoding
        :type encoding: str
        """
        json.dump(obj, self.open_file(bucket, key, mode='w', encoding=encoding))

    def exists(self, bucket: str, key: str):
        """
        Check is bucket exists.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :return: bool -- True if file exist, False otherwise
        """
        try:
            smart_open.smart_open(self.get_uri(bucket, key),
                                  mode='rb',
                                  aws_access_key_id=self.aws_access_key_id,
                                  aws_secret_access_key=self.aws_secret_access_key).close()
            return True
        except Exception:
            return False

    def check_if_maintenance(self, bucket: str, key: str):
        """
        Check maintenance.

        :param bucket: bucket name
        :type bucket: str
        :param key: key name
        :type key: str
        :raise RuntimeError: if loading is terminated
        :return: None
        """
        if self.exists(bucket, self.STOP_FILE_NAME):
            raise RuntimeError('Loading is terminated, delete in s3 root "{}/{}" file to continue.'
                               .format(bucket, self.STOP_FILE_NAME))
        elif self.exists(bucket, key + self.STOP_FILE_POSTFIX):
            raise RuntimeError('Loading is terminated, delete "{}/{}" file in data folder to continue.'
                               .format(bucket, key + self.STOP_FILE_POSTFIX))

    def copy_folder(self, src_bucket: str, src_key: str, dest_bucket: str, dest_key: str):
        """
        Copy data from source to destination.

        :param src_bucket: source bucket name
        :type src_bucket: str
        :param src_key: source key name
        :type src_key: str
        :param dest_bucket: destination bucket name
        :type dest_bucket: str
        :param dest_key: destination key name
        :type dest_key: str
        :return: None
        """
        session = boto3.Session(profile_name=None,
                                aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key)
        s3 = session.resource(service_name='s3',
                              aws_access_key_id=self.aws_access_key_id,
                              aws_secret_access_key=self.aws_secret_access_key)
        bucket_from = s3.Bucket(self.bucket_prefix + src_bucket)
        bucket_to = s3.Bucket(self.bucket_prefix + dest_bucket)
        for obj in bucket_from.objects.filter():
            key_from = obj.key
            if key_from.startswith(self.key_prefix + self.bucket_path + src_key):
                source = {'Bucket': self.bucket_prefix + src_bucket, 'Key': key_from}
                key_to = key_from.replace(
                    self.key_prefix + self.bucket_path + src_key,
                    self.key_prefix + self.bucket_path + dest_key
                )
                dist_obj = bucket_to.Object(key_to)
                self.logger.info('Copying from {}:{} to {}:{}'
                                 .format(self.bucket_prefix + src_bucket, key_from, dest_bucket, key_to))
                dist_obj.copy(source)

    def load_file(self, filename, key, bucket_name=None, replace=False, encrypt=False):
        """
        Load a local file to S3

        :param filename: name of the file to load.
        :type filename: str
        :param key: S3 key that will point to the file
        :type key: str
        :param bucket_name: Name of the bucket in which to store the file
        :type bucket_name: str
        :param replace: A flag to decide whether or not to overwrite the key
            if it already exists. If replace is False and the key exists, an
            error will be raised.
        :type replace: bool
        :param encrypt: If True, the file will be encrypted on the server-side
            by S3 and will be stored in an encrypted form while at rest in S3.
        :type encrypt: bool
        """

        with self.open_file(bucket_name, key, 'w') as dist:
            with open(filename, 'r') as source:
                for line in source:
                    dist.write(line)

    def load_string(self, string_data, key, bucket_name=None, replace=False,
                    encrypt=False, encoding='utf-8'):
        """
        Load a string to S3

        This is provided as a convenience to drop a string in S3. It uses the
        boto infrastructure to ship a file to s3.

        :param string_data: string to set as content for the key.
        :type string_data: str
        :param key: S3 key that will point to the file
        :type key: str
        :param bucket_name: Name of the bucket in which to store the file
        :type bucket_name: str
        :param replace: A flag to decide whether or not to overwrite the key
            if it already exists
        :type replace: bool
        :param encrypt: If True, the file will be encrypted on the server-side
            by S3 and will be stored in an encrypted form while at rest in S3.
        :type encrypt: bool
        :param encoding: String encoding
        :type encoding: str
        """

        with self.open_file(bucket_name, key, 'w', encoding) as out:
            out.write(string_data)

    def get_key(self, key, bucket_name=None):
        """
        Check if Key exists

        :param key: the path to the key
        :type key: str
        :param bucket_name: the name of the bucket
        :type bucket_name: str
        """
        return self.read_key(key, bucket_name)

    def read_key(self, key, bucket_name=None):
        """
        Read a key from S3

        :param key: S3 key that will point to the file
        :type key: str
        :param bucket_name: Name of the bucket in which the file is stored
        :type bucket_name: str
        """

        if self.exists(bucket_name, key):
            with self.open_file(bucket_name, key, 'r', 'utf-8') as out:
                return out.read()
        else:
            return None


class CsvReader:
    """CSV file reader."""

    EOL = '\r\n'

    def __init__(self, reader: object, column_splitter: str = ',', quote: str = '"'):
        """
        Initialize CsvReader.

        :param reader: data reader
        :type reader: object
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        """
        self.reader = reader
        self.column_splitter = column_splitter
        self.quote = quote

    def __enter__(self):
        """
        Open reader and return self.

        :return: :py:class:`CsvReader` -- csv reader
        """
        self.reader.__enter__()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object):
        """
        Close reader.

        :param exc_type: type
        :type exc_type: object
        :param exc_val: value
        :type exc_val: object
        :param exc_tb: traceback
        :type exc_tb: object
        :return: None
        """
        self.reader.__exit__(exc_type, exc_val, exc_tb)

    def __iter__(self):
        """
        Return self.

        :return: :py:class:`CsvReader` -- csv reader
        """
        return self

    def __next__(self):
        """
        Return next row.

        :return: list -- data row
        """
        row = self.reader.__next__()
        while row.count(self.quote) % 2 == 1:
            row = row + '\n' + self.reader.__next__()
        if row is not None:
            return self._read_row(row, self.column_splitter, self.quote)
        else:
            return None

    def __getattr__(self, name: str):
        """
        Return attribute value by name.

        :param name: attribute name
        :type name: str
        :return: str -- attribute value
        """
        return getattr(self.reader, name)

    @staticmethod
    def _read_row(row: str, column_splitter: str = ',', quote: str = '"'):
        """
        Read and return row.

        :param row: row
        :type row: str
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        :return: list -- data row
        """
        cells = []
        cell = ''
        for c in row.rstrip():
            if ((c == column_splitter) and (
                    (len(cell) >= 1 and cell[0] != quote) or (len(cell) >= 2 and cell[0] == quote and cell[-1] == quote)
            )):
                if len(cell) >= 2 and cell[0] == quote and cell[-1] == quote:  # trim quotes
                    cell = cell[1:-1]
                cells.append(cell.replace(quote + quote, quote))  # replace double quotes to single quote
                cell = ''
            else:
                cell += c
        if len(cell) > 0:  # if cell is not empty
            if len(cell) >= 2 and cell[0] == quote and cell[-1] == quote:  # trim quotes
                cell = cell[1:-1]
            cells.append(cell.replace(quote + quote, quote))  # replace double quotes to single quote
        return cells


class CsvWriter(object):
    """CSV file writer."""

    EOL = '\r\n'

    def __init__(self, writer: object, column_splitter: str = ',', quote: str = '"'):
        """
        Initialize CsvWriter.

        :param writer: data writer
        :type writer: object
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        """
        self.writer = writer
        self.column_splitter = column_splitter
        self.quote = quote

    def __enter__(self):
        """
        Open writer and return self.

        :return: :py:class:`CsvWriter` -- csv writer
        """
        self.writer.__enter__()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object):
        """
        Close writer.

        :param exc_type: type
        :type exc_type: object
        :param exc_val: value
        :type exc_val: object
        :param exc_tb: traceback
        :type exc_tb: object
        :return: object -- close result
        """
        return self.writer.__exit__(exc_type, exc_val, exc_tb)

    def write_csv(self, cells: list):
        """
        Write csv data.

        :param cells: data to write
        :type cells: list
        :return: None
        """
        if cells is not None:
            self.writer.write(self._format_row(cells, self.column_splitter, self.quote) + self.EOL)

    def __getattr__(self, name: str):
        """
        Return attribute value by name.

        :param name: attribute name
        :type name: str
        :return: str -- attribute value
        """
        return getattr(self.writer, name)

    def get_total_bytes(self):
        """
        Return total bytes written.

        :return: int -- written bytes count
        """
        if hasattr(self.writer, '_total_bytes'):
            return self.writer._total_bytes
        else:
            return 0

    @staticmethod
    def _format_row(cells: list, column_splitter: str = ',', quote: str = '"'):
        """
        Format row.

        :param cells: list data
        :type cells: list
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        :return: str -- formatted row
        """
        row = ''
        for cell in cells:
            if column_splitter in cell or quote in cell or '\n' in cell:  # if cell contains comma or quote
                protected_cell = quote + cell.replace(quote, quote + quote) + quote  # wrap cell in quotes
                if row != '':
                    row += column_splitter
                row += protected_cell
            else:
                if row != '':
                    row += column_splitter
                row += cell
        return row
