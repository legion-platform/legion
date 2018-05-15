# Legion Template Engine

Legion Template Engine is a command line interface for renreding Jinja2 templates based on File content or Enclaves details.
It watches for any changes in sources and regenerates output.

## Usage
```bash
usage: ltemplate [-h] [--command COMMAND] [--signal SIGNAL] [--pid PID]
                 [--pid-file PID_FILE]
                 template output

Template Renderer

positional arguments:
  template              Template file path
  output                Output file path

optional arguments:
  -h, --help            show this help message and exit
  --command COMMAND, -c COMMAND
                        Bash command to execute on render
  --signal SIGNAL, -s SIGNAL
                        Signal number to send to a PID on render
  --pid PID, -p PID     PID of a process to signal number on render
  --pid-file PID_FILE, -f PID_FILE
                        PID file of a process to signal number on render

```

## Template samples

### File watch module
File watch module is able to watch for any changes in a text or yaml file and recreate output on any change.
File watch module is located in **legion.io.render_on_file_change**.

#### Watch for YAML file
```
{{ load_module('legion.io.render_on_file_change', filepath='config.yml', is_yaml_file=True, var_name='cfg') }}
<ul>
{% for item in cfg:  %}
      <li>{{ item.hosts }}</li>
{% endfor %}
</ul>
```


#### Watch for Text file
```
{{ load_module('legion.io.render_on_file_change', filepath='data.log', var_name='log') }}
<pre>
{{ log }}
</pre>
```

### Enclaves watch module
Enclaves watch module is able to watch for any changes in an enclave and its models (via Kubernetes API) and recreate output on any change.
Enclaves watch module is located in **legion.containers.explorer.render_on_enclave_change**.

```
    {{ load_module('legion.containers.explorer.render_on_enclave_change') }}
    # Models API
    {% for model_name, service in enclave.models.items() %}
    location /api/model/{{ model_name }} {
        proxy_pass http://{{ service.metadata.name }}:5000;
    }
    {% endfor %}
```