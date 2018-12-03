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
"""S3 hook package."""
import smart_open
import json
import boto3

from airflow.exceptions import AirflowConfigException

from airflow import configuration as conf
from legion_airflow.hooks.k8s_base_hook import K8SBaseHook
from urllib.parse import urlparse


class S3Hook(K8SBaseHook):
    """S3 hook."""

    STOP_FILE_POSTFIX = '.STOP'
    STOP_FILE_NAME = 'STOP'

    def __init__(self, conn_id: str = None, *args, **kwargs):
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

        if conn_id is not None:
            self.connection = self.get_connection(conn_id)
            self.extras = self.connection.extra_dejson
            self.aws_access_key_id = self.extras.get('aws_access_key_id', None)
            self.aws_secret_access_key = self.extras.get('aws_secret_access_key', None)
        else:
            self.aws_access_key_id = None
            self.aws_secret_access_key = None

        try:
            self.s3_root_path = conf.get('core', 's3_root_path')
        except AirflowConfigException:
            self.s3_root_path = ''
        if self.s3_root_path.startswith('s3://'):
            self.s3_root_path = self.s3_root_path[5:]

    def _get_uri(self, bucket, key):
        """
        Create an URI based on passed bucket, key and Airflow configuration.
        :param bucket: S3 folder
        :param key: Path inside S3 bucket (
            if key is a full path it is simply returned)
        :return: URI, that contains protocol, bucket, path, e.g. s3://bucket/k1/k2/k3_file
        """
        if key.startswith('s3://'):
            return key
        path = [self.s3_root_path or bucket, key]
        return 's3://' + '/'.join(name.strip('/') for name in path)

    @staticmethod
    def _parse_s3_url(s3url):
        """
        Parse any passed s3url into bucket and key pair
        :param s3url: s3 storage absolute path
        :return: tuple (bucket, key)
        """
        parsed_url = urlparse(s3url)
        bucket_name = parsed_url.netloc
        key = parsed_url.path.strip('/')
        return bucket_name, key

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
        uri = self._get_uri(bucket, key)
        self.logger.info('Opening file "{}" with "{}" mode'.format(uri, mode))
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

    def write_csv_file(self, bucket: str, key: str, encoding: str = 'utf-8', splitter: str = ',',
                       quote: str = '"', columns_number: int = 0):
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
        :param columns_number: number of columns for validation
        :type columns_number: int
        :return: :py:class:`CsvWriter` -- csv reader
        """
        return CsvWriter(self.open_file(bucket, key, 'w', encoding), column_splitter=splitter, quote=quote,
                         columns_number=columns_number)

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
            uri = self._get_uri(bucket, key)
            self.logger.info('Checking if "{}" exists'.format(uri))
            smart_open.smart_open(uri,
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
        src_bucket, src_key = self._parse_s3_url(
            self._get_uri(src_bucket, src_key))
        dest_bucket, dest_key = self._parse_s3_url(
            self._get_uri(dest_bucket, dest_key))

        session = boto3.Session(profile_name=None,
                                aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key)
        s3 = session.resource(service_name='s3',
                              aws_access_key_id=self.aws_access_key_id,
                              aws_secret_access_key=self.aws_secret_access_key)
        bucket_from = s3.Bucket(src_bucket)
        bucket_to = s3.Bucket(dest_bucket)
        for obj in bucket_from.objects.filter():
            key_from = obj.key
            if key_from.startswith(src_key):
                source = {'Bucket': src_bucket, 'Key': key_from}
                key_to = key_from.replace(src_key, dest_key)
                dist_obj = bucket_to.Object(key_to)
                self.logger.info(
                    'Copying from {}:{} to {}:{}'.format(
                        src_bucket, key_from, dest_bucket, key_to
                    )
                )
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
            return self.read_row(row, self.column_splitter, self.quote)
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
    def read_row(row: str, column_splitter: str = ',', quote: str = '"'):
        """
        Read a CSV line char by char and convert it into list of cells.

        :param row: line in CSV format
        :type row: str
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        :return: list -- list of cells
        """
        cells = []
        cell = ''  # cell buffer
        for c in row.rstrip():
            if c == column_splitter and len(cell) >= 1 and cell[0] != quote:
                # found splitter in cell that is not framed with quotes
                cells.append(cell.replace(quote + quote, quote))
                # replaced middle double quotes with a single
                cell = ''
            elif c == column_splitter and len(cell) >= 2 and cell[0] == quote and cell[-1] == quote \
                    and cell.count(quote) % 2 == 0:
                # found splitter outside of cell framed with quotes
                # if number of found quotes is even, than current character is outside of quotes
                cell = cell[1:-1]
                cells.append(cell.replace(quote + quote, quote))
                # replaced middle double quotes with a single
                cell = ''
            elif c == column_splitter and len(cell) == 0:  # found empty cell
                cells.append(cell)  # add an empty cell
                cell = ''
            else:  # append found character to current cell buffer
                cell += c
        # row is read but something left in cell buffer
        if len(cell) >= 2 and cell[0] == quote and cell[-1] == quote:  # remove frame quotes
            cell = cell[1:-1]
        cells.append(cell.replace(quote + quote, quote))  # replaced middle double quotes with a single
        return cells


class CsvWriter(object):
    """CSV file writer."""

    EOL = '\r\n'

    def __init__(self, writer: object, column_splitter: str = ',', quote: str = '"', columns_number: int = 0):
        """
        Initialize CsvWriter.

        :param writer: data writer
        :type writer: object
        :param column_splitter: column splitter
        :type column_splitter: str
        :param quote: quote symbol
        :type quote: str
        :param columns_number: (Optional) a number of columns, that is used for input validation
        :type columns_number: int
        """
        self.writer = writer
        self.column_splitter = column_splitter
        self.quote = quote
        self.columns_number = columns_number

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
            if self.columns_number and len(cells) != self.columns_number:
                raise ValueError('Expected {} columns in input but got {}: {}'
                                 .format(self.columns_number, len(cells), ', '.join(cells)))
            else:
                self.writer.write(self.format_row(cells, self.column_splitter, self.quote) + self.EOL)

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
    def format_row(cells: list, column_splitter: str = ',', quote: str = '"'):
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
        cell_number = 0
        for cell in cells:
            if column_splitter in cell or quote in cell or '\n' in cell:  # if cell contains comma or quote
                cell = quote + cell.replace(quote, quote + quote) + quote  # wrap cell in quotes
            if cell_number > 0:
                row += column_splitter
            row += cell
            cell_number += 1
        return row
