from __future__ import annotations

from typing import Dict, Optional
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# --- TritRPC v1 alignment: record envelope codes (TRUE/MID/FALSE) per endpoint/tenant ---
REQUESTS = Counter(
    "atlas_rpc_requests_total",
    "Total RPC requests accepted by atlasd",
    ["endpoint", "tenant", "trit"],  # trit ∈ {TRUE,MID,FALSE}
)

# Admission & scheduling
QUEUE_DEPTH = Gauge("atlas_queue_depth", "Queued jobs", ["tenant"])
SCHEDULE_LATENCY = Histogram(
    "atlas_schedule_latency_seconds",
    "Time from QUEUED to RUNNING",
    buckets=[0.05, 0.1, 0.2, 0.5, 1, 2, 5],
    labelnames=["tenant"],
)
DRF_DOM_SHARE = Gauge(
    "atlas_drf_dominant_share",
    "DRF dominant share by tenant and resource",
    ["tenant", "resource"],
)

# Trials
TRIAL_METRIC = Gauge("atlas_trial_metric", "Best metric per job", ["job_id", "metric"])
TRIAL_FLOPS = Gauge("atlas_trial_flops", "FLOPs of best trial", ["job_id"])
TRIAL_PARAMS = Gauge("atlas_trial_params", "Params of best trial", ["job_id"])

# ONNX checks
ONNX_COS_SIM = Gauge(
    "atlas_onnx_cosine_similarity",
    "Cosine similarity PyTorch↔ONNX for best trial",
    ["job_id"],
)
ONNX_EXPORTS = Counter(
    "atlas_onnx_exports_total",
    "ONNX export attempts",
    ["job_id", "status"],  # status ∈ {ok,fail}
)

# Serve routing & autoscaler
ROUTER_LAT_P95 = Gauge("atlas_router_latency_p95_ms", "Router p95 latency ms", ["backend"])
ROUTER_INFLIGHT = Gauge("atlas_router_inflight", "Router inflight requests", ["backend"])
ROUTER_WEIGHT = Gauge("atlas_router_weight", "Router weight per backend", ["backend"])
AUTOSCALE_ADJUST = Counter(
    "atlas_router_autoscale_adjustments_total",
    "Autoscaler weight adjustments",
    ["backend", "reason"],
)


def start_metrics_server(port: int = 9108) -> None:
    """Start a Prometheus /metrics exporter on port. Call once in daemon init."""
    start_http_server(port)


def record_request(endpoint: str, tenant: str, trit: str) -> None:
    REQUESTS.labels(endpoint=endpoint, tenant=tenant, trit=trit).inc()


def set_queue_depth(tenant: str, depth: int) -> None:
    QUEUE_DEPTH.labels(tenant=tenant).set(int(depth))


def observe_schedule_latency(tenant: str, seconds: float) -> None:
    SCHEDULE_LATENCY.labels(tenant=tenant).observe(float(seconds))


def set_drf_share(tenant: str, resource: str, share: float) -> None:
    DRF_DOM_SHARE.labels(tenant=tenant, resource=resource).set(float(share))


def record_best_trial(
    job_id: str,
    metric_name: str,
    metric_value: float,
    flops: Optional[float] = None,
    params: Optional[float] = None,
) -> None:
    TRIAL_METRIC.labels(job_id=job_id, metric=metric_name).set(float(metric_value))
    if flops is not None:
        TRIAL_FLOPS.labels(job_id=job_id).set(float(flops))
    if params is not None:
        TRIAL_PARAMS.labels(job_id=job_id).set(float(params))


def record_onnx_export(job_id: str, status: str, cos_sim: Optional[float] = None) -> None:
    ONNX_EXPORTS.labels(job_id=job_id, status=status).inc()
    if cos_sim is not None:
        ONNX_COS_SIM.labels(job_id=job_id).set(float(cos_sim))


def set_router_stats(
    lat_p95: Optional[Dict[str, float]],
    inflight: Optional[Dict[str, int]],
    weights: Optional[Dict[str, int]],
) -> None:
    for k, v in (lat_p95 or {}).items():
        ROUTER_LAT_P95.labels(backend=k).set(float(v))
    for k, v in (inflight or {}).items():
        ROUTER_INFLIGHT.labels(backend=k).set(float(v))
    for k, v in (weights or {}).items():
        ROUTER_WEIGHT.labels(backend=k).set(float(v))


def record_autoscale_adjust(backend: str, reason: str) -> None:
    AUTOSCALE_ADJUST.labels(backend=backend, reason=reason).inc()
