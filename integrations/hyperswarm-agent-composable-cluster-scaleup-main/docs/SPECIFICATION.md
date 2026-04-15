# HyperSwarm Agent Composable Cluster Scale-Up — Specification

## Overview
This repository defines a **scale-up wrapper** that pins and fetches upstream cluster toolchains
into `third_party/` for reproducible consumption by other SocioProphet integrations. It does **not**
ship upstream sources in git; instead it provides a deterministic fetch mechanism and metadata that
binds the wrapper to the larger SocioProphet ecosystem.

## Scope
**In-scope**
- Reproducible pinning of upstream cluster scale-up tooling.
- Fetching upstreams into a local `third_party/` directory for build/inspection.
- Validation of repository hygiene and pinned references.

**Out-of-scope**
- Executing any cluster provisioning or scale-up actions.
- Modifying upstream source code.
- Storing secrets, credentials, or deployment state.

## Capability Metadata
- **Capability ID:** `caps.infra.cluster-scaleup.hyperswarm@0.1.0`
- **Kind:** `infra.wrapper`
- **Status:** `experimental`
- **Primary metadata file:** `capd/hyperswarm.cluster-scaleup.capd.json`

## Artifacts
| Artifact | Location | Purpose |
| --- | --- | --- |
| Fetch script | `tools/fetch_upstreams.sh` | Clones or updates pinned upstream repositories. |
| Pinned refs | `tools/upstreams.env` | Single source of truth for upstream URLs and tags/commits. |
| Validation | `tools/validate.py` | Verifies required docs, gitignore rules, and pinned refs. |
| Upstream notes | `docs/UPSTREAMS.md` | Rationale for upstream choices and linkage references. |

## Upstreams (Pinned Dependencies)
All upstreams are pinned to tags or commits unless explicitly allowed otherwise.
`tools/validate.py` enforces this policy.

| Upstream | Source | Ref | Rationale |
| --- | --- | --- | --- |
| Kubespray | `https://github.com/kubernetes-sigs/kubespray.git` | `v2.29.1` | Stable release for Kubernetes cluster provisioning. |
| Krew | `https://github.com/kubernetes-sigs/krew.git` | `v0.4.5` | Stable kubectl plugin manager. |
| Fybrik / Mesh-for-Data | `https://github.com/IBM/the-mesh-for-data.git` | `v1.3.3` | Lineage reference for data mesh scale patterns. |
| Heroku buildpack apt | `https://github.com/heroku/heroku-buildpack-apt.git` | `master` | Legacy reference; no releases upstream. |

## Fetch Semantics
1. `tools/fetch_upstreams.sh` creates `third_party/` if missing.
2. Each upstream is cloned if missing, otherwise updated in place.
3. The script checks out the exact ref configured in `tools/upstreams.env`.
4. Success is logged per upstream and on completion.

**Determinism:**
- Determinism is achieved by pinning to tags/commits (except the explicitly allowed legacy
  reference) and by keeping the fetched output outside of git tracking.

**Idempotence:**
- Re-running the fetch script results in the same checked-out refs for each upstream.

## Validation and Guardrails
`tools/validate.py` enforces:
- Required documentation and scripts exist.
- `third_party/` is excluded from git tracking (`.gitignore`).
- Upstream refs are pinned (no floating refs except the allowlist).
- Core docs contain no placeholder ellipses.

## Interfaces
This wrapper exposes **two operator-facing entry points**:
- `make fetch`: fetches pinned upstreams into `third_party/`.
- `make validate`: validates repository requirements and pinning guarantees.

No programmatic API is exposed beyond these deterministic scripts.

## Storage and Data Handling
- **Data stored:** Only cloned upstream source code in `third_party/`.
- **Persistence:** Local filesystem only; not tracked in git.
- **Secrets:** Not stored or handled by this repository.
- **Retention:** `third_party/` can be deleted at any time and rehydrated via `make fetch`.

## Security and Compliance
- Upstreams are pinned to reduce supply-chain drift.
- No secrets or credentials are stored in-repo.
- The repository expects consumers to supply their own access controls and scanning
  policies for any usage of fetched upstreams.

## Failure Modes
| Failure | Symptom | Mitigation |
| --- | --- | --- |
| Missing upstream ref | `git checkout` fails in fetch script | Update `tools/upstreams.env` to a valid tag/commit. |
| Floating ref detected | `tools/validate.py` exits with error | Pin ref or explicitly allow in allowlist. |
| `third_party/` tracked | `tools/validate.py` exits with error | Ensure `.gitignore` includes `third_party/`. |
| Network outage | Fetch script fails | Retry when network access is restored. |

## Change Management
- Update `tools/upstreams.env` for any upstream version change.
- Update `docs/UPSTREAMS.md` with rationale for new pins.
- Run `make validate` before committing changes.

## Linkages (Truth Hierarchy)
- Platform integration target: `SocioProphet/prophet-platform`
- Workspace governance + cross-repo validation: `SocioProphet/sociosphere`
- Canonical protocol contracts: `SocioProphet/tritrpc`
- Storage/graph standards: `SocioProphet/socioprophet-standards-storage`

## Standards Alignment Notes
This specification is written to align with the SocioProphet storage standards by documenting
scope, data handling, artifacts, guardrails, security expectations, and operational interfaces.
Any deviations or unresolved gaps are tracked in `docs/STANDARDS_GAPS.md`.
