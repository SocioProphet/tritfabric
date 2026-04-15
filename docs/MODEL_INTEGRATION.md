# Model Integration Framework (Classification → Decomposition → Rewiring)

This doc is the operational “how we integrate new models without turning TritFabric into duct tape”.

The guiding principle:
**Contracts, gates, and observability must be stronger than any one model/framework.**

---

## 0) Inputs and outputs we standardize

### Inputs we must know (minimum)
- task: classification / detection / segmentation / generation / embedding / ASR / RL / graph / doc-AI
- family: resnet / bert / retinanet / deeplab / diffusion / rllib-ppo / etc.
- dataset: URI + hash + license
- metric: name + direction (max/min)
- compute constraints: FLOPs/params ceilings, memory caps, latency SLO

### Outputs we must produce (minimum)
- `artifacts/<job_id>/model_card.json`
- `artifacts/<job_id>/ledger.json` (math + shapes + costs)
- optional `artifacts/<job_id>/onnx_check.json`
- optional `artifacts/<job_id>/model.onnx`
- promotion report (pass/fail + reasons)

---

## 1) Classification (what is it?)
We classify a new model by:
- **task** (what it does),
- **contract** (input/output schema),
- **dominant risks** (privacy, safety, robustness),
- **runtime target** (native vs ONNX).

This classification determines:
- which gates apply,
- which dashboards matter,
- which CI smoke tests we require.

---

## 2) Decomposition (what is it made of?)
We decompose the model into reusable “cells/blocks” that we can reason about:

Examples:
- CV: stem → backbone → FPN → heads
- NLP: embeddings → encoder blocks → pooling/head
- Diffusion: U-Net blocks → scheduler → sampler
- RL: encoder → policy head → value head

For each block we capture:
- tensor shapes + dtypes,
- parameter counts,
- major operations (attention, conv, matmul),
- expected invariants (e.g., logits shape, mask behavior).

These flow into the **ledger**.

---

## 3) Rewiring (how do we adapt it safely?)
Rewiring is where we:
- add PEFT (LoRA / IA³ / adapters),
- add regularizers (DropPath / DropBlock / label smoothing),
- add distillation (KD temperature schedule),
- add export hooks (ONNX dynamic axes templates),
- add observability (per-block timings, memory, activations).

The goal is not “more features”.
The goal is “same contract, measurable improvements, and reversible rollout”.

---

## 4) Minimal integration checklist (fail-closed)

### Contract
- [ ] IRSpec exists (even if simple)
- [ ] dataset URIs + hashes are recorded
- [ ] metric is named and direction declared

### Gates
- [ ] SHACL shapes validate model card (or fail promotion)
- [ ] ONNX export works (if onnx.enabled)
- [ ] ONNX cosine check passes threshold (if runtime_check enabled)
- [ ] eval delta is within allowed regression

### Ops
- [ ] SLO defined (p95 latency, error ratio)
- [ ] canary rollout configured (Rollouts analysis)
- [ ] dashboards imported (Grafana)

---

## 5) Recommended workflow

1) Start with a tiny shard dataset (fast iteration).
2) Train 1–3 configs, export ONNX, run cosine check.
3) Add CI smoke test that runs the pipeline end-to-end.
4) Only then expand hyperparameter grids.
5) Promote only through gates (no manual backdoors).
6) Roll out via canary with SLO + gates.

---

## 6) Where to add things in this repo

- Training glue: `slate/`
- Gates and registry: `atlas/registry.py`, `atlas/autopilot/`
- Proto/API: `api/atlas/v1/atlas.proto`
- Dashboards: `grafana/`
- GitOps: `deploy/`
