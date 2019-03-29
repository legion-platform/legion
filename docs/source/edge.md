# EDGE
EDGE is a model API Gateway.

Functionality:
* Routing of traffic to your models.
* Monitoring of performance. It includes response time, model information and model endpoint name.
* Included Feedback API which captures all model request/responses and allows writing feedback to the AWS S3.
* Security. An edge checks a JSON web token before route an HTTP request to the models.

Implementation details:
* An edge pod consists of one container with two concurent processes:
  * Nginx server
  * Daemon process which updates Nginx config when you add or remove models and invokes SIGHUP signal to Nginx to [force configuration reload](http://nginx.org/en/docs/control.html#reconfiguration).
* FluentD daemon which writes model API requests/responses and feedback to the AWS S3.
* All monitoring, feedback and security logic are implemented using Lua.