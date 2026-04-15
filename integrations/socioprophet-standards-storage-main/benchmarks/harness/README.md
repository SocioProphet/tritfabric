# Benchmark Harness (Scaffold)

This directory will host:
- workload runners (drivers) for Postgres, MongoDB, CouchDB, OpenSearch, vector backends
- OTEL exporters for uniform measurement capture
- fault injection tooling for recovery tests

## Planned commands (to implement)
- bench run --candidate postgres-jsonb --workload W03
- bench run --candidate mongo --workload W18
- bench suite --candidate baseline --all

