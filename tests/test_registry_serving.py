from __future__ import annotations

import json


def test_registry_carries_adapter_into_serving_block(tmp_path, monkeypatch):
    """On promote, the trainer's base_model + adapter_path must survive into card['serving'] so
    stage-4 serving (vllm --enable-lora) can find and load the promoted adapter."""
    import atlas.registry as reg

    # Stub the RDF/SHACL emitters so the test focuses on the serving carry-over (no rdflib/pyshacl).
    monkeypatch.setattr(reg, "model_card_to_jsonld", lambda c, **k: {})
    monkeypatch.setattr(reg, "model_card_to_turtle", lambda c: "")
    monkeypatch.setattr(reg, "validate_trial_graph_turtle", lambda **k: (True, ""))

    r = reg.Registry(root=str(tmp_path))
    jdir = tmp_path / "jobX"
    jdir.mkdir()
    adapter = str(jdir / "adapter")
    # The trainer's model_card.json (written before promote overwrites it).
    (jdir / "model_card.json").write_text(
        json.dumps({"base_model": "Qwen/Qwen2.5-Coder-7B-Instruct", "adapter_path": adapter, "method": {"kind": "lora", "r": 16}})
    )

    card = r.promote(
        "jobX",
        {"tenant": "noetica", "entrypoint": "causal_lm_lora", "task": "generation"},
        {"metrics": {"pass_at_1": 0.7}},
    )

    sv = card["serving"]
    assert sv["engine"] == "vllm"
    assert sv["base_model"] == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert sv["adapter_path"] == adapter
    assert sv["served_model_id"] == "noetica-lora-jobX"
    # and it's persisted in the rewritten card
    persisted = json.loads((jdir / "model_card.json").read_text())
    assert persisted["serving"]["adapter_path"] == adapter
