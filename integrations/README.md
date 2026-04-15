# Integration snapshots

This directory contains **vendored snapshots** of related repositories you provided:

- `tritrpc-main` — TritRPC protocol and framing spec
- `sociosphere-main` — workspace / adapter harness and integration docs
- `prophet-platform-main` — Prophet platform skeleton (training/customization hub)
- `socioprophet-standards-storage-main` — storage standards and conventions
- `ontogenesis-main` — ontology / schema work
- `human-digital-twin-main` — consent + digital twin concepts
- `sourceos-a2a-mcp-bootstrap-main` — SourceOS bootstrap for A2A/MCP
- `hyperswarm-agent-composable-cluster-scaleup-main` — composable hyperswarm agent cluster

## Why these are here
They are included **only to keep this repo self-contained** for review and integration planning.

For long-term maintenance, we recommend converting these to:
- git submodules, or
- separate repos coordinated by a workspace manifest (sociosphere pattern), or
- released artifacts pinned by digest (preferred for SourceOS consumption).

Licenses and original READMEs are preserved within each snapshot.
