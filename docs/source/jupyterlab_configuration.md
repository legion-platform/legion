# Jupyterlab

Legion provides the Jupyterlab plugin as part of the platform.

## Internal deployment

Every Legion deployment contains Jupyterlab instance.
Its URL is `https://jupyterlab.<root-domain>/`.

## Installation

For now, there is no way to install the plugin from pypy\npm.
You can use the prebuilt Docker image, which is located in [repository](https://hub.docker.com/r/legionplatformtest/jupyterlab/tags).

```bash
legionctl sandbox --image legion/jupyterlab:latest
./legion-activate.sh
```

To setup an instance of Jupyterlab, you can use an environment variables. Available configuration options:
* `DEFAULT_EDI_ENDPOINT` - preconfigured EDI endpoint, for example `http://edi.demo.ailifecycle.org`.
* `LEGIONCTL_OAUTH_AUTH_URL` - Keycloak authorization endpoint, for example `https://keycloak.company.org/auth/realms/master/protocol/openid-connect/auth` 
* `JUPYTER_REDIRECT_URL` - JupyterLab external URL.
* `LEGIONCTL_OAUTH_SCOPE` - Oauth2 scopes. Th default value is `openid profile email offline_access groups`.
* `LEGIONCTL_OAUTH_CLIENT_SECRET` - Oauth2 client secret
* `LEGIONCTL_OAUTH_CLIENT_ID` - Oauth client ID

To enable SSO, you should provide the following options:
* `LEGIONCTL_OAUTH_AUTH_URL`
* `JUPYTER_REDIRECT_URL`
* `LEGIONCTL_OAUTH_CLIENT_SECRET`
* `LEGIONCTL_OAUTH_CLIENT_ID`
