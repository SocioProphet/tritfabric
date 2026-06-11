# Atlas Spine on Cainpath Mesh

**Status:** planning. This document describes the intended architecture. It distinguishes proposed, planned, and implemented state explicitly throughout.
**Non-claim:** No layer below is live unless explicitly marked `[IMPLEMENTED]`.

---

## 1. The five-layer spine

```
Atlas / TritFabric / Cainpath Spine
├── 1. Network Atlas          [PLANNED]
├── 2. atlasd                 [IMPLEMENTED — local daemon exists]
├── 3. Framework Catalog      [PLANNED — catalog/ directory exists, intake gates TBD]
├── 4. Calculus Contracts     [PLANNED — model card fields defined, SHACL gate not yet enforced]
└── 5. Devine Intelligence War Games  [PROPOSED — spec only]
```

---

## 2. Layer 1 — Network Atlas

**Status:** planned.

Network Atlas is the model zoo taxonomy and IR layer. It defines:
- A taxonomy of model families, architectures, and capability classes.
- A composable intermediate representation (IR) for model graphs.
- Shape contracts: input/output tensor shape declarations, dtype contracts.
- Study recipes: declarative training/eval configuration templates.

**What it is not:** a model serving router (that is Layer 2 / atlasd serve plane), a training runner (that is atlasd), or a catalog of external frameworks (that is Layer 3).

**Required before Layer 1 is implemented:**
- `docs/atlas/NETWORK_ATLAS_SPEC.md` defining taxonomy, IR schema, and shape contract format.
- At least one toy model entry validated against the IR schema.

---

## 3. Layer 2 — atlasd

**Status:** implemented (local daemon, HTTP + gRPC, policy-gated).

atlasd is the local Atlas daemon. It already provides:
- Training/tuning job submission and execution (local + Ray optional).
- Artifact registry: model cards, promotion ledgers.
- ONNX export and cosine round-trip check.
- Policy admission (fail-closed by default).
- Fairness scheduler (DRF).

**Gap:** atlasd does not currently emit CairnSteps. The Cainpath integration adds a Cairnlog sink to the job lifecycle — see `docs/cainpath/CAINPATH_MESH.md` for the full event mapping.

**Next concrete task for atlasd:**
- Add a `CairnLine` emitter to the job lifecycle.
- Every state transition listed in the Atlas → Cairn event table emits a signed CairnStep to the local Cairnlog.
- This is the minimal local proof defined in `docs/atlas/LOCAL_VERTICAL_SLICE.md`.

---

## 4. Layer 3 — Framework Catalog

**Status:** planned. `catalog/` directory exists.

The Framework Catalog is the intake gate for external methods and frameworks. Every external framework (optimizer, data loader, eval harness, etc.) that enters the Atlas stack must go through the catalog.

Catalog entry requirements (per adapter):
- **Contract type**: what the adapter provides, in terms of the Atlas IR.
- **Scorecard**: quality metrics, eval results, known failure modes.
- **ADR**: architectural decision record explaining why this adapter was chosen.
- **Promotion gates**: what must pass before the adapter is production-admitted.
- **Observability metrics**: what the adapter emits and where.

No adapter enters the stack without a catalog entry. No catalog entry is accepted without an ADR.

See `docs/catalog/FRAMEWORK_CATALOG.md` for the full intake gate specification.

---

## 5. Layer 4 — Calculus Contracts

**Status:** planned. Fields defined in model card spec; SHACL gate not yet enforced in CI.

Calculus Contracts give every model and adapter machine-auditable mathematical roots.

Required fields on every model card:
- `math_type`: the mathematical structure the model operates over (e.g., `euclidean_vector_space`, `riemannian_manifold`, `ternary_logic_space`).
- `calc_ops`: the specific operations used (e.g., `gradient_descent`, `attention_softmax`, `ternary_matmul`).

Enforcement:
- SHACL validation runs in CI against every model card before promotion.
- A model card without `math_type` and `calc_ops` fails the `calculus_checked` promotion gate.
- No vapor declarations: `math_type` must reference a defined type in the calculus type registry, not a free-form string.

See `docs/calculus/CALCULUS_CONTRACTS.md` for the type registry and SHACL shape.

---

## 6. Layer 5 — Devine Intelligence War Games

**Status:** proposed (spec only).

Devine Intelligence War Games is the defensive validation and agent-evaluation layer. It:
- Defines controlled exercises for agent evaluation.
- Produces grader outputs as Atlas artifacts.
- Implements witness-backed canonization: claims become canonical only through mesh promotion.
- Writes validation events back into the Cainpath mesh as CairnSteps.
- Maintains reputation and accountability records as promotion-gated Cairn artifacts.

What it is not:
- It does not own the model-training service (that is atlasd).
- It does not run production inference (that is atlasd serve plane).
- It does not self-canonize: all canonization requires promotion through standard Atlas gates.

See `docs/war-games/DEVINE_INTELLIGENCE_WAR_GAMES.md`.

---

## 7. Promotion state machine

Every Atlas artifact moves through this state machine. Each transition emits a CairnStep.

```
draft
→ planned
→ runnable
→ evaluated
→ export_checked
→ calculus_checked
→ policy_checked
→ promoted
→ served
→ monitored
→ retired
```

Promotion to `promoted` fails closed if any of these are absent from the CairnLine:

| Gate | CairnStep opcode | Required |
|---|---|---|
| `ledger_present` | STACK metadata | Always |
| `model_card_present` | STACK metadata | Always |
| `math_type_present` | STACK validation | Always |
| `calc_ops_present` | STACK validation | Always |
| `dataset_or_input_lineage_present` | STACK metadata | Always |
| `metric_gate_result_present` | STACK policy | Always |
| `onnx_check_present` | STACK validation | If exported |
| `policy_decision_present` | STACK policy | Always |

---

## 8. Non-goals for the planning phase

- Do not implement full Ray Serve, Grafana, K8s autoscaler, or distributed mesh.
- Do not import external frameworks before their catalog entries exist.
- Do not add octonion/symmetric-space/Noether kits to the critical path.
- Do not expand Devine Intelligence War Games beyond defensive validation spec.
- Do not implement HPST tomography or reward economy before the witness/canonization spec is accepted.
