# Ecosystem: web, monorepo, docs, and automation

## Repos and roles

- Standards repos (governance): this repo + triRPC + policy/evidence specs.
- Shipping repos: socioprophet-web, prophet-cli, sociosphere (workspace orchestration).
- Docs repo: socioprophet-docs (canonical narrative + generated references).

## Monorepo strategy (thin monorepo)

- Apps + packages live together for refactors and shared tooling.
- Standards remain external and are consumed via pinned commits or release artifacts.
- Shared packages: SDK (triRPC client), UI kit, schema helpers, evidence emitter.

## Documentation automation

- Docs site vendors pinned standards markdown and generates reference pages from:
  - rpc/*.yaml
  - schemas/*
  - benchmarks/workloads/*.yaml
- Automation opens PRs; policy gates merges; evidence is emitted for every run.

## Reproducible milestones

M0: repo presentation + gates (philosophy + reading order + validator)
M1: docs repo builds and publishes
M2: web portal reads standards artifacts (static mode)
M3: SDK + reference service
M4: agentic DevSecOps PR bots (policy + evidence)
M5: benchmarks + dashboards
