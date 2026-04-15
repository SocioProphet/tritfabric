# Opt-in model (SourceOS integration)

The hard rule: **TritFabric must not be usable in SourceOS unless the user/admin opts in.**

This repo provides a reference opt-in model that works in both local and cluster settings.

---

## Threat model (why we do this)

Without opt-in, an “always-on” AI orchestration/runtime can:
- accidentally process sensitive local data,
- leak prompts/documents through misconfigured connectors,
- create user confusion (“why is this running?”),
- expand the attack surface (sockets, services, credentials).

So we default to:
- **no service** running,
- **no network listeners**,
- **no training jobs**,
- **no external connectors**.

---

## Control points

### 1) Packaging-level default
- Do not auto-enable systemd units.
- Do not open ports in firewalls.
- Ship configs with `opt_in_required: true`.

### 2) Runtime gating
Atlas/TritFabric should reject requests unless one of the following is true:
- `ATLAS_OPT_IN_REQUIRED=false` **and** the operator is root/admin (cluster mode),
- OR a valid opt-in token is provided (local user mode).

Reference:
- `configs/policy.yaml`:
  - `security.opt_in_required`
  - `security.opt_in_token_sha256`
- RPC/HTTP middleware checks:
  - header `X-Opt-In-Token`
  - or local UDS socket permissions (`/var/run/atlas.sock`)

### 3) Explicit UX / CLI acknowledgement
- SourceOS should surface an explicit “Enable TritFabric” step.
- The user must see what it does (data flows, ports, storage location).

---

## Suggested implementations

### Local workstation (best default)
- Bind Atlas to **Unix Domain Socket** only.
- Require:
  - file permissions (owner-only) + optional opt-in token.
- No TCP listeners unless explicitly enabled.

### Kubernetes / cluster
- Opt-in is implemented by:
  - namespace-level installation (nothing installed by default),
  - secrets provisioned by Vault/ExternalSecrets,
  - Gatekeeper policies preventing privileged pods or rogue images.

---

## Auditing

At minimum, record:
- who opted in (subject),
- when (timestamp),
- what was enabled (components, versions),
- where artifacts are stored.

Write to:
- local append-only log (SourceOS side),
- and/or platform audit sink (Prophet side).
