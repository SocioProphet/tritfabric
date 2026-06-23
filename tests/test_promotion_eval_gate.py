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


def test_gate_skips_without_baseline(tmp_path):
    # No req baseline + no artifact → SKIP (can't compare), not a false block.
    report = _gate(tmp_path).run_gates("job-skip", {"metric": "pass_at_1", "mode": "max"}, {"metrics": {"pass_at_1": 0.6}})
    assert report["gates"]["eval_delta"]["reason"] == "SKIP"
