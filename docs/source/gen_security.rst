===================
Security
===================

Legion delegates user, token and credential management to third-party providers.

Any service that supports the OAuth2 protocol can be used to provide authentication and authorization to a Legion cluster.

.. warning::

    Connectivity from cluster to OAuth2 IP (identity provider) is required.

Legion integrations OAuth2 to Identity Providers using the ``oauth2_proxy`` library.

Securing model APIs
-----

:term:`Model prediction API` and :term:`Model Feedback API` calls are secured using :term:`JWT tokens <JWT Token>`.
:term:`EDI` services can issue a new :term:`JWT token` for a given :term:`role name <Model Deployment Access Role Name>`.
:term:`JWT tokens <JWT Token>` are scoped to specific :term:`role names <Model Deployment Access Role Name>` and may be used for granting access to the :term:`Model prediction API`.
The role name has to be defined during creation of :term:`model deployments <Deploy>`, otherwise a hard-coded default value will be used.

Securing management APIs
-----

When enabled in the Legion start-up configuration, all other endpoints (such as :term:`EDI`) are secured using :term:`JWT tokens <JWT Token>` and OAuth2 cookies.
When a user tries to open a secured resource, ``oauth2_proxy`` checks the incoming request for a :term:`JWT token<JWT Token>` and OAuth2 Cookies.
If a request does not contain appropriate credentials, the user will be redirected to a login URL.

Securing network connections, ingress and egress
-----
Legion does not ship with network policies enabled, but any policy that uses Pod label selection can be used (e.g. K8s NetworkPolicy). Details are in the Network Connectivity Reference.

.. todo::

    This document should be updated for Keycloak usage
