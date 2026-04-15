# Platform Standards (Normative)

This document uses RFC 2119 language: **MUST**, **SHOULD**, **MAY**.

## 1. Vendor neutrality
- Components MUST be specified by **interface and behavior**, not vendor brand.
- Any implementation MAY be swapped if it satisfies the same contracts and SLAs.

## 2. Contracts and evolution
- Event schemas MUST be versioned and compatibility-checked.
- Backward-compatible changes MUST be additive with defaults.
- Breaking changes MUST increment major version and publish to new topic/endpoint.

## 3. Identity and provenance
- Every record MUST carry stable identifiers (incident_id, event_id, artifact_id, model_id, policy_id).
- Derived artifacts MUST reference inputs by ID and include a transform signature (git commit + parameters hash).

## 4. Observability
- All services MUST emit traces/metrics/logs with shared correlation IDs.

## 5. Measurement-first decisions
- Storage and indexing decisions MUST be justified by benchmark workloads and reported p50/p95/p99.

