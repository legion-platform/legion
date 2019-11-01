.. _edi-server-description:

===
EDI
===

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Technologies used", "GoLang"
    "Distribution representation", "Docker Image"
    "Source code location", "`legion/legion/operator <https://github.com/legion-platform/legion/tree/develop/legion/operator>`_"
    "Can be used w/o Legion Platform?", "Yes"
    "Does it connect to another services?", "Yes (Kubernetes API)"
    "Can be deployed locally?", "If local Kubernetes cluster is present"
    "Does it provide any interface?", "Yes (HTTP REST API)"


:term:`EDI` is a service which allows to manage Legion Platform entities such as:

- :term:`Connections <Connection>`
- :term:`Model Trainings <Model Training>` (including log retrieval)
- :term:`Model Packagings <Model Packaging>` (including log retrieval)
- :term:`Model Deploying <Model Deploying>` (including log and metrics retrieval, A/B testing configuration and etc.)

Also :term:`EDI` provides possibility to retrieve:

- :term:`Model Training Metrics`
- :term:`Model Training Tags`
- :term:`Model Prediction Metrics`

Things that :term:`EDI` **can not** do:

- Managing (installation / removal / configuration) of :term:`Toolchain Train Integrations <Toolchain Train Integration>`
- Managing (installation / removal / configuration) of :term:`Toolchain Packaging Integrations <Toolchain Packaging Integration>`
- Making :term:`predictions <prediction>`
- Gathering and providing :term:`prediction feedbacks <Prediction Feedback>`
- Managing (installation / removal / configuration) of :term:`Toolchain Train Integrations <Toolchain Train Integration>`

How to reach EDI in target cluster
----------------------------------

By default, :term:`EDI` service is available on URL ``edi.<cluster-name>``, where ``<cluster name>`` is target cluster's base URL (e.g. ``edi.my-cluster.lab.university.com``. But this address can be configured during Legion's HELM chart installation.

What URLs does it provide
-------------------------

All information about URLs that :term:`EDI` provides can be viewed using auto generated, interactive Swagger (OpenAPI) documentation web page, located at ``<edi-address>/swagger/index.html``. You can read all up-to-date documentation and invoke all methods (allowed for your account) right on this webpage.


Authentication and authorization
--------------------------------

:term:`EDI` analyzes incoming HTTP headers for JWT token, extracts client's scopes from this token and approves / declines incoming requests based on these (provided in JWT) scopes.


Details of realization
----------------------

:term:`EDI` is a HTTP REST API server, written using GoLang. For easily integration it provides swagger endpoint with up-to-date protocol information.