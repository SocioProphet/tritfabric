# Recovered knowledge framework executable map

## Status

This file records the first executable integration tranche for the recovered Atlas/TritFabric knowledge-framework chat archive.

This is not a prose-only capture. The tranche lands machine-readable contracts and validation surfaces first:

- community learning schemas,
- JSON-LD contexts,
- SHACL shape files,
- valid/invalid fixtures,
- a lightweight repository validator,
- and pytest coverage for the recovered framework contracts.

## Source archive grouping

The recovered material was triaged into these source groups:

1. Composite TritFabric/Atlas archive: model catalog, community learning, Noetherian layer contracts, quantum/symmetric layer notes.
2. Model Zoo / Network Atlas raw catalog corpus.
3. Network Atlas wiring and Atlas OS service bridge.
4. Atlas OS service implementation tranche.
5. Serve plane, observability, and Beam/Airflow/Kafka consolidation.
6. A2A ontology, JSON-LD/SHACL promotion, TritRPC promotion discipline, calculus contracts, framework governance, and Hopf/Tenfold knowledge framework.
7. Clean Community Learning Plane extraction.

## First executable tranche

This PR begins with the least ambiguous contracts:

- `community/schemas/*.avsc` defines Avro-compatible community learning records.
- `api/jsonld/community_context.jsonld` and `api/jsonld/math_context.jsonld` define semantic terms used by community and model-card payloads.
- `api/shapes/community_shapes.ttl` and `api/shapes/model_shapes.ttl` define SHACL gates for consent, provenance, math type, calculus operations, and promotion evidence.
- `community/fixtures/*` gives a positive and negative fixture for the HF event boundary.
- `tools/validate_recovered_framework_contracts.py` validates the landed contracts without requiring optional runtime services.

## Claim boundary

This tranche does not claim that the recovered chat artifacts were already merged, shipped, or operational in production. It turns recovered design work into repo-owned contracts that can be tested, promoted, and evolved under TritFabric governance.

## Follow-on executable tranches

1. Add JSON-LD model-card emitters and SHACL validation around registry promotion.
2. Add TritRPC-visible promotion status tests.
3. Add Network Atlas framework catalog JSONL and adapter scorecard schema.
4. Add Serve router p95/inflight autoscaler implementation and tests.
5. Add Community Learning Plane workflow stubs for feedback, curation, evaluation, and reputation.
