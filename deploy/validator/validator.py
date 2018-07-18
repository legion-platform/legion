
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
YAML file validator
"""
import sys
import os

import argparse
import yaml

def validate(f, temp, key=""):
    """
    Validate python dict using template

    :param f: file data
    :type f: dict
    :param temp:  template data
    :type temp: dict
    :param key: yaml-file key
    :type key: str
    :return: list
    """

    absent_keys = []

    for el in temp:
        value = temp[el]
        if not value:
            if (f is None) or not (el in f):
                absent_keys.append(key + "/" + str(el))
        else:
            if isinstance(value, list):
                absent_keys.extend(validate(f[el][0], temp[el][0], key + "/" + el))
            else:
                absent_keys.extend(validate(f[el], temp[el], key + "/" + el))
    return absent_keys




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="YAML-file validator")
    parser.add_argument('file',
                        help='path to yaml-file',
                        type=str,
                        )
    parser.add_argument('template',
                        help='path to template',
                        type=str,
                        )
    args = parser.parse_args(sys.argv[1:])

    # Check files existing and type

    for path in (args.file, args.template):
        if not os.path.exists(path):
            raise Exception("{} file doesn't exists".format(path))
        if not os.path.isfile(path):
            raise Exception("{} isn't file".format(path))

    with open(args.file, 'r') as stream:
        file = yaml.load(stream)

    with open(args.template, 'r') as stream:
        template = yaml.load(stream)


    data = validate(file, template)

    if data:
        raise Exception("{} file doesn't have {} keys".format(args.file, data))

    print("Validate successful")