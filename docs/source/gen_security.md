# Security approaches

## Securing model APIs

Model API and Model Feedback calls are secured using JWT tokens (if it is enabled in start-up configuration). EDI services can be called to issue new JWT token. JWT tokens are scoped to specific model and may be used for granting granular access to Model's API.

## Securing management APIs

Other endpoints (such as EDI) are secured according configuration. Out of box Legion provides ability to use Oauth2 with CoreOS Dex. [See integrations](./gs_integrations.md).

## Securing network connections, ingresses and egresses
Legion is not shipped with network policies, but any policy that uses Pod label selection (like standard K8S NetworkPolicy) can be used. Details are in [Network Connectivity Reference](./ref_network_connectivity.md).