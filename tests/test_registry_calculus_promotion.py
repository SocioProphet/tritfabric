from __future__ import annotations

import json
import os

import pytest

import atlas.registry as registry_mod
from atlas.registry import Registry


def _req(**overrides):
    req = {
        "entrypoint": "demo-model",
        "task": "classification",
        "tenant": "default",
        "train": {"uri": "s3://example/train.parquet"},
        "val": {"uri": "s3://example/val.parquet"},
        "dataset_hash": "sha256:demo",
        "mathType": ["algebraic", "optimization"],
        "calcOps": ["linear", "softmax"],
        "artifactRef": "s3://example/model.onnx",
        "export": {"onnx": {"path": "s3://example/model.onnx", "opset": 17, "providers": ["CPUExecutionProvider"]}},
    }
    req.update(overrides)
    return req


def _write_ledger(root, job_id="job-valid"):
    os.makedirs(os.path.join(root, job_id), exist_ok=True)
    with open(os.path.join(root, job_id, "ledger.json"), "w", encoding="utf-8") as f:
        json.dump({"params": 10, "flops": 20}, f)


def test_registry_promote_writes_calculus_model_card(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_mod, "validate_trial_graph_turtle", lambda **kwargs: (True, "ok"))
    _write_ledger(tmp_path, "job-valid")
    reg = Registry(str(tmp_path), shacl_enforce=True)

    card = reg.promote("job-valid", _req(), {"metrics": {"accuracy": 0.9}})

    assert card["mathType"] == ["algebraic", "optimization"]
    assert card["calcOps"] == ["linear", "softmax"]
    assert card["ledgerRef"].endswith("ledger.json")
    assert card["artifactRef"] == "s3://example/model.onnx"
    assert os.path.exists(tmp_path / "job-valid" / "model_card.json")
    assert os.path.exists(tmp_path / "job-valid" / "model_card.jsonld")
    assert os.path.exists(tmp_path / "job-valid" / "model_card.ttl")

    ttl = (tmp_path / "job-valid" / "model_card.ttl").read_text(encoding="utf-8")
    assert "mathType" in ttl
    assert "calcOps" in ttl
    assert "ledgerRef" in ttl
    assert "artifactRef" in ttl


def test_registry_promote_blocks_when_shacl_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_mod, "validate_trial_graph_turtle", lambda **kwargs: (False, "missing mathType"))
    reg = Registry(str(tmp_path), shacl_enforce=True)

    with pytest.raises(ValueError, match="SHACL validation failed"):
        reg.promote("job-invalid", _req(mathType=[], calcOps=[]), {"metrics": {"accuracy": 0.9}})

    assert os.path.exists(tmp_path / "job-invalid" / "shacl_report.txt")


def test_registry_promote_warns_when_shacl_not_enforced(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(registry_mod, "validate_trial_graph_turtle", lambda **kwargs: (False, "missing mathType"))
    reg = Registry(str(tmp_path), shacl_enforce=False)

    with caplog.at_level("WARNING"):
        card = reg.promote("job-warn", _req(mathType=[], calcOps=[]), {"metrics": {"accuracy": 0.9}})

    assert card["model"]["id"] == "job-warn"
    assert os.path.exists(tmp_path / "job-warn" / "model_card.json")
    assert os.path.exists(tmp_path / "job-warn" / "model_card.jsonld")
    assert os.path.exists(tmp_path / "job-warn" / "shacl_report.txt")
    assert any("SHACL validation failed for job job-warn" in rec.message for rec in caplog.records)
