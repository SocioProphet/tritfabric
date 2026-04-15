# Service Interface Standard (TritRPC)

## Goals
- Replace informal REST payload drift with typed, versioned interfaces.
- Carry correlation/provenance metadata consistently.

## Requirements
- All RPC methods MUST have versioned request/response message types.
- All calls MUST include standard metadata headers:
  - trace_id, span_id
  - tenant_id
  - incident_id/event_id where applicable
  - model_id + model_version for model-influenced outputs
  - artifact_hash references for any external payloads

## Minimal method families
- Ingest: SubmitLogs, SubmitEvents
- Detect: Score
- Group: Cluster
- Enrich: Topology, Localization
- Retrieve: Similar
- ChatOps: Compose, Query
- Policy: Evaluate

