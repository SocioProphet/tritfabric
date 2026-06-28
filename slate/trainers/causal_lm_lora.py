"""Causal-LM LoRA/QLoRA fine-tuning loop — the REAL trainer under WS-A.

This is the worker-side training function executed by Ray Train (see ``atlas/ray_train_lora.py``), plus the pure
helpers that decide adapter targets / config. The heavy ML deps (torch/transformers/peft/trl/datasets) are imported
LAZILY inside ``train_func`` so this module imports cleanly on a control plane that has none of them installed —
the pure helpers stay unit-testable without a GPU.

Pipeline (standard, sovereign-portable LoRA stack):
  AutoModelForCausalLM (optional 4-bit) → PEFT LoraConfig → TRL SFTTrainer (or HF Trainer fallback)
  → Ray Train reports loss each step → adapter saved to the run dir.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Per-architecture LoRA attachment points. Keys matched as substrings of the (lowercased) model id.
# Covers the open-weights families the choir actually fields; falls back to attention projections otherwise.
_TARGET_MODULES_BY_ARCH: Dict[str, List[str]] = {
    "llama": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "qwen": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "mistral": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "mixtral": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "gemma": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "phi": ["q_proj", "k_proj", "v_proj", "dense", "fc1", "fc2"],
    "gpt": ["c_attn", "c_proj", "c_fc"],
}
_DEFAULT_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]


def default_target_modules(model_id: str) -> List[str]:
    """Pick sensible LoRA target modules for the model family (pure; no torch)."""
    mid = (model_id or "").lower()
    for arch, mods in _TARGET_MODULES_BY_ARCH.items():
        if arch in mid:
            return list(mods)
    return list(_DEFAULT_TARGET_MODULES)


def build_lora_config_dict(req: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the job's LoRA knobs into a peft.LoraConfig kwargs dict (pure; validates ranges)."""
    lora = (req.get("lora") or {}) if isinstance(req.get("lora"), dict) else {}
    r = int(lora.get("r", req.get("lora_rank", 16)))
    if r <= 0:
        raise ValueError("lora.r must be > 0")
    alpha = int(lora.get("alpha", r * 2))
    dropout = float(lora.get("dropout", 0.05))
    targets = lora.get("target_modules") or default_target_modules(str(req.get("model") or req.get("model_id") or ""))
    return {
        "r": r,
        "lora_alpha": alpha,
        "lora_dropout": dropout,
        "target_modules": list(targets),
        "bias": "none",
        "task_type": "CAUSAL_LM",
    }


def format_example(ex: Dict[str, Any]) -> str:
    """Render one dataset row to a training string (pure).

    Accepts {text}, {prompt, completion}, or {messages:[{role,content}...]}.
    """
    if isinstance(ex.get("text"), str):
        return ex["text"]
    if "messages" in ex and isinstance(ex["messages"], list):
        parts = []
        for m in ex["messages"]:
            role = str(m.get("role", "user"))
            content = str(m.get("content", ""))
            parts.append(f"<|{role}|>\n{content}")
        return "\n".join(parts) + "\n<|end|>"
    prompt = str(ex.get("prompt", ""))
    completion = str(ex.get("completion", ex.get("response", "")))
    return f"{prompt}{completion}"


def train_loop_config(job_id: str, req: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """Assemble the config dict handed to each Ray Train worker (pure)."""
    return {
        "job_id": job_id,
        "model_id": str(req.get("model") or req.get("model_id") or "Qwen/Qwen2.5-7B"),
        "dataset_path": req.get("dataset_path") or req.get("dataset"),
        "output_dir": output_dir,
        "lora": build_lora_config_dict(req),
        "max_steps": int(req.get("max_steps", 100)),
        "learning_rate": float(req.get("learning_rate", 2e-4)),
        "per_device_batch_size": int(req.get("batch_size", 1)),
        "grad_accum": int(req.get("grad_accum", 8)),
        "max_seq_len": int(req.get("max_seq_len", 2048)),
        "load_in_4bit": bool(req.get("load_in_4bit", True)),
        "bf16": bool(req.get("bf16", True)),
        "metric": str(req.get("metric") or "train_loss"),
    }


def train_func(config: Dict[str, Any]) -> None:
    """Ray Train per-worker training function. Heavy imports are deferred to here on purpose.

    Runs a LoRA/QLoRA SFT pass and reports metrics through Ray Train each logging step; saves the adapter to
    ``config['output_dir']``. Raises (so the orchestrator can fall back) if the ML stack is absent.
    """
    import os

    import torch  # noqa: F401
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    import ray.train

    model_id = config["model_id"]
    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    quant_args: Dict[str, Any] = {}
    if config["load_in_4bit"]:
        try:
            from transformers import BitsAndBytesConfig

            quant_args["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16 if config["bf16"] else torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        except Exception:
            pass  # bitsandbytes unavailable → full-precision LoRA

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if config["bf16"] else torch.float16,
        **quant_args,
    )
    if config["load_in_4bit"] and "quantization_config" in quant_args:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(**config["lora"]))

    # Dataset: jsonl with text/prompt+completion/messages → tokenized blocks.
    ds_path = config["dataset_path"]
    if not ds_path or not os.path.exists(ds_path):
        raise FileNotFoundError(f"dataset_path missing or not found: {ds_path!r}")
    raw = load_dataset("json", data_files=ds_path, split="train")

    def _tok(batch: Dict[str, Any]) -> Dict[str, Any]:
        texts = [format_example(dict(zip(batch.keys(), vals))) for vals in zip(*batch.values())]
        return tok(texts, truncation=True, max_length=config["max_seq_len"])

    tokenized = raw.map(_tok, batched=True, remove_columns=raw.column_names)
    collator = DataCollatorForLanguageModeling(tok, mlm=False)

    args = TrainingArguments(
        output_dir=config["output_dir"],
        max_steps=config["max_steps"],
        learning_rate=config["learning_rate"],
        per_device_train_batch_size=config["per_device_batch_size"],
        gradient_accumulation_steps=config["grad_accum"],
        bf16=config["bf16"],
        logging_steps=1,
        save_strategy="no",
        report_to=[],
    )
    trainer = Trainer(model=model, args=args, train_dataset=tokenized, data_collator=collator)

    # Bridge HF logs → Ray Train reports so the driver sees per-step metrics.
    try:
        from ray.train.huggingface.transformers import RayTrainReportCallback, prepare_trainer

        trainer.add_callback(RayTrainReportCallback())
        trainer = prepare_trainer(trainer)
    except Exception:
        pass  # standalone (non-Ray) execution still trains; just no live reporting

    result = trainer.train()
    model.save_pretrained(config["output_dir"])  # adapter only (LoRA)
    tok.save_pretrained(config["output_dir"])

    final = {config["metric"]: float(getattr(result, "training_loss", 0.0) or 0.0)}
    try:
        ray.train.report(final)
    except Exception:
        pass
