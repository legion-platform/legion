# Legionctl

LegionCTL (`legionctl`) is a command line interface for manipulating with models (external deployed, local deployed and building process).

## Basic

To read legionctl help you should use the following command:

```bash
legionctl --help
```

for a specific command, for example, inspect:

```bash
legionctl inspect --help
```

## Security

You should open edi url in a browser to get a token.

Then you can use it in a legionctl command, for example:

```bash
legionctl inspect --edi <edi-url> --token <your-token>
```

Another option save the token in config file. Further you can use legionctl commands without `edi` and
`token` parameters. For example:

```bash
legionctl login --edi <edi-url> --token <your-token>
legionctl inspect
```

## Model

To get json web model token for a model, you can use a command:
```bash
legionctl generate-token --edi <edi-url> --model-id <model-id> --model-version <model-version>
```

## Invoke models

You can invoke a model locally or remotely:
```bash
legionctl invoke --model-id 'test-summation' --model-version '1.0' --model-server-url 'https://edge-company-a.legion.org' -p a=1
```

You can pass model parameters as key-value `-p a=1` or json structure `--json {"a": 1}`.
If you have both kind of parameters that they will be merged. The key-value parameter has a higher priority.