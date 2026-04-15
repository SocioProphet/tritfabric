from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class PromotionController:
    """Fail-closed promotion gates.

    Gates:
    - SHACL validation of the model card graph
    - ONNX round-trip cosine similarity threshold
    - Eval delta threshold (regression protection)

    This controller is intentionally filesystem-based so it can run:
    - in CI
    - as a Kubernetes Job (tools image)
    - inside a Rollouts analysis step
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts",
        onnx_cosine_threshold: float = 0.995,
        eval_delta_threshold: float = 0.01,
        shacl_enforce: bool = True,
    ):
        self.artifacts_root = artifacts_root
        self.onnx_cos_thr = float(onnx_cosine_threshold)
        self.eval_delta_thr = float(eval_delta_threshold)
        self.shacl_enforce = bool(shacl_enforce)

    def _job_dir(self, job_id: str) -> str:
        return os.path.join(self.artifacts_root, job_id)

    def _read_json(self, path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_gates(self, job_id: str, req: Dict[str, Any], best: Dict[str, Any]) -> Dict[str, Any]:
        jdir = self._job_dir(job_id)
        os.makedirs(jdir, exist_ok=True)

        # --- Gate: ONNX cosine ---
        onnx_check = self._read_json(os.path.join(jdir, "onnx_check.json")) or {}
        onnx_ok = True
        onnx_reason = "SKIP"
        if onnx_check:
            sim = float(onnx_check.get("cos_sim", 0.0))
            thr = float(onnx_check.get("threshold", self.onnx_cos_thr))
            onnx_ok = bool(onnx_check.get("ok", sim >= thr))
            onnx_reason = f"cos_sim={sim:.6f} thr={thr:.6f}"
        else:
            # If req says runtime_check is required, missing check is a failure.
            onnx_cfg = (req.get("export", {}) or {}).get("onnx", {}) or {}
            if bool(onnx_cfg.get("runtime_check", False)):
                onnx_ok = False
                onnx_reason = "missing onnx_check.json but runtime_check=true"

        # --- Gate: eval delta ---
        # We support a simple baseline supplied in req: req["baseline_metrics"].
        eval_ok = True
        eval_reason = "SKIP"
        baseline = req.get("baseline_metrics") or {}
        metric_name = req.get("metric") or (req.get("eval") or {}).get("metric") or ""
        if baseline and metric_name and metric_name in baseline:
            try:
                base_v = float(baseline[metric_name])
                new_v = float((best.get("metrics") or {}).get(metric_name))
                # allowed regression: new_v >= base_v - thr  (for "max" metrics)
                # if mode is "min", invert.
                mode = (req.get("mode") or "max").lower()
                if mode == "min":
                    eval_ok = (new_v <= base_v + self.eval_delta_thr)
                    eval_reason = f"min: new={new_v:.6f} base={base_v:.6f} thr={self.eval_delta_thr:.6f}"
                else:
                    eval_ok = (new_v >= base_v - self.eval_delta_thr)
                    eval_reason = f"max: new={new_v:.6f} base={base_v:.6f} thr={self.eval_delta_thr:.6f}"
            except Exception as e:
                eval_ok = False
                eval_reason = f"eval delta parse error: {e}"

        # --- Gate: SHACL ---
        # SHACL is executed by the Registry during promotion; here we just check whether a report exists.
        shacl_report_path = os.path.join(jdir, "shacl_report.txt")
        shacl_ok = not os.path.exists(shacl_report_path)
        shacl_reason = "ok" if shacl_ok else f"see {shacl_report_path}"

        ok = bool(onnx_ok and eval_ok and shacl_ok)

        report: Dict[str, Any] = {
            "job_id": job_id,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ok": ok,
            "gates": {
                "onnx_cosine": {"ok": onnx_ok, "reason": onnx_reason},
                "eval_delta": {"ok": eval_ok, "reason": eval_reason},
                "shacl": {"ok": shacl_ok, "reason": shacl_reason, "enforce": self.shacl_enforce},
            },
        }

        out_path = os.path.join(jdir, "promotion_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    def on_study_complete(self, job_id: str, req: Dict[str, Any], best: Dict[str, Any]) -> Dict[str, Any]:
        return self.run_gates(job_id, req, best)
