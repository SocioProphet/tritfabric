# ADR-0001: Atlas spine runs on Cainpath mesh

**Status:** accepted
**Date:** 2026-06-11
**Deciders:** Michael Heller

---

## Context

TritFabric / Atlas is a contract-first ML runtime with promotion gates, ONNX checks, model cards, and policy admission. It currently produces files, ledger records, and logs, but its job history is not replayable in a principled way: there is no ordered, hash-bound, divergence-detectable audit trail.

Cainpath mesh (`SocioProphet/cairnpath-mesh`) provides exactly this substrate: `CairnContext`, `CairnStep`, `CairnLine`, and `CairnResult` define a checkpointed, replayable, policy-bounded traversal path. The `CairnLine` is append-only and supports `RESTACK`, `REPLAY`, `BRANCH`, `DIVERGENCE`, and `PROMOTE` as first-class operations.

The question: should Atlas job history be modeled as a Cainpath CairnLine, or should Atlas maintain its own custom audit/ledger format?

---

## Decision

Atlas job transitions emit CairnSteps into a CairnLine. The Cainpath mesh is the evidence substrate for Atlas job history, promotion decisions, and replay guarantees.

Atlas does not own a separate custom audit log format. The Cairnlog is the single source of truth for "what happened, in order, with evidence."

---

## Rationale

1. **Avoid bespoke audit formats.** A custom Atlas ledger would duplicate what Cainpath already provides. Two competing evidence formats means two sources of truth.

2. **Promotion requires replay.** The existing Atlas promotion gates (SHACL, ONNX cosine, eval delta) are already fail-closed. Adding Cainpath gives them a replayable, deterministic substrate rather than point-in-time file checks.

3. **Cainpath already exists and is operational.** The schemas are in `SocioProphet/cairnpath-mesh`. Using them avoids inventing a new primitive.

4. **Divergence detection is free.** With CairnLine as the job history, `REPLAY` + `DIVERGENCE` detection requires no extra implementation — it is a property of the substrate.

5. **Cainpath bounds total work.** `O(hops × K)` under stable K. Atlas jobs are bounded traversals. The fit is structural.

---

## Consequences

- Every Atlas state transition must emit a CairnStep. This is a new requirement on atlasd's job lifecycle.
- The `calculus_checked` and `policy_gate_checked` steps in a CairnLine become the promotion evidence, replacing any ad-hoc log checks.
- Replay of an Atlas job requires a stable `dataset_ref` and signed steps. Atlas jobs must declare their inputs as content-addressed references.
- Cainpath schemas are a dependency of tritfabric. Changes to `cairnpath-mesh` schemas that are breaking require a tritfabric migration.

---

## Alternatives considered

**1. Keep a custom Atlas ledger format.**
Rejected: duplicates Cainpath, creates two sources of truth, no replay guarantee.

**2. Use an external observability tool (Grafana, OpenTelemetry) as the audit trail.**
Rejected: these are metric/trace tools, not evidence substrates. They do not provide deterministic replay, content-addressed artifact references, or promotion semantics.

**3. Use `SocioProphet/agentplane` as the evidence sink.**
Not rejected outright — agentplane is the right sink for the `AdmissionResult.evidenceRef` cross-reference (see Triune integration map). But agentplane is an evidence relay, not the primary audit trail. Cainpath is the primary trail; agentplane may be a downstream consumer.
