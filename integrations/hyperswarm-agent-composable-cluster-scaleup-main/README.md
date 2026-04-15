# HyperSwarm Agent Composable Cluster — Scale-Up Wrapper

This repository is a **SocioProphet integration wrapper** for cluster scale-up primitives.
It does **not** vendor third-party sources by default; instead it pins upstream versions
and fetches them into `third_party/` for reproducibility and license correctness.

## Truth hierarchy (linkages)
- Platform integration target: `SocioProphet/prophet-platform`
- Workspace governance + cross-repo validation: `SocioProphet/sociosphere`
- Canonical protocol contracts: `SocioProphet/tritrpc`
- Storage/graph standards: `SocioProphet/socioprophet-standards-storage`

## What gets fetched (pinned upstreams)
- kubespray (Kubernetes cluster provisioning)
- krew (kubectl plugin manager)
- heroku-buildpack-apt (legacy reference only; not required; no releases upstream)

## Documentation
- Specification: `docs/SPECIFICATION.md`
- Upstream rationale: `docs/UPSTREAMS.md`
- Standards gaps/issues: `docs/STANDARDS_GAPS.md`

## Quickstart
1) Fetch upstreams:
   - `make fetch`
2) Validate repo gates:
   - `make validate`

## Non-goals
- We do not ship secrets.
- We do not fork canonical specs here (triRPC remains canonical upstream).
