# Design philosophy

## Axioms (the invariants)

1) Open, verifiable, self-hostable by default.
2) Seams over monoliths: contracts and envelopes first; engines are replaceable.
3) Evidence-first: meaningful actions must be observable and auditable.
4) Determinism over heroics: reproducible configs, provenance, and benchmarks win.
5) Minimal mandatory surface area: optional features exist, but the core stays lean.
6) Pluralism at the storage layer: we standardize translation surfaces, not one true model.
7) Human legibility is a requirement: every standard has worked examples and validation hooks.

## How philosophy becomes real

- Standards translate axioms into MUST/SHOULD/MAY requirements.
- ADRs record tradeoffs when axioms collide.
- Validation gates enforce the non-negotiables.
