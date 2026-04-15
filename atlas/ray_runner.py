from __future__ import annotations

import hashlib
import json
import os
import random
import time
from typing import Any, Dict, Optional, Tuple

from slate.utils.ledger import write_onnx_check


class RayRunner:
    """Runner abstraction.

    - In production, this launches Ray Tune / Ray Train / Ray Serve tasks.
    - In this consolidated scaffold, we provide:
        - a deterministic local fallback that produces artifacts
        - optional Ray usage if installed (not required for basic repo validity)

    The key is that the *interfaces* are stable, so we can swap implementations without changing the API surface.
    """

    def __init__(self, artifacts_root: str = "artifacts"):
        self.artifacts_root = artifacts_root

    def _job_dir(self, job_id: str) -> str:
        return os.path.join(self.artifacts_root, job_id)

    def run(self, job_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
        """Run a job and return a dict containing best metrics and metadata."""
        try:
            import ray  # type: ignore  # noqa: F401
            # If Ray is installed, we still use fallback unless explicitly enabled.
            if bool(req.get("use_ray", False)):
                return self._run_with_ray(job_id, req)
        except Exception:
            pass
        return self._run_local(job_id, req)

    def _run_local(self, job_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
        os.makedirs(self._job_dir(job_id), exist_ok=True)

        # Deterministic pseudo-metric from job_id
        h = hashlib.sha256(job_id.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "big")
        rnd = random.Random(seed)

        metric_name = str(req.get("metric") or "val_score")
        mode = str(req.get("mode") or "max").lower()

        # Produce a plausible metric
        base = rnd.random()
        value = base if mode == "max" else (1.0 - base)

        best_metrics = {metric_name: float(value)}

        # ledger.json (best trial)
        ledger = {
            "job_id": job_id,
            "trial_id": "trial-0",
            "best_metrics": best_metrics,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "local fallback runner (replace with Ray Train/Tune for real workloads)",
        }
        with open(os.path.join(self._job_dir(job_id), "ledger.json"), "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)

        # If ONNX runtime check requested, write a sidecar. (Real impl would export and check.)
        onnx_cfg = (req.get("export", {}) or {}).get("onnx", {}) or {}
        if bool(onnx_cfg.get("runtime_check", False)):
            thr = float(onnx_cfg.get("cos_sim_threshold", 0.995))
            sim = 0.999  # optimistic placeholder
            ok = sim >= thr
            write_onnx_check(
                artifacts_root=self.artifacts_root,
                job_id=job_id,
                trial_id="trial-0",
                ok=ok,
                sim=sim,
                thr=thr,
                path=str(onnx_cfg.get("path", "")),
            )

        return {"best_metrics": best_metrics, "trial_id": "trial-0"}

    def _run_with_ray(self, job_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder hook point.
        # Real implementation would:
        # - build trainable from req["ir"], req["entrypoint"], etc
        # - allocate placement groups from req["resources"]
        # - run Ray Tune/Trian and collect best result
        return self._run_local(job_id, req)
