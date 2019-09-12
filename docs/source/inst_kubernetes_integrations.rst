===========================
Integration with Kubernetes
===========================



Kubernetes Ingress Controller
-----------------------------

Kubernetes ingress controller is required to publish web services (such as :term:`EDI`) to internet / extranet depending of installation case.


TLS certificates for Kubernetes Ingress controller
--------------------------------------------------

You may use your own issued TLS certificates (they have to be copied on a cluster as Kubernetes secrets) or use tools line Let’s Encrypt's Certbot that generates certificates for your deployment on the fly.


Authentication provider
-----------------------

For limiting access to legion WEB services (such as EDI) you may use authentication gateways.

Legion supports `oauth2_proxy <https://github.com/bitly/oauth2_proxy>`_ gateway, that could be easily integrated (through `CoreOS Dex <https://github.com/dexidp/dex>`_) with next authentication provides:

- LDAP

- SAML

- OAuth2 / OpenID – with some limitations


Kubernetes cluster autoscaling facilities
-----------------------------------------

Auto scaling ability can be added to Legion using any Kubernetes auto scaler due the fact that Legion uses native Kubernetes object for training and deployment purposes.

Usage of autoscalers, provided by cloud providers also is possible (GKE auto scaler and etc.)

.. todo::

    Add information how does Operator interacts with auto scaling (labels and etc)
