.. _edi-server-description:

===
EDI
===

:term:`EDI` is a service that manages Legion Platform entities.

- :term:`Connections <Connection>`
- :term:`Training Events <Train>`
- :term:`Packaging Events <Package>`
- :term:`Deploy Events <Deploy>`

:term:`EDI` can provide the following data, when queried:

- Model Train and Deploy logs
- Model :term:`Trainer Metrics`
- Model :term:`Trainer Tags`
- Model Prediction Metrics

Things that :term:`EDI` **can not** do:

- Manage (installation / removal / configuration) of :term:`Trainer <Trainer Extension>` or :term:`Packager Extensions <Packager Extension>`
- Return :term:`predictions <prediction>` for any model (they're deployed elsewhere!)
- Gather or provide :term:`Prediction Feedback`

How to reach EDI in the K8s cluster
----------------------------------

By default, the :term:`EDI` service is available on the calculated URL: ``edi.<cluster-name>``, where ``<cluster name>`` is the cluster's base URL (e.g. ``edi.my-cluster.lab.university.com``). This address can be configured during Legion's Helm chart installation.

EDI-provided URLs
--------------------------

All information about URLs that :term:`EDI` provides can be viewed using the auto-generated, interactive Swagger page. It is located at ``<edi-address>/swagger/index.html``. You can read all of the up-to-date documentation and invoke all methods (allowed for your account) right from this web page.

Authentication and authorization
--------------------------------

:term:`EDI` analyzes incoming HTTP headers for JWT token, extracts client's scopes from this token and approves / declines incoming requests based on these (provided in JWT) scopes.

.. _edi-server-auth:

.. todo:
    implement next piece

HOWTO authorize

Implementation details
----------------------

:term:`EDI` is a REST server, written in GoLang. For easy integration, it provides a Swagger endpoint with up-to-date protocol information.

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Technologies used", "GoLang"
    "Distribution representation", "Docker Image"
    "Source code location", "`legion/legion/operator <https://github.com/legion-platform/legion/tree/develop/legion/operator>`_"
    "Can be used w/o Legion Platform?", "Yes"
    "Does it connect to other services?", "Yes (Kubernetes API)"
    "Can it be deployed locally?", "If a local Kubernetes cluster is present"
    "Does it provide any interface?", "Yes (HTTP REST API)"
