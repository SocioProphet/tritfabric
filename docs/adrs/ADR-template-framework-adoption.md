# ADR: Framework adoption template

## Status

Proposed | Accepted | Rejected | Superseded

## Framework

- Framework id:
- Framework name:
- Catalog entry:
- Scorecard:

## Context

Describe the recovered source, external framework, or internal adapter request. Include the exact reason this framework belongs in TritFabric rather than remaining catalog-only.

## Decision

State the adoption decision. Valid decision classes:

- catalog-only
- adapter-stub
- smoke-tested adapter
- validated adapter
- rejected
- superseded

## Scope

State the allowed adapter scope:

- training
- serving
- evaluation
- dataset
- conversion
- observability
- none

## Required gates

- License status:
- Provenance status:
- Tests required:
- Model-card status:
- Runtime safety status:
- Promotion gates:

## Claim boundary

State what this adoption does **not** claim. This section is mandatory.

## Rollback / retirement

Describe how this adapter is removed, superseded, or demoted if gates fail.

## Follow-on work

List concrete implementation tasks and tests.
