# TritFabric (Atlas OS Service) — unified runtime + gates + GitOps

This repository is the **fresh, consolidated “ONE” repo** that emerged from the TritFabricAI design/work:
a protocol-first AI runtime that can be embedded into **SourceOS** (opt-in only) while also feeding the
**SocioProphet** training/customization platform.

It includes:
- **Atlas OS Service** (Python): orchestration, registry, promotion gates, fairness scheduling (DRF), and a Serve router/autoscaler scaffold.
- **Protocol surface**: `api/atlas/v1/atlas.proto` (gRPC-first, REST-mirror friendly).
- **Promotion discipline**: SHACL + ONNX round-trip cosine + eval deltas (fail-closed by default).
- **Automation**:
  - GitHub Actions publish workflow (GHCR)
  - Dockerfiles for server / SSE gateway / tools job
  - ArgoCD AppSet + Rollouts canary + Workflows/Events placeholders
  - Image Updater + Gatekeeper policy packs (baseline hardening)
  - Vault/ExternalSecrets templates for keys and creds
- **Training-side scaffolds** (Slate): hooks and utilities used by Prophet-side experiments (kept optional here).
- **Integration snapshots** under `integrations/` (vendored copies of related repos you provided).

> **Opt-in principle**: SourceOS can ship with hooks for TritFabric, but **nothing activates** unless a user/admin explicitly opts in.
> See `docs/OPT_IN.md`.

---

## Quickstart (local)

### 1) Create a venv and install
```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
```

### 2) Run the daemon (HTTP + metrics)
```bash
. .venv/bin/activate
python -m cmd.atlasd.main --config configs/policy.yaml
# metrics: http://127.0.0.1:9108/metrics
```

### 3) Smoke-submit a job (HTTP)
```bash
python tools/smoke_submit.py
```

### 4) Generate protobuf stubs (optional)
This repo supports `buf`, but you can also use `grpc_tools.protoc`.

```bash
make proto
```

---

## Repo map

- `cmd/atlasd/` — daemon entrypoint and process wiring
- `api/` — protobuf API surface (gRPC-first)
- `atlas/` — core service code (policy, scheduler, registry, gates, RPC server scaffolds)
- `slate/` — training utilities + optional doc-AI pipeline scaffolds
- `deploy/` — GitOps manifests (ArgoCD, Rollouts, Gatekeeper, ExternalSecrets, Image Updater)
- `charts/` — Helm charts (optional alternative to Kustomize)
- `grafana/` — dashboards (starter pack)
- `tools/` — schema/context helpers, SHACL/ONNX validation helpers, smoke utilities
- `integrations/` — integration snapshots of related repos (see `integrations/README.md`)

---

## Where this belongs (org placement)

See `docs/ORG_PLACEMENT.md` for a concrete split plan between:
- **Socios-linux**: SourceOS integration, OS automation, hard opt-in wiring.
- **SocioProphet**: training/customization, standards, ontologies, evaluation harnesses.

---

## License

MIT (repo root). Vendored integration snapshots retain their own licenses under `integrations/*/LICENSE`.
