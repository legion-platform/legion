===========================
Kubernetes
===========================

Ingress Controller
------------------

- Legion requires a Kubernetes ingress controller to publish web services (such as :term:`EDI`) to the internet/extranet
- TLS certificates must:
    - be configured as K8s `Secrets <https://kubernetes.io/docs/concepts/configuration/secret/>`_
    - be provided from a tool like `Certbot <https://certbot.eff.org/>`_ or `Vault <https://www.vaultproject.io/>`_ to generate certificates on-the-fly

Authentication provider
-----------------------

For limiting access to legion WEB services, you may use authentication gateways.

Legion supports the `oauth2_proxy <https://github.com/bitly/oauth2_proxy>`_ gateway.

To integrate the following authentication providers:

- LDAP
- SAML
- OAuth2 / OpenID – with some limitations

`Dex <https://github.com/dexidp/dex>`_ has been tested.


Auto-scaling
------------

Because Legion provides native K8s objects for Train and Deploy, it supports any K8s auto-scaler.

Any K8s-compliant auto-scaler, such as those provided by major cloud providers, works out of the box.

.. todo::

    Add information how does Operator interacts with auto scaling (labels and etc)
