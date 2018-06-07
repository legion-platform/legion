{{ load_module('legion.template_plugins.file_change_monitor', filepath='yaml_file_test_values_first.tmp.yml', is_yaml=True, var_name='first') }}
{{ load_module('legion.template_plugins.file_change_monitor', filepath='yaml_file_test_values_second.tmp.yml', is_yaml=True, var_name='second') }}

First is {{ first.data.key }}
Second is {{ second.data.key }}