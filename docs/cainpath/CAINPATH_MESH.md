# Cainpath Mesh

**Status:** planning. This document defines Cainpath mesh semantics for Atlas integration. It does not describe a live deployed system.
**Source schemas:** `SocioProphet/cairnpath-mesh` — treat those schemas as canonical. This doc explains how tritfabric consumes them.

---

## 1. What Cainpath mesh is

Cainpath mesh is the checkpoint, replay, and evidence substrate for Atlas and TritFabric.

Where a conventional ML pipeline produces files and logs, a Cainpath-aligned pipeline produces a **replayable path**: an ordered sequence of Cairn state nodes that can be replayed deterministically, divergence-detected, and promoted through policy gates with evidence.

The core invariant from `cairnpath_v0.md`:

```
After each hop:
1. candidates = EXPAND(frontier, args)
2. candidates = DEDUP(candidates)
3. candidates = RANK(candidates)
4. frontier   = CAP(candidates, K)
```

Total work is bounded: `O(hops × K)` under stable K.

---

## 2. Primitive objects

These are defined in `SocioProphet/cairnpath-mesh/schemas/cairn/`. Do not redefine them here.

| Object | Schema | Role |
|---|---|---|
| `CairnContext` | `context.v0.jsonschema.json` | Initial traversal state: engine, dataset_ref, frontier, seed_entities, constraints, bindings |
| `CairnStep` | `step.v0.jsonschema.json` | One transition: opcode, args, in_context_id → out_context_id, metrics |
| `CairnLine` | `line.v0.jsonschema.json` | Ordered path of steps: line_id, root_context_id, steps[], status, branch_of |
| `CairnResult` | `result.v0.jsonschema.json` | Output of a step: frontier, supporting_refs, equivalence_map, warnings |
| `CairnLimits` | `policy/cairn_limits.v0.jsonschema.json` | Policy bounds: max_hops, max_cap_k, allowed opcodes, materialization budget |

---

## 3. Operations

| Operation | Meaning |
|---|---|
| `STACK` | Append a new CairnStep to an active CairnLine |
| `RESTACK` | Edit a step's config and invalidate downstream steps |
| `REPLAY` | Re-execute a CairnLine from a given step with the same or new args |
| `BRANCH` | Fork a CairnLine at a step; produces a new line with `branch_of` reference |
| `PROMOTE` | Canonize a CairnLine result; requires all policy gates to pass |
| `DIVERGENCE` | Record that a REPLAY produced different output than the committed result |

---

## 4. Atlas event → CairnStep mapping

Every meaningful Atlas transition emits a CairnStep. The Atlas pipeline must not merely produce files — it must produce a replayable CairnLine.

| Atlas event | Opcode | CairnStep notes |
|---|---|---|
| Job submitted | `STACK` | intent cairn; args = job config ref |
| Config resolved | `STACK` | config cairn; args = resolved config hash |
| Training trial started | `STACK` | trial cairn; args = trial ID, hyperparams |
| Metric emitted | `STACK` | observation cairn; args = metric name, value, step |
| ONNX exported | `STACK` | artifact cairn; args = artifact content hash |
| ONNX cosine checked | `STACK` | validation cairn; args = cosine score, pass/fail |
| Model card emitted | `STACK` | metadata cairn; args = model card ref |
| Promotion gate checked | `STACK` | policy cairn; args = gate name, result |
| Promotion accepted | `PROMOTE` | canonical cairnmark; line status → `promoted` |
| Config edited | `RESTACK` | invalidates downstream steps |
| Downstream rerun | `REPLAY` | from the restacked step |
| Output changed from prior | `DIVERGENCE` | recorded explicitly, not silently dropped |
| Alternate model path | `BRANCH` | new CairnLine with `branch_of` |

---

## 5. Cairnlog (append-only audit trail)

A Cairnlog is a CairnLine whose steps are never deleted, only appended. It is the evidence trail for promotion and compliance.

Rules:
- Steps are immutable once written.
- `RESTACK` and `DIVERGENCE` are appended as new steps, not edits to prior steps.
- Every promotion decision cites the Cairnlog `line_id` and the specific step indices that satisfied each gate.

The Cairnlog is the single source of truth for "what happened, in order, with evidence."

---

## 6. Promotion requires a complete Cairnlog

A model artifact cannot be promoted unless its CairnLine contains steps for all of these:

```
job_submitted
config_resolved
trial_completed
onnx_exported         (if exported)
onnx_cosine_checked   (if exported)
model_card_emitted
calculus_checked      (math_type + calc_ops present and SHACL-valid)
policy_gate_checked
```

Missing any step → promotion fails closed.

---

## 7. Replay guarantee

A CairnLine is replayable if:
- `root_context_id.dataset_ref` is a stable, content-addressed snapshot.
- Each CairnStep is signed or hash-bound.
- No step's args reference mutable external state without a pinned ref.

Atlas jobs must satisfy the replay guarantee before a CairnLine can be promoted.

---

## 8. What this document does not cover

- Live Cainpath mesh topology or network routing — that belongs in `SocioProphet/cairnpath-mesh`.
- CairnLimits policy enforcement engine — that is a future atlasd gate.
- Cross-line federation or multi-agent CairnLine merging — out of scope for v0.

---

## Non-claims

- This document does not prove a live Cainpath mesh is running.
- No Atlas job currently emits CairnSteps. This is the planned integration, not the current state.
- The Cairnlog implementation is not yet built; this doc specifies its required behavior.
