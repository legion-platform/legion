===================
Security approaches
===================

Legion platform does not manages users, tokens or other credentials by itself. Instead, it relies on OAuth2 IP (identity provider), that can be deployed anyware.


.. warning::

    Connectivity from cluster to OAuth2 IP (identity provider) is required.

How does it work
----------------

For integrating with OAuth2 IP Legion Platform uses product named ``oauth2_proxy``. ``oauth2_proxy`` is responsible for checking requests that are coming to Legion Platform to be signed and valid and handles authorization pipeline (redirection to OAuth2 IP and etc.) otherwise.


How does it check that request is valid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``oauth2_proxy`` analyzes incoming request for:

- Special HTTP Cookie, that ``oauth2_proxy`` sends to user after successfull authorization. It Cookie contains OAuth2 identity tokens (access and refresh) and user's scopes (groups, name, email and etc). This cookie is encrypted by ``oauth2_proxy`` and can not be read or changed by anyone without encryption key (that is only in ``oauth2_proxy`` configuration).

- JWT token, placed in Authorization header (e.g. ``Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR....``). This token contains time-limited access token (w/o refresh) and user's scopes (groups, name, email and etc). Is is not encrypted, but signatured with OAuth2 IP private key. Signing is required to be sure that this token has not been modified by anyone (otherwise, signature is invalid). This token is generated directly by OAuth2 IP and ``oauth2_proxy`` checks signature only.


Securing model APIs
-----

:term:`Model prediction API` and :term:`Model Feedback API` calls are secured using :term:`JWT tokens <JWT Token>` (if it is enabled in start-up configuration).
:term:`EDI` services can be called to issue new :term:`JWT token` for specific :term:`role name <Model Deployment Access Role Name>`.
:term:`JWT tokens <JWT Token>` are scoped to specific :term:`role name <Model Deployment Access Role Name>` and may be used for granting granular access to :term:`Model prediction API`.
Role name has to be defined during creation of :term:`model deployments <Model Deploying>`, otherwise default value will be used.

Securing management APIs
-----

Other endpoints (such as :term:`EDI`) are secured (if it is enabled in start-up configuration) using :term:`JWT tokens <JWT Token>` and OAuth2 cookies. 
When user tries to open secured resource, ``oauth2_proxy`` checks income requests for :term:`JWT tokens <JWT Token>` and OAuth2 Cookies. 
If request does not contain appropriate credentials, user will be redirected.

Securing network connections, ingresses and egresses
-----
Legion is not shipped with network policies, but any policy that uses Pod label selection (like standard K8S NetworkPolicy) can be used. Details are in Network Connectivity Reference.

.. todo::

    This document should be updated for Keycloak usage
