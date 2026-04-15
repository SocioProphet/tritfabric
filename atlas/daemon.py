from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

from atlas.policy import Policy
from atlas.ray_runner import RayRunner
from atlas.registry import Registry
from atlas.scheduler.drf import DRFBroker
from atlas.autopilot.promotion_controller import PromotionController
from atlas.observability.metrics import observe_schedule_latency, set_queue_depth
from atlas.observability.logs import log_event


def _local_resources() -> Dict[str, float]:
    cpu = float(os.cpu_count() or 1)
    # GPU and MEM are unknown in minimal mode.
    return {"CPU": cpu, "GPU": 0.0, "MEM": 1.0}


class Daemon:
    def __init__(self, policy: Policy, artifacts_root: str, shacl_enforce: bool = True):
        self.policy = policy
        self.artifacts_root = artifacts_root
        self.runner = RayRunner(artifacts_root=artifacts_root)
        self.registry = Registry(artifacts_root, shacl_enforce=shacl_enforce)

        weights = policy.get("scheduler", "tenant_weights", default={"default": 1.0})
        self.broker = DRFBroker(tenant_weights=weights)

        # promotion controller reads sidecars produced by registry/runner.
        self.promoter = PromotionController(
            artifacts_root=artifacts_root,
            onnx_cosine_threshold=float(policy.get("promotion", "onnx_cosine_threshold", default=0.995)),
            eval_delta_threshold=float(policy.get("promotion", "eval_delta_threshold", default=0.01)),
            shacl_enforce=bool(policy.get("promotion", "shacl_enforce", default=True)),
        )

        self._status: Dict[str, Dict[str, Any]] = {}
        self._reqs: Dict[str, Dict[str, Any]] = {}
        self._best: Dict[str, Dict[str, Any]] = {}

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None

        # cluster totals for DRF
        self.broker.set_cluster_total(_local_resources())

    def start(self) -> None:
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        t = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread = t
        t.start()

    def stop(self) -> None:
        self._stop.set()

    def submit_job(self, req: Dict[str, Any]) -> str:
        job_id = req.get("job_id") or f"job-{uuid.uuid4().hex[:12]}"
        tenant = req.get("tenant", "default")
        with self._lock:
            self._reqs[job_id] = dict(req)
            self._status[job_id] = {"state": "QUEUED", "info": {"tenant": tenant, "queued_at": time.time()}}
        self.broker.submit(tenant=tenant, job_id=job_id, req=req)
        log_event("job_queued", tenant=tenant, job_id=job_id, extra={"req_keys": list(req.keys())})
        self.start()
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._status.get(job_id, {"state": "UNKNOWN", "info": {}}))

    def cancel(self, job_id: str) -> Dict[str, Any]:
        # Minimal cancellation: mark; runner won't be interrupted.
        with self._lock:
            st = self._status.get(job_id)
            if not st:
                return {"state": "UNKNOWN", "info": {}}
            st["state"] = "CANCEL_REQUESTED"
            st.setdefault("info", {})["cancel_requested_at"] = time.time()
        return self.get_status(job_id)

    def promote(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            req = dict(self._reqs.get(job_id, {}))
            best = dict(self._best.get(job_id, {}))
        card = self.registry.promote(job_id, req, {"metrics": best.get("metrics", {})})
        # After promotion, run gate report (reads onnx_check + shacl report if any).
        report = self.promoter.on_study_complete(job_id, req, {"metrics": best.get("metrics", {})})
        return {"card": card, "report": report}

    def _scheduler_loop(self) -> None:
        while not self._stop.is_set():
            # Update cluster totals (could be dynamic)
            self.broker.set_cluster_total(_local_resources())

            # available resources = cluster totals - sum reserved
            # in minimal mode we approximate available == cluster totals
            available = _local_resources()

            picked = self.broker.pick(available=available)
            if picked is None:
                time.sleep(0.25)
                continue

            tenant, job_id, req = picked
            now = time.time()
            with self._lock:
                st = self._status.get(job_id, {})
                queued_at = float(st.get("info", {}).get("queued_at", now))
                self._status[job_id] = {"state": "RUNNING", "info": {"tenant": tenant, "started_at": now}}
            observe_schedule_latency(tenant, now - queued_at)
            log_event("job_started", tenant=tenant, job_id=job_id)

            th = threading.Thread(target=self._run_job, args=(tenant, job_id, req), daemon=True)
            th.start()

            # small sleep to avoid tight loop
            time.sleep(0.05)

    def _run_job(self, tenant: str, job_id: str, req: Dict[str, Any]) -> None:
        try:
            result = self.runner.run(job_id, req)
            metric_name = str(req.get("metric") or "val_score")
            metrics = result.get("best_metrics", {}) or {}
            with self._lock:
                self._best[job_id] = {"metrics": metrics, "trial_id": result.get("trial_id")}
                self._status[job_id] = {"state": "SUCCEEDED", "info": {"tenant": tenant, "finished_at": time.time()}}
            log_event("job_succeeded", tenant=tenant, job_id=job_id, extra={"metrics": metrics})

            # Auto-promotion
            thresh = self.policy.get("scheduler", "auto_promotion", "metric_threshold", default=None)
            if thresh is not None:
                try:
                    v = float(metrics.get(metric_name, -1e9))
                    if v >= float(thresh):
                        self.promote(job_id)
                        log_event("job_promoted", tenant=tenant, job_id=job_id, extra={"metric": metric_name, "value": v, "threshold": float(thresh)})
                except Exception as e:
                    log_event("auto_promotion_error", level="warning", tenant=tenant, job_id=job_id, extra={"error": str(e)})

        except Exception as e:
            with self._lock:
                self._status[job_id] = {"state": "FAILED", "info": {"tenant": tenant, "error": str(e), "finished_at": time.time()}}
            log_event("job_failed", level="error", tenant=tenant, job_id=job_id, extra={"error": str(e)})
        finally:
            # release reserved resources
            self.broker.release(tenant, req)
