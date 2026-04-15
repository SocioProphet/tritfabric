# Graph and Storage Interview Template (Requirements Elicitation)

## Purpose

This template is used to elicit the *workload and correctness envelope* from a user or product owner so we can choose appropriate consistency, replication, storage placement, and graph engine mix. The goal is to translate “how the app should feel” into measurable storage requirements and benchmark workloads.

## Section A — User Experience Targets

1. **Interactive latency target:** What is the acceptable response time for the main graph queries (p95 and p99)?
2. **Freshness expectation:** When data is written, how quickly must it be visible to the same user, to other users, and across regions?
3. **Offline/disconnected mode:** Does the app need local-first behavior with conflict resolution?
4. **Failure tolerance:** What behavior is acceptable during partial outages (degraded reads, read-only, queue writes)?

## Section B — Correctness and Consistency

5. Which of these profiles describe the expected semantics?
   - Strong single-region
   - Read-your-writes
   - Eventual multi-region (bounded staleness acceptable)
   - Snapshot analytics
6. Are there any objects that must never be inconsistent (policy decisions, evidence chains, access grants)?
7. Do we need transactional updates across multiple graph entities (atomic incident state updates)?
8. Do we need immutable append-only audit for changes, with reconstructable history?

## Section C — Graph Workload Shape

9. What is the dominant graph type?
   - RDF semantic graph (SPARQL)
   - Property graph (traversal, path queries)
   - Hypergraph (n-ary, AtomSpace-style)
   - Mixed
10. Typical query patterns (select all that apply):
   - Star queries (entity with many attributes)
   - k-hop neighborhood expansion
   - Shortest path / constrained path
   - Provenance chain traversal (prov:wasDerivedFrom depth N)
   - Subgraph extraction (CONSTRUCT)
   - Full-text + facets (hybrid graph + search)
11. Expected graph size (order-of-magnitude):
   - Nodes
   - Edges
   - Named graphs / tenants
12. Degree distribution expectations (few hubs vs uniform)?
13. Update rate: inserts/sec, updates/sec, deletes/sec.

## Section D — Multimodal Requirements

14. Which modalities are first-class in the app?
   - Text documents
   - Images
   - Audio/video
   - Tables (Arrow/Parquet)
   - Embeddings/vectors
15. Must the graph store perform vector similarity, or is it acceptable to reference an external vector index?
16. Must we support provenance linking from “answer” back to original multimodal evidence?

## Section E — Replication, Placement, and Mesh

17. Geographic distribution: single region, multi-region active/active, edge nodes?
18. Data residency constraints (per tenant, per region)?
19. Expected concurrency: active users, active agents, background jobs.
20. Mesh topology: are there constrained links (high latency, intermittent)?
21. Are we allowed to centralize the graph store, or must it be federated?

## Section F — Governance, Auditing, and Security

22. Tenant isolation requirements (logical vs physical separation).
23. Authentication and authorization model (OIDC, service identity).
24. Required audit outputs (who queried what, who changed what).
25. Retention and deletion requirements (legal holds, right-to-delete).

## Section G — Benchmark Mapping (for measurement)

26. For each critical query, identify:
   - Query class (SPARQL/Cypher/etc.)
   - Result size distribution
   - SLA target (p95/p99)
   - Concurrency level
27. Choose top 5 “make-or-break” workloads; map them to the graph workload suite IDs in `benchmarks/workloads/graph_workloads.yaml`.

## Output

At completion, we produce:
- A chosen consistency profile per context
- A graph engine mix proposal (RDF, property, hypergraph, optional)
- A benchmark subset (minimum 10 workloads) and acceptance thresholds

