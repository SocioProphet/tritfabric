# Framework Catalog

**Status:** planned. The `catalog/` directory exists; this document defines the intake gate requirements.
**Rule:** No external method or framework enters the Atlas stack without a catalog entry. No catalog entry is accepted without a completed ADR.

---

## 1. What the Framework Catalog is

The Framework Catalog is the governed intake registry for external methods, optimizers, data loaders, eval harnesses, and adapters that Atlas jobs may use. It prevents the pattern where frameworks accumulate as duct tape: silently imported, undocumented, never evaluated, never removable.

Every catalog entry is a first-class artifact: it has a contract type, a scorecard, an ADR, defined promotion gates, and declared observability metrics. It is hash-bound and version-pinned.

---

## 2. Catalog entry requirements

An adapter may not be used in an Atlas job until all of the following exist:

### 2.1 Contract type

What the adapter provides, expressed in Atlas IR terms:
- Input/output interface (tensor shapes, dtypes, or graph node types).
- Side effects (file writes, network calls, process spawns).
- Resource requirements (GPU memory, CPU threads, storage).
- Failure modes: what it throws, what it leaves behind on failure.

### 2.2 Scorecard

| Field | Description |
|---|---|
| `quality_metrics` | Eval results on standard benchmarks relevant to this adapter's function |
| `known_failure_modes` | Documented failure cases, edge conditions, OOM behavior |
| `resource_profile` | Measured resource consumption under representative load |
| `version_pinned` | Exact version (semver or commit hash) this scorecard applies to |
| `eval_ref` | Content hash of the eval run that produced these metrics |
| `epistemic_level` | SCOPE-D label: proved / bounded / empirical / synthetic / speculative |

An adapter with `epistemic_level: speculative` may enter the catalog but is not promotion-eligible until it reaches at minimum `empirical`.

### 2.3 ADR

An architectural decision record explaining:
- Why this adapter was chosen over alternatives.
- What alternatives were considered and why they were not chosen.
- What the reversibility path is (can we remove it without cascading breakage?).
- What the upgrade path is.

ADRs live in `docs/adrs/`. One ADR per adapter adoption decision.

### 2.4 Promotion gates

Before an adapter can be used in a promoted Atlas artifact, it must pass:
- Content hash verification (adapter is pinned, not floating).
- Scorecard review (at minimum `empirical` epistemic level).
- ADR accepted (merged to main).
- Observability check: the adapter must emit at least one observable event.

### 2.5 Observability metrics

Every adapter must declare:
- What it emits (timing, error, resource utilization).
- Where it emits (which sink, which Cairnlog).
- Whether it emits anything silently (answer must be: no).

---

## 3. Catalog entry format

```yaml
# catalog/<adapter-name>/<version>/entry.yaml
adapter_id: <string>
version: <exact semver or commit hash>
contract_type: <Atlas IR reference>
scorecard_ref: <content hash of scorecard JSON>
adr_ref: <path to ADR in docs/adrs/>
epistemic_level: <proved | bounded | empirical | synthetic | speculative>
promotion_gate_status: <pending | ready | promoted>
observability:
  emits: [timing, error, ...]
  sink: <cairnlog line_id or local file ref>
  silent_emissions: none
```

---

## 4. Rejection rule

An adapter submitted without a completed ADR is rejected at the catalog gate. An adapter with an incomplete scorecard may enter as `speculative` but cannot advance to `promoted` until the scorecard is completed. An adapter with undeclared network egress is rejected unconditionally.

---

## 5. Current catalog state

No adapters are yet cataloged. The first adapter to enter should be the framework used for the toy training job in `docs/atlas/LOCAL_VERTICAL_SLICE.md`. That entry will serve as the template for all subsequent adapters.
