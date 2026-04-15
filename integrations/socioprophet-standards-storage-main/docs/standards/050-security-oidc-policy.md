# Security Standard: Identity, Authorization, and Policy

## Identity
- User and service identity SHOULD use OIDC/OAuth2.
- Service-to-service traffic SHOULD use mTLS when operating in a hostile or multi-tenant environment.

## Authorization
- Access decisions MUST be centralized in a policy service.
- Policy decisions MUST be logged as immutable audit events (PolicyEvaluated/AccessGranted/AccessDenied).

## Data minimization
- ChatOps outputs MUST support redaction and least-privilege views.

