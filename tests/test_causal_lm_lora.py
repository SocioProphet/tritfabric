from __future__ import annotations

import json
import os

import pytest

from slate.trainers import causal_lm_lora as clm


def _write_jsonl(tmp_path, rows):
    p = tmp_path / "verified.sft.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(p)


def test_read_sft_texts_handles_three_shapes(tmp_path):
    path = _write_jsonl(
        tmp_path,
        [
            {"text": "pre-formatted"},
            {"input": "Q", "output": "A"},
            {"prompt": "P", "completion": "C"},
            {},  # no usable content → skipped
        ],
    )
    texts = clm.read_sft_texts(path)
    assert texts == ["pre-formatted", "Q\nA", "P\nC"]


def test_resolve_requires_dataset(monkeypatch):
    monkeypatch.delenv("SFT_PATH", raising=False)
    with pytest.raises(ValueError):
        clm._resolve({"base_model": "x"})


def test_resolve_reads_train_uri_and_peft(tmp_path):
    cfg = clm._resolve(
        {"train": {"uri": "/data/v.jsonl"}, "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct", "peft": {"r": 8, "alpha": 16}}
    )
    assert cfg["sft_path"] == "/data/v.jsonl"
    assert cfg["r"] == 8 and cfg["alpha"] == 16


def test_build_model_card_writes_contract(tmp_path):
    cfg = {"base_model": "B", "sft_path": "/d.jsonl", "r": 16, "alpha": 32}
    card = clm.build_model_card(str(tmp_path), cfg, {"train_loss": 0.5, "examples": 3})
    assert card["task"] == "generation" and card["family"] == "causal-lm-lora"
    assert card["method"] == {"kind": "lora", "r": 16, "alpha": 32}
    on_disk = json.loads((tmp_path / "model_card.json").read_text())
    assert on_disk["base_model"] == "B" and on_disk["metrics"]["examples"] == 3


def test_runner_dispatches_causal_lm_lora(tmp_path, monkeypatch):
    """_run_with_ray(entrypoint=causal_lm_lora) runs the trainer + writes ledger.json with real
    metrics, instead of the deterministic _run_local placeholder."""
    from atlas.ray_runner import RayRunner

    monkeypatch.setattr(
        clm, "train_causal_lm_lora", lambda job_dir, req: {"train_loss": 0.123, "examples": 5}
    )
    runner = RayRunner(artifacts_root=str(tmp_path))
    out = runner._run_with_ray("job-1", {"entrypoint": "causal_lm_lora"})

    assert out["best_metrics"]["train_loss"] == 0.123
    ledger = json.loads((tmp_path / "job-1" / "ledger.json").read_text())
    assert ledger["best_metrics"]["examples"] == 5
    assert "causal_lm_lora" in ledger["note"]


def test_runner_unknown_entrypoint_falls_back_local(tmp_path):
    from atlas.ray_runner import RayRunner

    runner = RayRunner(artifacts_root=str(tmp_path))
    out = runner._run_with_ray("job-2", {"entrypoint": "toy", "metric": "val_score", "mode": "max"})
    # local fallback still produces a ledger + a (deterministic) metric
    assert "best_metrics" in out
    assert os.path.exists(tmp_path / "job-2" / "ledger.json")
