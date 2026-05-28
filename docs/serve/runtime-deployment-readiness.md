# Serve runtime deployment readiness

## Status

Readiness note only. This document records what must be true before the Serve router/autoscaler is treated as a runtime deployment surface.

## What is already merged

The following implementation/test tranches are present before runtime deployment work begins:

- `RouterCore.status()` exposes `weights`, `lat_p95`, `inflight`, `shadow`, and `sticky`.
- `RouterCore.update()` applies weight changes and refreshes backend windows/counters.
- `RouterAutoscalerCore` consumes `RouterCore.status()`-shaped payloads.
- Autoscaler pressure is computed from p95 latency plus inflight pressure.
- Autoscaler decisions are bounded by `min_weight` and `step`.
- Autoscaler observability emits pressure and decision metrics.
- Integration tests prove `RouterCore.status()` / `RouterCore.update()` compose with `RouterAutoscalerCore.step_from_status()` without Ray Serve deployment.

## Deployment preconditions

Before enabling runtime deployment, all of the following must be true:

1. Core unit tests pass:
   - `python -m pytest -q tests/test_serve_autoscaler.py`
2. Router/autoscaler integration tests pass:
   - `python -m pytest -q tests/test_serve_router_autoscaler_integration.py`
3. Metrics names are stable:
   - `atlas_router_latency_p95_ms`
   - `atlas_router_inflight`
   - `atlas_router_weight`
   - `atlas_router_pressure`
   - `atlas_router_autoscale_decisions_total`
   - `atlas_router_autoscale_adjustments_total`
4. Runtime deployment remains opt-in.
5. Any Ray Serve integration must keep the fallback import path working when Ray is not installed.
6. Any live weight update loop must preserve existing `shadow` and `sticky` router settings unless explicitly changed.
7. Runtime rollout must include rollback instructions and a dry-run/report-only mode.

## Non-goals

This document does not deploy Ray Serve.

This document does not start a metrics exporter.

This document does not enable an autoscaler loop.

This document does not define production SLOs.

This document does not claim production autoscaling readiness.

## Runtime rollout sequence

A future runtime PR should be split into the following stages:

1. Dry-run autoscaler loop: collect router status, compute decision, emit metrics, do not call `RouterCore.update()`.
2. Report-only deployment doc: record proposed changes, pressure, reason, and adjusted backend.
3. Opt-in active loop: apply decisions only under explicit configuration.
4. Rollback path: disable active loop and restore static router weights.
5. Observability check: confirm pressure and decision metrics are emitted.
6. Promotion gate: require tests and report-only evidence before any active loop is accepted.

## Rollback expectations

Rollback must be possible by configuration only:

- disable the autoscaler loop;
- restore static router weights;
- keep existing router deployments available;
- preserve `shadow` and `sticky` settings unless rollback explicitly changes them;
- keep metrics reporting available for post-rollback analysis.

## Claim boundary

This document is a readiness checklist. It is not a deployment manifest, runtime controller, Ray Serve rollout, SLO declaration, or production readiness claim.
