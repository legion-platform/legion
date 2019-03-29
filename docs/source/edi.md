# EDI
EDI is a service which allows managing model inside Kubernetes.

Functionality:
* Deployment of a model image to a Kubernetes namespace.
* Undeployment of a model from a Kubernetes namespace.
* Scaling of a model pod in a Kubernetes namespace.
* Inspecting of models in an enclave.
* Generating JSON web token for access to your models.

Implementation details:
* Stateless python web server which uses Flask and uWSGI.
