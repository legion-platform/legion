#!/usr/bin/env python3
"""
Validate HELM Chart schema
"""

import jsonschema
import yaml

schema = yaml.safe_load(open('schema.yaml'))
values = yaml.safe_load(open('values.yaml'))

jsonschema.validate(values, schema)
