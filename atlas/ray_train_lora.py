"""Ray Train orchestration for the WS-A LoRA fine-tune.

Turns a job request + a brokered GPU placement (from ``atlas/gpu_broker.py``) into a Ray Train ``TorchTrainer`` run
and collects the best metric. Ray is imported lazily so the control plane imports this module without Ray installed;
``scaling_config_from_placement`` is pure and unit-tested without Ray/GPU.

This is the implementation behind ``RayRunner._run_with_ray`` — the seam where the SAME training fabric lands on
whatever GPU the broker picked as cheapest/compliant (NeoCloud, hyperscaler, or non-NVIDIA Ascend).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


def gpu_count_from_req(req: Dict[str, Any]) -> int:
    """How many GPU workers the job asked for (pure)."""
    gpu = req.get("gpu") or {}
    try:
        return max(1, int(gpu.get("count", 1)))
    except (TypeError, ValueError):
        return 1


def scaling_config_from_placement(req: Dict[str, Any], placement: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Derive Ray ScalingConfig kwargs from the job + KubeRay placement (pure — returns a plain dict).

    One worker per GPU; each worker pinned to 1 GPU and the placement's vCPU budget (default 8).
    """
    num_workers = gpu_count_from_req(req)
    cpus_per_worker = 8
    if placement and isinstance(placement.get("worker_group"), dict):
        cpus_per_worker = int(placement["worker_group"].get("cpu", cpus_per_worker))
    use_gpu = bool((req.get("gpu") or {}).get("type")) or num_workers >= 1
    return {
        "num_workers": num_workers,
        "use_gpu": use_gpu,
        "resources_per_worker": {"GPU": 1, "CPU": cpus_per_worker},
    }


def run_lora_finetune(job_id: str, req: Dict[str, Any], artifacts_root: str = "artifacts") -> Dict[str, Any]:
    """Run a real LoRA fine-tune on Ray Train and return {"best_metrics", "trial_id"}.

    Raises if Ray/torch stack is unavailable so the caller (RayRunner) can fall back to the local runner.
    """
    import ray.train  # noqa: F401
    from ray.train import RunConfig, ScalingConfig
    from ray.train.torch import TorchTrainer

    from slate.trainers.causal_lm_lora import train_func, train_loop_config

    out_dir = os.path.join(artifacts_root, job_id)
    os.makedirs(out_dir, exist_ok=True)

    placement = req.get("_placement")
    sc = scaling_config_from_placement(req, placement)
    loop_cfg = train_loop_config(job_id, req, output_dir=out_dir)

    trainer = TorchTrainer(
        train_loop_per_worker=train_func,
        train_loop_config=loop_cfg,
        scaling_config=ScalingConfig(
            num_workers=sc["num_workers"],
            use_gpu=sc["use_gpu"],
            resources_per_worker=sc["resources_per_worker"],
        ),
        run_config=RunConfig(name=job_id, storage_path=os.path.abspath(artifacts_root)),
    )
    result = trainer.fit()

    metric = loop_cfg["metric"]
    best_metrics: Dict[str, Any] = dict(result.metrics or {}) if getattr(result, "metrics", None) else {}
    if metric not in best_metrics:
        best_metrics[metric] = float(best_metrics.get("train_loss", 0.0) or 0.0)

    ledger = {
        "job_id": job_id,
        "trial_id": "ray-0",
        "best_metrics": best_metrics,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "ray-train LoRA fine-tune",
        "placement": placement,
        "adapter_dir": out_dir,
        "model_id": loop_cfg["model_id"],
        "scaling": sc,
    }
    with open(os.path.join(out_dir, "ledger.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

    return {"best_metrics": best_metrics, "trial_id": "ray-0"}
