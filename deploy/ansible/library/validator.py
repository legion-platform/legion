
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
#!/usr/bin/python3

DOCUMENTATION = '''
---
module: validator
short_description: Validate YAML-files 
'''

EXAMPLES = '''
- name: Validate Yaml-file
  validator:
    source: path/to/yaml
    template: path/to/template
'''


import os

import yaml
from ansible.module_utils.basic import AnsibleModule


def validate(f, temp, key=""):
    """
    Validate python dict using template

    :param f: file data
    :type f: dict
    :param temp:  template data
    :type temp: dict
    :param key: yaml-file key
    :type key: str
    :return: list of asent keys
    :rtype: list
    """


    absent_keys = []

    if isinstance(f, dict): # check source data to supported type (skip encryption info)
        for el in temp:
            value = temp[el]
            if not (el in f):
                absent_keys.append(key + "/" + str(el))
                continue
            if isinstance(value, list):
                for e in f[el]:
                    absent_keys.extend(validate(e, temp[el][0], key + "/" + el))
            elif isinstance(value, dict):
                absent_keys.extend(validate(f[el], temp[el], key + "/" + el))

    return absent_keys




def main():

    module = AnsibleModule(
        argument_spec=dict(
            source=dict(type='str', required=True),
            template=dict(type='str', required=True)
        ),
        supports_check_mode=True
    )

    if module.params['source'].endswith('yml'): # check if source is yaml or ansible dict
        for path in (module.params['source'], module.params['template']):
            if not os.path.exists(path):
                module.fail_json(msg="{} file doesn't exist".format(path))
            if not os.path.isfile(path):
                module.fail_json(msg="{} is directory".format(path))

        with open(module.params['source'], 'r') as stream:
            file = yaml.load(stream)


        with open(module.params['template'], 'r') as stream:
            template = yaml.load(stream)

        if not file:
            module.fail_json(msg="{} file is empty".format(module.params['source']))

    else:
        file = yaml.load(module.params['source'])

        with open(module.params['template'], 'r') as stream:
            template = yaml.load(stream)

    if not isinstance(file, dict):
        module.fail_json(msg="Can't load secrets file")

    data = validate(file, template)

    if data:
        path = module.params["source"] if "yml" in module.params["source"] else "secret"
        module.fail_json(msg="{} keys is missing in {} file".format(data, path))

    module.exit_json(msg="Validate successfull")

if __name__ == "__main__":
    main()