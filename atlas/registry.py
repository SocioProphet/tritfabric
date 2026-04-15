from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from atlas.semantics.emit_jsonld import model_card_to_jsonld
from atlas.semantics.emit_rdf import model_card_to_turtle
from atlas.semantics.shacl_validate import validate_trial_graph_turtle


class Registry:
    """Artifact registry rooted in a filesystem directory.

    In production we may back this with object storage (S3/MinIO) and a catalog DB.
    For now, we stay local and deterministic.
    """

    def __init__(self, root: str, shacl_enforce: bool = True):
        self.root = root
        self.shacl_enforce = bool(shacl_enforce)
        os.makedirs(root, exist_ok=True)

    def _job_dir(self, job_id: str) -> str:
        return os.path.join(self.root, job_id)

    def list_artifacts(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if not os.path.isdir(self.root):
            return out
        for job_id in sorted(os.listdir(self.root)):
            jdir = self._job_dir(job_id)
            if not os.path.isdir(jdir):
                continue
            card_path = os.path.join(jdir, "model_card.json")
            if os.path.exists(card_path):
                out[job_id] = {"dir": jdir, "model_card": card_path}
        return out

    def read_ledger(self, job_id: str) -> Optional[Dict[str, Any]]:
        p = os.path.join(self._job_dir(job_id), "ledger.json")
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_onnx_check(self, job_id: str) -> Optional[Dict[str, Any]]:
        p = os.path.join(self._job_dir(job_id), "onnx_check.json")
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def promote(self, job_id: str, req: Dict[str, Any], best: Dict[str, Any]) -> Dict[str, Any]:
        """Promote a finished job into a registry artifact.

        Fail-closed behavior is controlled by `shacl_enforce`.
        """
        outdir = self._job_dir(job_id)
        os.makedirs(outdir, exist_ok=True)

        onnx_cfg = (req.get("export", {}) or {}).get("onnx", {}) or {}
        onnx_check = self._read_onnx_check(job_id) or {}

        card: Dict[str, Any] = {
            "model": {
                "id": job_id,
                "family": (req.get("entrypoint") or req.get("family") or ""),
                "task": req.get("task", ""),
                "tenant": req.get("tenant", "default"),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "data": {
                "train_uri": ((req.get("train") or {}) or {}).get("uri", ""),
                "val_uri": ((req.get("val") or {}) or {}).get("uri", ""),
                "dataset_hash": req.get("dataset_hash", "unknown"),
            },
            "metrics": (best.get("metrics") or {}),
            "onnx": {
                "path": onnx_cfg.get("path", ""),
                "opset": onnx_cfg.get("opset"),
                "providers": onnx_cfg.get("providers", []),
                "cos_sim": onnx_check.get("cos_sim"),
                "threshold": onnx_check.get("threshold"),
                "ok": onnx_check.get("ok"),
            },
            "policy_ref": req.get("policy_ref"),
        }

        # Persist JSON model card
        with open(os.path.join(outdir, "model_card.json"), "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2, sort_keys=False)

        # JSON-LD
        card_jsonld = model_card_to_jsonld(card, context_url="api/jsonld/math_context.jsonld")
        with open(os.path.join(outdir, "model_card.jsonld"), "w", encoding="utf-8") as f:
            json.dump(card_jsonld, f, indent=2, sort_keys=False)

        # Turtle graph + SHACL validation
        turtle = model_card_to_turtle(card)
        ttl_path = os.path.join(outdir, "model_card.ttl")
        with open(ttl_path, "w", encoding="utf-8") as f:
            f.write(turtle)

        conforms, report = validate_trial_graph_turtle(
            turtle=turtle,
            shapes_path="api/shapes/model_shapes.ttl",
            ontology_path=None,
        )

        if not conforms:
            report_path = os.path.join(outdir, "shacl_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            msg = f"SHACL validation failed for job {job_id}. Report written to {report_path}"
            if self.shacl_enforce:
                raise ValueError(msg + "\n" + report)
            logging.warning(msg)

        return card
