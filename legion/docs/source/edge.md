# Edge

Is a Nginx server that routes all HTTP requests on system.

Edge server is used for models inspection and invocation via [Rest API](model_rest_api.md) .

For dynamically updating models routes uses *k8s-template* utility, that:
* receives details about Model Services from Kubernetes API;
* generates *nginx.conf* based on a template;
* reloads *Nginx* configuration
