# EDGE

**This component will be replaced in version 1.0**

EDGE is a model API Gateway that is a intermediate point in contact with model.

Functionality:
* Routing of traffic to your models.
* Monitoring of performance. It includes response time, model information and model endpoint name. It shares performance metrics in a Prometheus-compatible way.
* [Feedback API](./gs_feedback_loop.md) which captures all model request/responses and allows writing feedback to the external storage.
* Security. An edge checks a JSON Web Token (JWT) before route an HTTP request to the models or to the feedback API endpoint.


Implementation details:
* An edge pod consists of one container with two concurent processes:
  * Nginx server
  * Daemon process which updates Nginx config when you add or remove models and invokes SIGHUP signal to Nginx to [force configuration reload](http://nginx.org/en/docs/control.html#reconfiguration).
* FluentD daemon which writes model API requests/responses and feedback to the external storage.
* All monitoring and security logic are implemented using Lua.