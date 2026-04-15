# Graph and Semantic Stores Standard (RDF, Property Graph, Hypergraph)

## Purpose

We standardize *graph persistence and graph query* as a first-class platform capability because incident intelligence, provenance, and “meaning over time” are graph-native problems: derivation chains, dependency topology, identity resolution, and policy/evidence linkage are all more naturally expressed as edges than as rows.

This standard defines a **Graph Store Abstraction Layer** that allows us to run multiple backing engines (e.g., Blazegraph for RDF/SPARQL, Neo4j for property graphs, AtomSpace-compatible hypergraph stores) behind stable contracts. The contracts, not the engines, are the product.

## Scope

This standard covers:
- **RDF store** requirements (SPARQL 1.1 query/update, named graphs, provenance)
- **Property graph** requirements (nodes/edges with properties, traversal queries)
- **Hypergraph** requirements (n-ary relations / “atoms” / higher-order links; AtomSpace-style patterns)
- **Multimodal linkage**: text, tables, images, audio, video, embeddings, and their provenance references

This standard does **not** require a single graph database to do everything. It requires that we can **compose** graph capabilities and switch engines without rewriting the platform.

## Normative Definitions

### Graph Data Classes

We define three interoperable data classes:

1. **RDF Data Class**
   - Representation: triples/quads (subject, predicate, object, optional graph)
   - Query language: SPARQL 1.1 (SELECT/CONSTRUCT/ASK/DESCRIBE)
   - Update: SPARQL Update
   - Semantics: JSON-LD contexts define mappings to RDF vocabularies

2. **Property Graph Data Class**
   - Representation: nodes and directed edges with key/value properties
   - Query language: engine-specific (Cypher, Gremlin) but abstracted through contracts
   - Update: upsert nodes/edges, bulk load, property patch

3. **Hypergraph Data Class**
   - Representation: atoms/hyperedges supporting n-ary relations and typed links
   - Query language: pattern matching primitives (AtomSpace-style), abstracted through contracts
   - Update: add/remove atoms, truth-values/confidence if supported

### Multimodal Objects

“Multimodal” in the graph layer means graph nodes can reference *modal artifacts* and their derived representations:
- **Artifact**: binary or structured object stored in object storage (S3/MinIO), identified by content hash
- **Representation**: text extraction, thumbnails, embeddings, feature tables (Arrow/Parquet), transcripts, etc.
- **Linkage**: graph assertions connect incidents/assets/policies to artifacts and representations

**MUST**: Large binary payloads are stored in object storage, not inside graph DB pages. Graph stores hold identifiers, metadata, and pointers.

## Required Interfaces (Engine-Agnostic Contracts)

### Query Contract

All graph stores MUST support the following *logical operations* via the platform RPC contract (see 030-service-interfaces-tritrpc.md):

- `Query(GraphQueryRequest) -> GraphQueryResponse`
- `Upsert(GraphUpsertRequest) -> GraphUpsertResponse`
- `Delete(GraphDeleteRequest) -> GraphDeleteResponse`
- `Explain(GraphExplainRequest) -> GraphExplainResponse` (optional but recommended for performance diagnostics)

`GraphQueryRequest` MUST include:
- `query_language`: { `SPARQL`, `CYPHER`, `GREMLIN`, `ATOM_PATTERN`, `DATALOG` (optional) }
- `query_text` or structured query AST
- `dataset_id` / `named_graph` / `tenant_id`
- `consistency_profile` (see below)
- `deadline_ms` and pagination hints

`GraphQueryResponse` MUST return:
- typed rows (Arrow preferred for tabular result sets) and/or RDF (N-Quads/JSON-LD) and/or graph paths
- `result_provenance`: input datasets, engine version, index versions, execution timestamps

### Consistency & Replication Profiles

We standardize *profiles* rather than forcing one model:

- `STRONG_SINGLE_REGION`: strongly consistent within a region (default for policy/evidence correctness)
- `READ_YOUR_WRITES`: per-tenant/session monotonicity (default for interactive editing)
- `EVENTUAL_MULTI_REGION`: async replication (default for large knowledge graphs where latency > strictness)
- `SNAPSHOT_ANALYTICS`: consistent snapshot for batch queries (default for reporting)

Graph store implementations MUST declare which profiles they support and the semantics (staleness bounds if applicable).

## RDF Store Requirements (Minimum Viable)

The platform MUST have at least one RDF store implementation that supports:
- SPARQL 1.1 Query and Update
- Named graphs and graph-level access control boundaries
- Bulk load of N-Triples/N-Quads
- Export to N-Quads and JSON-LD
- Basic RDFS entailment is OPTIONAL; OWL reasoning is OPTIONAL and should be externally pluggable

**Implementation note (non-normative):** Blazegraph is a plausible initial engine because it is mature for SPARQL workloads and can be containerized, but the interface must remain engine-neutral.

## Property Graph Requirements (Optional but Supported)

We SHOULD support a property graph engine for:
- Low-latency traversals (k-hop neighborhood, shortest path variants)
- Operational topology queries (service dependency exploration)
- Graph algorithms pipelines

Neo4j is a plausible engine candidate; alternatives may be used if they satisfy the contract.

## Hypergraph Requirements (AtomSpace Alignment)

If we use AtomSpace-style hypergraphs, we MUST define:
- Atom types, link types, and identifiers (stable IRIs/UUIDs)
- Pattern matching primitives exposed through `ATOM_PATTERN` queries
- Optional truth-value/confidence semantics must be represented explicitly (no hidden inference)

The hypergraph layer MUST be interoperable with RDF export when possible (e.g., reification or RDF-star mappings), even if information is lossy.

## Performance Measurement Criteria

Graph stores MUST be evaluated using a standardized workload suite (see `benchmarks/workloads/graph_workloads.yaml`) with metrics:

- Latency distributions: p50/p95/p99 for each query class
- Throughput: queries/sec and updates/sec under concurrency
- Index build and rebuild time
- Storage footprint: raw vs indexed
- Replication lag (for eventual profiles) and recovery time
- Query plan stability (regression detection)

We MUST test multiple graph shapes:
- scale-free (power-law degree)
- near-bipartite (entity-attribute)
- temporal provenance chains (long derivation paths)
- dense local clusters (incident cohorts)

## Security and Multi-tenancy

- Tenant boundaries MUST be enforceable at the graph layer (named graphs, labels, or physical separation).
- Access decisions MUST be logged as immutable policy events and linked into provenance graphs.

## What “multimodal” demands from the graph layer

The graph layer MUST be able to represent and query links such as:
- Incident -> EvidenceArtifact (hash pointer) -> DerivedText -> EmbeddingVector
- Incident -> Service -> Deployment -> Region -> OwnerTeam
- Claim -> Justification -> SourceRecord(s) -> Transform(s)

We do not require the graph engine itself to store embeddings, but it MUST store stable references and metadata to enable retrieval.

