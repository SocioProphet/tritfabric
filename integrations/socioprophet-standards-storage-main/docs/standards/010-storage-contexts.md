# Storage Contexts and Canonical Mapping

## Context taxonomy
We distinguish the following contexts:

1) **Event stream (hot path)**: append-only events flowing through topics.
2) **Incident state (system-of-record)**: mutable lifecycle state and relational mappings.
3) **Domain documents (JSON objects)**: configs, runbooks, connectors, annotations.
4) **Artifacts (binary + columnar)**: PDFs, traces, Parquet shards, Arrow IPC, model binaries.
5) **Search**: full-text + faceting.
6) **Vectors**: embedding indexes for similarity.
7) **Graphs**: topology + provenance (JSON-LD/PROV-O).
8) **Metrics/time series**: operational telemetry and drift signals.

## Canonical mapping (baseline)
- Artifacts: **Object storage** (S3/MinIO)
- Incident state + policy/audit: **Postgres**
- Domain documents: **Postgres/JSONB** initially; optional MongoDB when triggered
- Search: **OpenSearch**
- Vectors: **pgvector** initially; optional OpenSearch kNN when triggered
- Graphs: relational adjacency tables initially; optional triplestore/graph DB when triggered
- Metrics: Prometheus-compatible TSDB (implementation-specific)

## Non-negotiable rule
Binary artifacts MUST NOT be stored as blobs inside relational/document DBs except for tiny control-plane payloads.
Store blobs in object storage and reference by content hash + URI.


## Graph / Semantic and Hypergraph Context

This context stores provenance, topology, identity links, and semantic assertions. It MUST support RDF export/import (JSON-LD and N-Quads) and SHOULD support operational traversal queries. Hypergraph capabilities (AtomSpace-style) MAY be provided behind the same abstraction.
