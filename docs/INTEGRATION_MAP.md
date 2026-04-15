# Integration map (SourceOS ↔ TritFabric ↔ SocioProphet)

This document maps the repos you provided to functional roles and integration seams.

---

## Core runtime lane (SourceOS-facing)

### `tritfabric` (this repo)
- Atlas daemon: orchestration + registry + gates
- opt-in enforcement (deny by default)
- GitOps scaffolds for runtime deployment

### `sourceos-a2a-mcp-bootstrap-main`
- bootstrap patterns for A2A/MCP servers in SourceOS
- **Integration seam**: expose Atlas endpoints as an MCP tool server (opt-in gated)

### `hyperswarm-agent-composable-cluster-scaleup-main`
- P2P swarm composition and scaling patterns
- **Integration seam**: use Atlas as a “control plane sidecar” for local/edge job dispatch and artifact promotion

---

## Canonical contract lane (platform-facing)

### `tritrpc-main`
- message framing, truth hierarchy, and payload envelopes
- **Integration seam**:
  - Atlas API responses should be wrap-able in TritRPC TRUE/MID/FALSE envelopes
  - promotion gates should emit TritRPC status + proofs

### `ontogenesis-main`
- ontology / schema primitives
- **Integration seam**:
  - SHACL shapes and JSON-LD contexts should converge here as canonical sources

### `socioprophet-standards-storage-main`
- storage conventions for datasets, models, ledgers, and evaluation traces
- **Integration seam**:
  - artifacts emitted by Atlas should satisfy these conventions (pathing, metadata, hashes)

---

## Training/customization lane (Prophet-facing)

### `prophet-platform-main`
- training orchestration hub
- **Integration seam**:
  - Prophet uses Atlas as an execution backend (submit tune/train)
  - Prophet consumes artifacts for eval + selection
  - Prophet publishes promoted artifacts back to registry (or to model store)

### `human-digital-twin-main`
- consent and identity model
- **Integration seam**:
  - opt-in tokens and consent receipts for local execution
  - “who authorized this run?” becomes first-class metadata in ledgers/model cards

---

## Workspace & “glue”

### `sociosphere-main`
- adapter/workbench for coordinating multiple components
- **Integration seam**:
  - treat Atlas as a component in sociosphere workspace
  - unify adapter specs to call into Atlas + Prophet

---

## What we still need (explicit gaps)
- `global-devsecops-intelligence` (mentioned but not provided here):
  - add as an integration stub repo or include as a workspace component later
- a canonical “spec repo” for:
  - proto + JSON-LD + SHACL + invariants + conformance tests (recommended in SocioProphet)
