from __future__ import annotations

import json
import os

from slate.eval import heldout_codeeval as hce


def test_grade_accepts_correct_rejects_wrong():
    gcd = next(p for p in hce.HELDOUT if p.name == "gcd")
    good = "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a"
    assert hce.grade(good, gcd.test) is True
    assert hce.grade("def gcd(a, b):\n    return 0", gcd.test) is False
    assert hce.grade(None, gcd.test) is False


def test_grade_cannot_be_gamed_by_stdout_or_early_exit():
    gcd = next(p for p in hce.HELDOUT if p.name == "gcd")
    # A wrong solution that prints a success marker must NOT pass (we judge by sentinel, not stdout).
    assert hce.grade('def gcd(a, b):\n    print("HIDDEN_OK")\n    return 0', gcd.test) is False
    # A solution that exits before the asserts run must NOT pass (never reaches the sentinel).
    assert hce.grade("import sys\nsys.exit(0)\ndef gcd(a, b):\n    return 0", gcd.test) is False


def test_pass_at_1_zero_without_code():
    assert hce.pass_at_1(lambda _p: "no code here, just prose") == 0.0


def test_pass_at_1_counts_solved_fraction():
    def gen(prompt: str) -> str:
        if "gcd" in prompt:
            return "```python\ndef gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n```"
        return ""
    score = hce.pass_at_1(gen)
    assert score == 1 / len(hce.HELDOUT)   # exactly one of the held-out problems solved


def _gate(tmp_path):
    from atlas.autopilot.promotion_controller import PromotionController
    return PromotionController(artifacts_root=str(tmp_path))


def test_gate_reads_baseline_artifact_and_promotes_when_adapter_beats_base(tmp_path):
    job = "job-win"
    jdir = tmp_path / job
    jdir.mkdir()
    (jdir / "baseline_eval.json").write_text(json.dumps({"pass_at_1": 0.50}))
    report = _gate(tmp_path).run_gates(
        job, {"metric": "pass_at_1", "mode": "max"}, {"metrics": {"pass_at_1": 0.75}}
    )
    assert report["gates"]["eval_delta"]["ok"] is True
    assert os.path.exists(jdir / "promotion_report.json")


def test_gate_blocks_when_adapter_worse_than_base(tmp_path):
    job = "job-regress"
    jdir = tmp_path / job
    jdir.mkdir()
    (jdir / "baseline_eval.json").write_text(json.dumps({"pass_at_1": 0.80}))
    report = _gate(tmp_path).run_gates(
        job, {"metric": "pass_at_1", "mode": "max"}, {"metrics": {"pass_at_1": 0.40}}
    )
    assert report["gates"]["eval_delta"]["ok"] is False   # promote-never-demote: refused
    assert report["ok"] is False


def test_gate_blocks_a_tie(tmp_path):
    # A tie is not an improvement — strictly-better means it must NOT promote (promote-never-demote).
    job = "job-tie"
    (tmp_path / job).mkdir()
    (tmp_path / job / "baseline_eval.json").write_text(json.dumps({"pass_at_1": 0.50}))
    report = _gate(tmp_path).run_gates(job, {"metric": "pass_at_1", "mode": "max"}, {"metrics": {"pass_at_1": 0.50}})
    assert report["gates"]["eval_delta"]["ok"] is False


def test_gate_fails_closed_when_metric_requested_but_eval_missing(tmp_path):
    # metric requested but NO baseline/new value → the eval did not run → FAIL CLOSED, not SKIP.
    report = _gate(tmp_path).run_gates("job-noeval", {"metric": "pass_at_1", "mode": "max"}, {"metrics": {"pass_at_1": 0.6}})
    assert report["gates"]["eval_delta"]["ok"] is False
    assert "missing" in report["gates"]["eval_delta"]["reason"]


def test_gate_skips_only_when_no_metric_requested(tmp_path):
    # No metric requested at all → legitimately SKIP (e.g. a non-trainer job).
    report = _gate(tmp_path).run_gates("job-nometric", {}, {"metrics": {}})
    assert report["gates"]["eval_delta"]["reason"] == "SKIP"
