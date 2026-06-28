"""Proofs for the WS-A LoRA trainer's PURE logic — runs without torch/ray/GPU.

The heavy training path (train_func) is exercised on real hardware in WS-A; here we lock down the decisions that
must be right BEFORE any GPU spins up: adapter targeting, config normalization, dataset formatting, and the
Ray ScalingConfig derived from the brokered placement.
"""
from atlas.gpu_broker import plan_cheapest
from atlas.ray_train_lora import gpu_count_from_req, scaling_config_from_placement
from slate.trainers.causal_lm_lora import (
    build_lora_config_dict,
    default_target_modules,
    format_example,
    train_loop_config,
)


def test_target_modules_by_arch():
    assert "gate_proj" in default_target_modules("Qwen/Qwen2.5-7B")
    assert "gate_proj" in default_target_modules("meta-llama/Llama-3.3-70B")
    assert default_target_modules("some-unknown-model") == ["q_proj", "k_proj", "v_proj", "o_proj"]


def test_lora_config_defaults_and_overrides():
    cfg = build_lora_config_dict({"model": "Qwen/Qwen2.5-7B"})
    assert cfg["r"] == 16 and cfg["lora_alpha"] == 32 and cfg["task_type"] == "CAUSAL_LM"
    cfg2 = build_lora_config_dict({"model": "x", "lora": {"r": 8, "alpha": 64, "target_modules": ["q_proj"]}})
    assert cfg2["r"] == 8 and cfg2["lora_alpha"] == 64 and cfg2["target_modules"] == ["q_proj"]


def test_lora_rank_must_be_positive():
    try:
        build_lora_config_dict({"lora": {"r": 0}})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_format_example_variants():
    assert format_example({"text": "hello"}) == "hello"
    assert format_example({"prompt": "Q: ", "completion": "A"}) == "Q: A"
    out = format_example({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]})
    assert "<|user|>" in out and "hi" in out and "yo" in out


def test_scaling_config_matches_broker_placement():
    # broker the cheapest 2×H100, then make sure the trainer asks Ray for 2 GPU workers
    req = {"gpu": {"type": "H100", "count": 2}, "hours": 18, "exclude_local": True}
    placement = plan_cheapest(req)
    assert placement is not None
    sc = scaling_config_from_placement(req, placement)
    assert sc["num_workers"] == 2
    assert sc["use_gpu"] is True
    assert sc["resources_per_worker"]["GPU"] == 1
    assert sc["resources_per_worker"]["CPU"] == placement["worker_group"]["cpu"]


def test_gpu_count_defaults_to_one():
    assert gpu_count_from_req({}) == 1
    assert gpu_count_from_req({"gpu": {"count": 4}}) == 4


def test_train_loop_config_threads_request_through():
    cfg = train_loop_config("job-123", {"model": "Qwen/Qwen2.5-7B", "max_steps": 50, "dataset_path": "/x.jsonl"}, "/out")
    assert cfg["job_id"] == "job-123" and cfg["max_steps"] == 50
    assert cfg["output_dir"] == "/out" and cfg["model_id"] == "Qwen/Qwen2.5-7B"
    assert cfg["lora"]["task_type"] == "CAUSAL_LM"
