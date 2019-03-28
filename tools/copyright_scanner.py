#!/usr/bin/env python3
#
#    Copyright 2017 EPAM Systems
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
Copyright scanner
"""

import argparse
import os
import re
import typing

SEARCH_REGEX = re.compile(r'\s+(copyright[^\n]+)', re.IGNORECASE)


class Colors:
    """
    Terminal colors
    """

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_copyright_header(path: str) -> typing.Optional[str]:
    """
    Get copyright from file

    :param path: path to file
    :type path: str
    :return: str or None -- copyright
    """
    try:
        with open(path, 'r') as file:
            chunk = file.read(400)
            results = SEARCH_REGEX.search(chunk)

            if results.group(1):
                return results.group(1).strip()

            return None
    except Exception:
        return None


def scan(folder: str) -> typing.Dict[str, typing.Dict[str, typing.List[str]]]:
    """
    Scan folder for copyrights

    :param folder: path to folder
    :type folder: str
    :return: dict[copyright => dict[extension => list[file1, file2,...]]] -- information about files
    """
    scan_results = {}

    for root, dirs, files in os.walk(folder):

        for file in files:
            full_file_path = os.path.join(root, file)

            if (os.sep + '.git' + os.sep) in full_file_path:
                continue

            _, file_extension = os.path.splitext(full_file_path)
            copyright_header = get_copyright_header(full_file_path)

            if copyright_header not in scan_results:
                scan_results[copyright_header] = {}

            if file_extension not in scan_results[copyright_header]:
                scan_results[copyright_header][file_extension] = []

            scan_results[copyright_header][file_extension].append(full_file_path)

    return scan_results


def work(folder: str) -> None:
    """
    Scan folder for copyrights and output results

    :param folder: path to folder
    :type folder: str
    """
    if not os.path.exists(folder):
        print('Path not exists: %s' % folder)
        exit(1)

    if not os.path.isdir(folder):
        print('Path is not directory: %s' % folder)
        exit(2)

    results = scan(folder)

    for copyright_header, extension_and_files in results.items():
        print('%sCopyright: %s"%s"%s%s' % (Colors.HEADER, Colors.BOLD, copyright_header, Colors.ENDC, Colors.ENDC))

        for extension_, files in extension_and_files.items():
            extension = extension_ if len(extension_) > 0 else '-'
            print('\tEXT = %s%s%s' % (Colors.BOLD, extension, Colors.ENDC))

            for file in files:
                print('\t\t%s' % file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copyright scanner')
    parser.add_argument('path', type=str, help='path to directory')

    args = parser.parse_args()

    work(args.path)
