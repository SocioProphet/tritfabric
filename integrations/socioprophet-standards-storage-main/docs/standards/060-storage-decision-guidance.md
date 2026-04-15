# Storage Decision Guidance: Baseline vs Maximal Specialization

## Baseline (default)
We default to:
- Object storage for artifacts and datasets
- Postgres as system-of-record for incident/policy/audit
- OpenSearch for search
- pgvector for similarity (initial)

This baseline prioritizes correctness and operability.

## Maximal specialization (only when measured)
We add specialized stores only when benchmark evidence forces it:

### 1) MongoDB for high-variability domain documents (optional)
Use when ALL are true:
- document schemas change frequently,
- query patterns are diverse (nested predicates, aggregation),
- change streams are needed for orchestration,
- Postgres/JSONB fails workload targets (latency, ops burden).

### 2) OpenSearch kNN (optional) or dedicated vector store
Use when:
- similarity workloads violate pgvector p95/p99 or throughput targets at required recall,
- index rebuild times become unacceptable,
- multi-tenant isolation cannot be met cleanly.

### 3) Graph DB / triplestore (optional)
Use when:
- provenance/topology traversal (derivation depth ≥ 3) is frequent,
- relational adjacency tables fail p95 latency targets,
- explainability requires richer graph query semantics.

## Required evidence
Any move to specialization MUST cite benchmark workloads and recorded results.

