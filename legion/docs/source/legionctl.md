# Legionctl

`legionctl` is a command line tool that allows you to manage an edi service.

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