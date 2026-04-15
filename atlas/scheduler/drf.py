from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque

try:
    from atlas.observability.metrics import set_drf_share, set_queue_depth
except Exception:  # pragma: no cover
    set_drf_share = None
    set_queue_depth = None


ResourceVec = Dict[str, float]


def _norm_res(res: Optional[Dict[str, Any]]) -> ResourceVec:
    res = res or {}
    out: ResourceVec = {}
    for k, v in res.items():
        try:
            out[str(k).upper()] = float(v)
        except Exception:
            continue
    for k in ("CPU", "GPU", "MEM"):
        out.setdefault(k, 0.0)
    return out


@dataclass
class QueuedJob:
    ts: float
    tenant: str
    job_id: str
    req: Dict[str, Any]


class DRFBroker:
    """Dominant Resource Fairness (DRF) broker.

    Goal:
    - pick the next runnable job (fits available resources)
    - prefer the tenant with the smallest dominant share (weighted)

    This is a *broker*, not a cluster manager:
    - it does not preempt
    - it does not pack across nodes
    - it simply decides ordering and updates per-tenant reserved shares

    Integrations:
    - daemon calls pick() when resources are available
    - daemon calls release() when a job completes
    """

    def __init__(self, tenant_weights: Optional[Dict[str, float]] = None):
        self.weights: Dict[str, float] = {k: float(v) for k, v in (tenant_weights or {}).items()}
        self.weights.setdefault("default", 1.0)

        self.alloc: Dict[str, ResourceVec] = defaultdict(lambda: {"CPU": 0.0, "GPU": 0.0, "MEM": 0.0})
        self.cluster_total: ResourceVec = {"CPU": 1.0, "GPU": 0.0, "MEM": 1.0}

        self._q: deque[QueuedJob] = deque()

    def set_cluster_total(self, total: Dict[str, Any]) -> None:
        t = _norm_res(total)
        # Avoid divide-by-zero; keep small eps
        self.cluster_total = {
            "CPU": max(1e-6, t.get("CPU", 0.0)),
            "GPU": max(0.0, t.get("GPU", 0.0)),
            "MEM": max(1e-6, t.get("MEM", 0.0)),
        }

    def submit(self, tenant: str, job_id: str, req: Dict[str, Any]) -> None:
        tenant = tenant or "default"
        self._q.append(QueuedJob(ts=time.time(), tenant=tenant, job_id=job_id, req=req))
        self._emit_queue_depths()

    def _emit_queue_depths(self) -> None:
        if not set_queue_depth:
            return
        # Count per tenant
        counts: Dict[str, int] = defaultdict(int)
        for j in self._q:
            counts[j.tenant] += 1
        for tenant, c in counts.items():
            set_queue_depth(tenant, c)

    def _dominant_share_after(self, tenant: str, req_res: ResourceVec) -> float:
        w = max(1e-6, float(self.weights.get(tenant, self.weights.get("default", 1.0))))
        dom = 0.0
        for r in ("CPU", "GPU", "MEM"):
            total = float(self.cluster_total.get(r, 0.0))
            if total <= 0.0:
                continue
            share = (self.alloc[tenant].get(r, 0.0) + req_res.get(r, 0.0)) / (total * w)
            dom = max(dom, share)
        return float(dom)

    def _emit_shares(self) -> None:
        if not set_drf_share:
            return
        for tenant, a in self.alloc.items():
            w = max(1e-6, float(self.weights.get(tenant, self.weights.get("default", 1.0))))
            for r in ("CPU", "GPU", "MEM"):
                total = float(self.cluster_total.get(r, 0.0))
                share = (a.get(r, 0.0) / (total * w)) if total > 0 else 0.0
                set_drf_share(tenant, r, float(share))

    def pick(self, available: Dict[str, Any]) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Pick the next job to run given currently available resources.

        Returns (tenant, job_id, req) and reserves its resources, or None if nothing fits.
        """
        avail = _norm_res(available)
        if not self._q:
            return None

        best_idx = None
        best_dom = None
        best_ts = None

        # Scan queue; choose smallest dominant share among runnable jobs.
        for idx, job in enumerate(self._q):
            req_res = _norm_res(job.req.get("resources", {}))
            # Fit check
            if req_res["CPU"] > avail["CPU"] + 1e-9:
                continue
            if req_res["GPU"] > avail["GPU"] + 1e-9:
                continue
            if req_res["MEM"] > avail["MEM"] + 1e-9:
                continue

            dom = self._dominant_share_after(job.tenant, req_res)
            if best_dom is None or dom < best_dom - 1e-12 or (abs(dom - best_dom) <= 1e-12 and job.ts < (best_ts or 0)):
                best_dom = dom
                best_idx = idx
                best_ts = job.ts

        if best_idx is None:
            return None

        # Pop by index from deque
        job = self._q[best_idx]
        del self._q[best_idx]

        # Reserve resources
        req_res = _norm_res(job.req.get("resources", {}))
        for r in ("CPU", "GPU", "MEM"):
            self.alloc[job.tenant][r] = float(self.alloc[job.tenant].get(r, 0.0) + req_res.get(r, 0.0))

        self._emit_queue_depths()
        self._emit_shares()
        return (job.tenant, job.job_id, job.req)

    def release(self, tenant: str, req: Dict[str, Any]) -> None:
        """Release reserved resources for a finished job."""
        tenant = tenant or "default"
        req_res = _norm_res(req.get("resources", {}))
        a = self.alloc[tenant]
        for r in ("CPU", "GPU", "MEM"):
            a[r] = max(0.0, float(a.get(r, 0.0) - req_res.get(r, 0.0)))
        self._emit_shares()

    def queued(self) -> List[QueuedJob]:
        return list(self._q)
