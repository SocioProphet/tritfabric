# Observability Standard (OpenTelemetry)

## Requirements
- All services MUST emit OTEL traces and metrics.
- Every event and RPC call MUST propagate correlation identifiers:
  - trace_id, span_id
  - incident_id, event_id
  - dataset_id / artifact_id where relevant

## Why this matters
Incident platforms are judged on tail latency and mean-time-to-understand. Without consistent correlation, debugging and audit become narrative rather than evidence.

## Baseline metrics
- ingest_throughput, queue_lag, processing_latency_p50/p95/p99
- error_rate, retry_rate, dead_letter_rate
- model_inference_latency_p95/p99
- similarity_recall@k (measured offline)
- storage_read_latency/write_latency and index_build_time

