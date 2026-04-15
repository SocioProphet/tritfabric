# ADR-020: Graph Store Abstraction Layer (RDF + Property Graph + Hypergraph)

## Status
Proposed

## Context

The platform requires first-class graph capabilities for provenance, topology, identity linkage, and semantic querying. Multiple graph paradigms are relevant:
- RDF (JSON-LD/PROV-O; SPARQL)
- Property graphs (operational traversals)
- Hypergraphs (AtomSpace-style n-ary relations)

No single engine is guaranteed to optimize all paradigms simultaneously. Therefore the platform must define engine-neutral contracts and allow pluggable implementations.

## Decision

We adopt a **Graph Store Abstraction Layer** with:
1. A unified RPC contract (`Query/Upsert/Delete/Explain`) supporting multiple query languages.
2. Canonical identity and provenance headers shared with Avro event contracts.
3. At least one RDF store implementation meeting SPARQL 1.1 requirements (initial candidate: Blazegraph in containers).
4. Optional property graph and hypergraph backends behind the same abstraction when justified by measured workloads.

## Consequences

### Positive
- Enables engine substitution and multi-engine composition.
- Makes graph correctness and performance measurable and testable.
- Keeps multimodal evidence references consistent across stores.

### Negative / Costs
- Adds an abstraction layer to design and maintain.
- Requires careful definition of cross-engine semantics (consistency, transactionality).

## Validation

Adoption is considered successful when:
- The platform can run graph workload suite benchmarks (graph_workloads.yaml) against at least one RDF engine with reproducible results.
- A reference dataset can be exported as JSON-LD and N-Quads with stable IDs and provenance links.
- The same application-level feature can be executed against alternative backends with no code changes outside the adapter.

