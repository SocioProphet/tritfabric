# Benchmark Program Overview

## Purpose
All storage specialization decisions MUST be supported by measured results under workloads representative of our platform.

## Method
- Each workload is defined in `benchmarks/workloads/workloads.yaml`.
- For each candidate configuration, we collect:
  - p50/p95/p99 latency distributions
  - sustained throughput
  - error rate
  - resource usage (CPU/mem/disk)
  - index build time + index size
  - recovery time under injected faults

## Statistical note
Latency is typically heavy-tailed; report percentiles and plot distributions. Use at least 1,000 samples per workload per configuration.

## Output format
- One report per experiment in `benchmarks/reports/<date>-<candidate>/`.
- Include full configuration manifests, so results are reproducible.

