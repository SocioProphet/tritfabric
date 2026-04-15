# SocioProphet Platform Standards — Storage, Contracts, and Measurement

This repository is a **standards and decision** package for an open, vendor-neutral incident intelligence / ChatOps platform.

We treat the platform as a set of **contexts** (event stream, incident state, artifacts, search, vectors, graphs, metrics) and we standardize:
- **Data contracts:** Avro for event contracts; Arrow + Parquet for analytic payloads; JSON-LD for semantic/provenance overlays.
- **Interfaces:** TritRPC (typed RPC) for service calls; event bus topics for asynchronous flows.
- **Execution:** Beam for batch/stream transforms; Ray for training/serving/task placement.
- **Storage portfolio:** Postgres as system-of-record; OpenSearch for text; optional vector/graph stores based on measured workload triggers.
- **Measurement:** a benchmark harness with 30 defined workloads (latency/throughput/cost/recovery).

## Repository map
- `docs/standards/` — normative standards (MUST/SHOULD/MAY language)
- `docs/benchmarks/` — benchmark methodology and reporting format
- `benchmarks/workloads/` — workload definitions (YAML)
- `benchmarks/harness/` — harness scaffold (drivers to implement)
- `adr/` — Architecture Decision Records (templates + initial decisions)
- `schemas/` — schema placeholders for Avro/Arrow/JSON-LD contexts
- `ops/` — deployment conventions (placeholders)

## Status
- Initial scaffold created: 2026-01-08
- Next: implement benchmark harness code + populate schema directories with v1 contracts.



## Graph Layer

This repo now includes the Graph Store Abstraction standard (RDF/SPARQL, property graph, and AtomSpace-style hypergraph) plus a dedicated graph benchmark workload suite.

## Dev setup

python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r requirements-dev.txt

