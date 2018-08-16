{{ load_module('legion.template_plugins.file_change_monitor', filepath='yaml_file_test_values.tmp.yml', is_yaml=True, var_name='var') }}
# This is base line

This is data section, value is {{ var.data.key }}

This is list section:
{% for key, value in var.kv.items() %}
    - {{ key }}, value is {{ value.name }}
{% endfor %}