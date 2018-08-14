# Load values
{{ load_module('legion.template_plugins.file_change_monitor', filepath='/opt/config/values.yaml', is_yaml=True, var_name='cfg') }}

# Receive
<source>
  @type http
  port 80
</source>

# Processing rules
# docs: https://github.com/fluent/fluent-plugin-s3

{% for tag in cfg.specific %}
# Section for tag {{ tag }}
<match *>
  @type s3
  # Connection
  s3_bucket {{ cfg.common.bucket }}
  s3_region {{ cfg.common.region }}

  # Storing
  path {{ cfg.specific[tag].path }}
  time_slice_format {{ cfg.specific[tag].time_slice_format }}
  time_slice_wait {{ cfg.specific[tag].time_slice_wait }}
  s3_object_key_format {{ cfg.specific[tag].s3_object_key_format }}
  utc
  store_as {{ cfg.specific[tag].store_as }}

  # Buffering
  <buffer tag,time>
    @type file
    path {{ cfg.specific[tag].buffer_path }}
    timekey {{ cfg.specific[tag].timekey }}
    timekey_wait {{ cfg.specific[tag].timekey_wait }}
    timekey_use_utc true
  </buffer>
  <format>
    @type {{ cfg.specific[tag].format_type }}
  </format>
</match>
{% endfor %}

{% if cfg is defined %}
# Default
<match *>
  @type s3
  # Connection
  s3_bucket {{ cfg.common.bucket }}
  s3_region {{ cfg.common.region }}

  # Storing
  path {{ cfg.default.path }}
  time_slice_format {{ cfg.default.time_slice_format }}
  time_slice_wait {{ cfg.default.time_slice_wait }}
  s3_object_key_format {{ cfg.default.s3_object_key_format }}
  utc
  store_as {{ cfg.default.store_as }}

  # Buffering
  <buffer tag,time>
    @type file
    path {{ cfg.default.buffer_path }}
    timekey {{ cfg.default.timekey }}
    timekey_wait {{ cfg.default.timekey_wait }}
    timekey_use_utc true
  </buffer>
  <format>
    @type {{ cfg.default.format_type }}
  </format>
</match>
{% endif %}