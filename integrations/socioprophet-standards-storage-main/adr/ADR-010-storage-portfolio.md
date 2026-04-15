# ADR-010: Storage Portfolio Baseline and Specialization Triggers

- Date: 2026-01-08
- Status: Proposed
- Contexts affected: artifacts, incident state, domain documents, search, vectors, provenance graph, metrics

## Context
Our platform stores multiple **distinct contexts** that do not share the same correctness or query requirements. A single database for all contexts creates hidden coupling and long-term cost.

## Decision (baseline)
We standardize a **minimal baseline** that is correct, operable, and measurable:

- **Object storage** (S3/MinIO-compatible) for all binary artifacts and columnar datasets (Parquet/Arrow IPC).
- **Postgres** as the system-of-record for incident state, tenancy, policy/audit, and relational mappings.
- **OpenSearch** for full-text search and faceting (rebuildable index).
- **Vectors** start in **pgvector** (inside Postgres) unless benchmarked workloads show it violates p95/p99 targets.

## Specialization triggers (maximal path)
We add specialized stores only when benchmarks show the need:

- **MongoDB (optional)** for high-variability domain documents *only if* schema churn + query diversity + change-stream workflows exceed Postgres/JSONB performance/operability targets.
- **OpenSearch kNN (optional)** for vectors *only if* similarity workloads exceed pgvector latency/throughput targets at required recall.
- **Graph store/triplestore (optional)** for provenance/topology *only if* graph traversal workloads (e.g., derivation depth ≥3) become frequent and exceed acceptable latency when implemented over relational tables + indexes.

## Measurement plan
Decisions must be justified by workloads in `benchmarks/workloads/workloads.yaml`:
- Similarity: workloads 14, 24
- Provenance traversal: workload 17
- Schema evolution stress: workload 30
- Multi-tenant contention: workload 28
- Failure/recovery: workload 29

## Consequences
- We keep correctness in one place (Postgres) and keep indexes rebuildable.
- We avoid premature complexity while preserving an evidence-based path to specialization.

