# Atlas Local Vertical Slice — Minimal Cainpath Proof

**Status:** planned. This document defines the first implementation target after the architecture docs are accepted.
**Non-claim:** Nothing described here is implemented yet.

---

## Objective

Produce a single runnable local proof that Atlas jobs emit Cainpath/Cairnlog events. This is the minimum viable integration — not a production system.

---

## Scope

```
atlasd local daemon
  ├── one toy training job (e.g. 2-layer MLP on synthetic data)
  ├── model card output (with math_type + calc_ops)
  ├── CairnLine event emission (all required steps)
  ├── Cairnlog written to local file
  ├── ONNX export + cosine check
  ├── artifact registry record
  └── promotion gate evaluation (fail-closed)
```

No Ray, no Kubernetes, no distributed mesh, no Grafana.

---

## Required CairnLine for this slice

The toy job must produce a CairnLine with at minimum these steps:

| Index | Atlas event | Opcode | Args |
|---|---|---|---|
| 0 | Job submitted | STACK | `{event: "job_submitted", job_id, config_hash}` |
| 1 | Config resolved | STACK | `{event: "config_resolved", resolved_config_hash}` |
| 2 | Training started | STACK | `{event: "trial_started", trial_id, epochs, lr}` |
| 3 | Training completed | STACK | `{event: "trial_completed", final_loss, final_acc}` |
| 4 | ONNX exported | STACK | `{event: "onnx_exported", artifact_hash}` |
| 5 | ONNX cosine checked | STACK | `{event: "onnx_cosine_checked", score, pass: true}` |
| 6 | Model card emitted | STACK | `{event: "model_card_emitted", card_ref, math_type, calc_ops}` |
| 7 | Calculus checked | STACK | `{event: "calculus_checked", shacl_result: pass}` |
| 8 | Policy gate checked | STACK | `{event: "policy_gate_checked", gate: "promotion_v0", result: pass}` |
| 9 | Promoted | PROMOTE | `{event: "promoted", line_id, canonical_ref}` |

---

## Acceptance criteria

- `atlasd` can run the toy job end-to-end locally.
- The Cairnlog file is written and contains all 10 steps.
- Each step is hash-bound (content hash of args).
- Model card includes `math_type` and `calc_ops`.
- SHACL validation passes on the model card.
- ONNX cosine check passes (score ≥ threshold).
- Promotion gate evaluates all required fields and passes.
- Replaying the CairnLine from step 0 produces identical output (determinism check).

---

## Out of scope

- Steering vectors or SAE features.
- Multi-GPU training.
- External framework adapters.
- Devine Intelligence War Games evaluation.
- Any network egress beyond localhost.
