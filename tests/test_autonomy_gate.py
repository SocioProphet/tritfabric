from __future__ import annotations

import json
import os

import pytest

import atlas.registry as registry_mod
from atlas.autonomy_gate import AutonomyGate, check_promotion_autonomy
from atlas.registry import Registry


def test_gate_admits_when_evidence_present():
    gate = AutonomyGate.from_file()
    decision = gate.evaluate("L4", ["conductor_response_envelope"])
    assert decision.ok
    assert decision.granted_level == "L4"


def test_gate_blocks_and_reports_ceiling_when_evidence_absent():
    gate = AutonomyGate.from_file()
    decision = gate.evaluate("L5", ["trail_log"])  # only supports L1
    assert not decision.ok
    assert decision.granted_level == "L1"
    assert "supports up to L1" in decision.reason


def test_l0_always_admissible():
    gate = AutonomyGate.from_file()
    assert gate.evaluate("L0", []).ok


def test_ceiling_reports_highest_with_noncontiguous_evidence():
    # An L4 token without lower-level tokens must report a ceiling of L4,
    # consistent with evaluate("L4", [L4-token]) admitting directly.
    gate = AutonomyGate.from_file()
    assert gate.evaluate("L4", ["conductor_response_envelope"]).ok
    blocked = gate.evaluate("L5", ["conductor_response_envelope"])
    assert not blocked.ok
    assert blocked.granted_level == "L4"
    assert "supports up to L4" in blocked.reason


def test_bare_string_evidence_is_coerced():
    # A single evidence token passed as a str (not a list) must still match.
    decision = check_promotion_autonomy({"autonomy": {"requested_level": "L1", "evidence": "trail_log"}})
    assert decision is not None
    assert decision.ok
    assert decision.granted_level == "L1"


def test_check_promotion_autonomy_noop_without_block():
    assert check_promotion_autonomy({"entrypoint": "demo"}) is None


def _req(**overrides):
    req = {
        "entrypoint": "demo-model",
        "task": "classification",
        "tenant": "default",
        "train": {"uri": "s3://example/train.parquet"},
        "val": {"uri": "s3://example/val.parquet"},
        "dataset_hash": "sha256:demo",
        "mathType": ["algebraic"],
        "calcOps": ["linear"],
        "artifactRef": "s3://example/model.onnx",
        "export": {"onnx": {"path": "s3://example/model.onnx", "opset": 17, "providers": ["CPUExecutionProvider"]}},
    }
    req.update(overrides)
    return req


def test_promote_blocks_on_autonomy_when_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_mod, "validate_trial_graph_turtle", lambda **kwargs: (True, "ok"))
    reg = Registry(str(tmp_path), shacl_enforce=True)
    req = _req(autonomy={"requested_level": "L5", "evidence": ["trail_log"]})
    with pytest.raises(ValueError, match="Autonomy gate blocked"):
        reg.promote("job-overclaim", req, {"metrics": {"accuracy": 0.9}})


def test_promote_stamps_autonomy_on_card_when_admitted(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_mod, "validate_trial_graph_turtle", lambda **kwargs: (True, "ok"))
    reg = Registry(str(tmp_path), shacl_enforce=True)
    req = _req(autonomy={"requested_level": "L4", "evidence": ["conductor_response_envelope"]})
    card = reg.promote("job-ok", req, {"metrics": {"accuracy": 0.9}})
    assert card["autonomy"]["ok"] is True
    assert card["autonomy"]["granted_level"] == "L4"
    on_disk = json.loads((tmp_path / "job-ok" / "model_card.json").read_text(encoding="utf-8"))
    assert on_disk["autonomy"]["granted_level"] == "L4"
