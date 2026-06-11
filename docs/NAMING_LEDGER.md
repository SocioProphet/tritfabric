# Naming Ledger

**Status:** frozen as of 2026-06-11. All implementation must use these terms.
Any deviation is a naming drift event — open an ADR or update this ledger, do not let it accumulate silently.

---

## Frozen terms

| Term | Role | Canonical repo | Notes |
|---|---|---|---|
| **Cainpath** | Product/system name for the mesh pathing layer | `SocioProphet/cairnpath-mesh` | Acceptable in prose and UX |
| **Cairnpath** | Acceptable alias where prior docs use "cairn" vocabulary | `SocioProphet/cairnpath-mesh` | Prefer Cainpath in new code |
| **Cairn** | Primitive checkpoint/state object | `SocioProphet/cairnpath-mesh` | A single addressable state node |
| **CairnContext** | Initial traversal context (frontier, dataset, engine) | `SocioProphet/cairnpath-mesh` | `schemas/cairn/context.v0.jsonschema.json` |
| **CairnStep** | One hop in a traversal (opcode, in/out context, metrics) | `SocioProphet/cairnpath-mesh` | `schemas/cairn/step.v0.jsonschema.json` |
| **CairnLine** | Ordered path of checkpointed steps | `SocioProphet/cairnpath-mesh` | `schemas/cairn/line.v0.jsonschema.json` |
| **CairnResult** | Output state of a step (frontier, supporting refs) | `SocioProphet/cairnpath-mesh` | `schemas/cairn/result.v0.jsonschema.json` |
| **Cairnlog** | Append-only replay/evidence ledger over a CairnLine | `SocioProphet/cairnpath-mesh` | Not yet a separate schema; maps to CairnLine + immutable append |
| **Atlas** | Model composition, training, tuning, serving, artifact plane | `SocioProphet/tritfabric` | `atlas/` directory; atlasd daemon |
| **atlasd** | Local Atlas daemon (HTTP + gRPC, policy-gated) | `SocioProphet/tritfabric` | `cmd/atlasd/` |
| **TritFabric** | Governance / contracts / promotion fabric around Atlas | `SocioProphet/tritfabric` | This repo |
| **TritRPC / TriTRPC** | Deterministic, ternary-native RPC protocol | `SocioProphet/TriTRPC` | AEAD envelope; preferred wire |
| **Framework Catalog** | Registry of external method/framework adapters with scorecards and ADRs | `SocioProphet/tritfabric` | `catalog/` |
| **Calculus Contracts** | `math_type` + `calc_ops` model-card fields with SHACL/CI validation | `SocioProphet/tritfabric` | Declared per model artifact |
| **Devine Intelligence War Games** | Defensive validation, agent-evaluation, witness/canonization layer | `SocioProphet/tritfabric` | Spelled "Devine" (proper name); consumes Atlas outputs |
| **Network Atlas** | Model zoo taxonomy, composable IR, shape contracts, study recipes | `SocioProphet/tritfabric` | Layer 1 of the Atlas spine |
| **Zoo Slate** | Do not use. This was a transitional name for Network Atlas. | — | Deprecated |

---

## Drift already observed (audit record)

| Observed drift | Canonical replacement | First seen |
|---|---|---|
| "Zoo Slate" | Network Atlas | pre-2026 |
| "Divine Intelligence War Games" (capital D) | Devine Intelligence War Games | pre-2026 |
| "CairnPath" (capital P) | Cairnpath or CairnPath as class prefix only | pre-2026 |
| Atlas referred to as just "model-service stack" | Atlas = model composition + training + tuning + serving + artifact plane | pre-2026 |

---

## Rule for new terms

Before introducing a new term, check this ledger. If the concept does not exist here, open a PR adding it here before using it in code or docs. No name enters the codebase before it is ledgered.
