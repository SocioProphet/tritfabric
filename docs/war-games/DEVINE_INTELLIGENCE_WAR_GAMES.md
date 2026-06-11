# Devine Intelligence War Games

**Status:** proposed — spec only. Nothing described here is implemented.
**Spelling note:** "Devine" is the proper name for this layer. It is not a typo of "Divine."

---

## 1. What Devine Intelligence War Games is

Devine Intelligence War Games is the defensive validation and agent-evaluation plane. It defines controlled exercises, grader outputs, witness-backed canonization, reputation records, and evidence-chain hardening.

It is not a model-training service. It consumes Atlas outputs and writes validation events back into the Cainpath mesh.

---

## 2. Boundary definition

| In scope | Out of scope |
|---|---|
| Controlled evaluation exercises | Model training (owned by atlasd) |
| Grader outputs as Atlas artifacts | Production inference (owned by atlasd serve plane) |
| Witness-backed canonization decisions | Self-canonization by automation |
| HPST (holographic proof / semantic tomography) reports | HPST implementation (future epic) |
| Reputation and accountability records | Reward economy implementation (future epic) |
| Evidence-chain promotion into Cainpath mesh | Mesh infrastructure (owned by cairnpath-mesh) |
| Agent performance measurement | Agent cognition or rewiring (out of scope entirely) |

---

## 3. The validation plane

Every War Games exercise produces:

1. **Exercise spec** — a declared, version-pinned challenge with input set, expected output contract, grading criteria, and policy scope.
2. **Agent run record** — what the agent actually did: inputs consumed, outputs produced, tool calls made, resources used.
3. **Grader output** — a structured pass/fail evaluation of the agent run against the exercise spec. This is an Atlas artifact with a model card.
4. **Witness record** — one or more independent grader outputs that corroborate or contest the primary grader. Claims become canonical only when a witness record exists.
5. **Canonization decision** — the promotion-gated decision that marks a claim as canonical. Requires: primary grader output, at least one witness record, policy gate pass, and Cainpath promotion.

---

## 4. Cainpath integration

Every War Games event emits a CairnStep. The exercise's CairnLine is the evidence trail for the canonization decision.

| War Games event | CairnStep opcode |
|---|---|
| Exercise submitted | STACK (intent) |
| Agent run started | STACK (trial) |
| Agent run completed | STACK (artifact) |
| Grader output produced | STACK (validation) |
| Witness record produced | STACK (validation) |
| Canonization gate checked | STACK (policy) |
| Claim canonized | PROMOTE |
| Contested result | DIVERGENCE |
| Re-evaluation requested | REPLAY |

---

## 5. What "canonical" means

A claim is canonical when:
- It is hash-bound to a specific grader output and witness record.
- The canonization decision passed the standard Atlas promotion gates.
- The CairnLine for the exercise is complete and replayable.
- The canonization decision is written into the Cairnlog.

A claim is not canonical merely because an agent produced it, a human agreed with it, or a model generated it with high confidence. Canonization requires promotion through the mesh.

---

## 6. Reputation and accountability records

Reputation records are Atlas artifacts. They are produced by aggregating canonization decisions over time and are themselves subject to the standard promotion gate. They cannot be self-issued by the agent being evaluated.

Accountability records capture deviations: cases where an agent's output was contested, a canonization was reversed, or a divergence was detected on replay. These are appended to the Cairnlog, never deleted.

---

## 7. HPST (placeholder)

HPST (Holographic Proof / Semantic Tomography) is a future tool for deep agent evaluation. It is out of scope for this planning phase. When it is scoped, it will be defined as:
- A distinct Atlas job type that produces a structured tomography report.
- An artifact that enters the Framework Catalog under the standard intake gate.
- A consumer of the existing War Games CairnLine — it does not own a separate evidence trail.

Do not implement HPST until the basic exercise/grader/witness/canonization pipeline exists.

---

## 8. Implementation order

1. Exercise spec schema (as an Atlas IR extension).
2. Agent run record schema.
3. Grader output as an Atlas artifact with model card.
4. Witness record schema and canonization decision gate.
5. CairnLine emission for the above.
6. Reputation and accountability records.
7. HPST (separate epic, after 1–6 are stable).

Do not begin any step until the previous step is promoted through the Atlas pipeline.
