#!/usr/bin/env python
#
#    Copyright 2019 EPAM Systems
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
import argparse
from os import path

from requirementslib import Pipfile


def main(path_to_project: str) -> None:
    p: Pipfile = Pipfile.load(path_to_project)

    with open(path.join(path_to_project, 'requirements.txt'), 'w') as f:
        f.write("\n".join(req.line_instance.get_line() for req in p.requirements))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert python dependencies from Pipenv format '
                                                 'to requirements.')
    parser.add_argument('path', help='Path to python project')
    args = parser.parse_args()

    main(args.path)
