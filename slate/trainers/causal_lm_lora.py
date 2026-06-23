"""causal_lm_lora — Atlas Slate trainer: LoRA fine-tune of a causal-LM on verified traces.

`slate/peft` covers conv/vision LoRA (ResNet); this is the missing transformer/causal-LM trainer
that fine-tunes a Qwen-class base on rejection-sampled VERIFIED traces. It is the entrypoint the
Atlas runner dispatches for `entrypoint == "causal_lm_lora"` (see atlas/ray_runner.py), and it
conforms to the Atlas artifact contract: it writes the LoRA adapter + `model_card.json` into the
job dir and returns `best_metrics` for `ledger.json` + the promotion gate.

Runs under Ray Train (TorchTrainer) when Ray is installed and a GPU is requested; otherwise trains
directly (CPU / single process) — so it is exercisable in CI without a cluster.

Heavy deps (torch/transformers/peft/datasets) are imported lazily inside the train path, matching
the repo convention (slate/utils/ledger.py), so importing this module never requires them — the
pure data path (`read_sft_texts`) and the model-card builder stay dependency-free + unit-testable.

Expected `req` keys (all optional except the dataset):
    train.uri / dataset.uri / SFT_PATH(env)   path to the verified SFT JSONL  (required)
    base_model                                default Qwen/Qwen2.5-Coder-7B-Instruct
    peft.r / peft.alpha                       LoRA rank/alpha (default 16 / 32)
    epochs / batch_size / lr / max_len
    resources.GPU                             >0 ⇒ try Ray Train on GPU
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List


# ── pure data path (stdlib only — unit-testable without torch/ray) ─────────────────────────────

def read_sft_texts(path: str) -> List[str]:
    """Parse a verified-trace JSONL into flat training texts. Tolerant of three shapes:
    {"text": ...} | {"input": ..., "output": ...} | {"prompt": ..., "completion": ...}."""
    texts: List[str] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            text = row.get("text")
            if not text:
                left = row.get("input") or row.get("prompt") or ""
                right = row.get("output") or row.get("completion") or ""
                text = f"{left}\n{right}".strip()
            if text:
                texts.append(text)
    return texts


def _resolve(req: Dict[str, Any]) -> Dict[str, Any]:
    peft = req.get("peft") or {}
    sft = (
        (req.get("train") or {}).get("uri")
        or (req.get("dataset") or {}).get("uri")
        or os.getenv("SFT_PATH")
    )
    if not sft:
        raise ValueError("causal_lm_lora: no SFT dataset (set req.train.uri / req.dataset.uri / SFT_PATH)")
    return {
        "base_model": req.get("base_model") or os.getenv("BASE_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct"),
        "sft_path": sft,
        "r": int(peft.get("r", os.getenv("LORA_R", 16))),
        "alpha": int(peft.get("alpha", os.getenv("LORA_ALPHA", 32))),
        "epochs": float(req.get("epochs", os.getenv("EPOCHS", 3))),
        "bs": int(req.get("batch_size", os.getenv("BATCH_SIZE", 4))),
        "lr": float(req.get("lr", os.getenv("LR", 2e-4))),
        "max_len": int(req.get("max_len", os.getenv("MAX_LEN", 1024))),
    }


def adapter_digest(adapter_dir: str) -> str:
    """Deterministic sha256 over the adapter's weight files — the identity the serving step verifies
    before loading, so a gated job's adapter cannot be swapped for a stale or poisoned one."""
    import hashlib

    h = hashlib.sha256()
    if os.path.isdir(adapter_dir):
        for fn in sorted(os.listdir(adapter_dir)):
            if fn.endswith((".safetensors", ".bin")):
                h.update(fn.encode())
                with open(os.path.join(adapter_dir, fn), "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        h.update(chunk)
    return h.hexdigest()


def build_model_card(
    job_dir: str,
    cfg: Dict[str, Any],
    metrics: Dict[str, Any],
    adapter_path: str | None = None,
    adapter_sha256: str | None = None,
) -> Dict[str, Any]:
    """Atlas model-card artifact (artifacts/<job_id>/model_card.json). adapter_path is where serving
    pulls the adapter (a JOB-SCOPED location); adapter_sha256 pins its identity for verification."""
    local_adapter = os.path.join(job_dir, "adapter")
    card = {
        "task": "generation",
        "family": "causal-lm-lora",
        "base_model": cfg["base_model"],
        "method": {"kind": "lora", "r": cfg["r"], "alpha": cfg["alpha"]},
        "dataset": {"uri": cfg["sft_path"], "examples": metrics.get("examples")},
        "metrics": metrics,
        "adapter_path": adapter_path or local_adapter,
        "adapter_sha256": adapter_sha256 if adapter_sha256 is not None else adapter_digest(local_adapter),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(os.path.join(job_dir, "model_card.json"), "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)
    return card


# ── the actual fine-tune (heavy deps imported lazily) ──────────────────────────────────────────

def _train_once(cfg: Dict[str, Any], adapter_dir: str) -> Dict[str, Any]:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"])
    model = get_peft_model(
        model,
        LoraConfig(r=cfg["r"], lora_alpha=cfg["alpha"], lora_dropout=0.05, task_type="CAUSAL_LM"),
    )
    trainable = int(sum(p.numel() for p in model.parameters() if p.requires_grad))

    texts = read_sft_texts(cfg["sft_path"])
    if not texts:
        raise ValueError(f"no usable training examples in {cfg['sft_path']}")
    ds = Dataset.from_dict({"text": texts}).map(
        lambda b: tok(b["text"], truncation=True, padding="max_length", max_length=cfg["max_len"]),
        batched=True,
        remove_columns=["text"],
    )

    args = TrainingArguments(
        output_dir=adapter_dir,
        per_device_train_batch_size=cfg["bs"],
        num_train_epochs=cfg["epochs"],
        learning_rate=cfg["lr"],
        logging_steps=5,
        save_strategy="no",
        report_to=[],
        # GPU only with real CUDA (the Ray GPU worker); off-GPU/CPU/Mac runs are pinned to CPU.
        use_cpu=not torch.cuda.is_available(),
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tok, mlm=False),
    )
    result = trainer.train()
    model.save_pretrained(adapter_dir)
    tok.save_pretrained(adapter_dir)

    loss = float(getattr(result, "training_loss", 0.0) or 0.0)
    return {"train_loss": loss, "trainable_params": trainable, "examples": len(texts)}


def _make_generate(base_model: str, adapter_dir: str | None):
    """Build a greedy generate(prompt)->text callable for the base model, optionally with a LoRA
    adapter applied — used by the held-out eval to score base+adapter and base on the same problems."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base_model)
    if adapter_dir:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_dir)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev).eval()

    def gen(prompt: str) -> str:
        ids = tok(prompt, return_tensors="pt", truncation=True, max_length=1024).to(dev)
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=256, do_sample=False, pad_token_id=tok.pad_token_id)
        return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)

    return gen


def train_causal_lm_lora(job_dir: str, req: Dict[str, Any]) -> Dict[str, Any]:
    """Atlas entrypoint. Fine-tunes the base on verified traces, writes the adapter + model_card,
    and returns best_metrics for the ledger + promotion gate. Uses Ray Train on GPU when available."""
    cfg = _resolve(req)
    adapter_dir = os.path.join(job_dir, "adapter")
    os.makedirs(adapter_dir, exist_ok=True)

    want_gpu = float((req.get("resources") or {}).get("GPU", 0) or 0) > 0
    metrics: Dict[str, Any]
    if want_gpu:
        try:
            from ray.train import ScalingConfig
            from ray.train.torch import TorchTrainer

            holder: Dict[str, Any] = {}

            def _loop(config: Dict[str, Any]) -> None:
                holder.update(_train_once(config["cfg"], config["adapter_dir"]))

            TorchTrainer(
                _loop,
                train_loop_config={"cfg": cfg, "adapter_dir": adapter_dir},
                scaling_config=ScalingConfig(num_workers=int(os.getenv("RAY_NUM_WORKERS", "1")), use_gpu=True),
            ).fit()
            metrics = holder or {"train_loss": 0.0}
        except Exception:
            # Ray/GPU path unavailable — fall back to a direct in-process train (still produces artifacts).
            metrics = _train_once(cfg, adapter_dir)
    else:
        metrics = _train_once(cfg, adapter_dir)

    # Held-out eval — score base+adapter AND base so the promotion gate can enforce promote-never-
    # demote (an adapter that doesn't beat the base on held-out pass@1 must not promote). If the eval
    # CRASHES we record the error and deliberately leave pass_at_1 / baseline_eval.json UNwritten — the
    # gate then fail-closes on the missing metric (a broken evaluator must never become a green light).
    try:
        from slate.eval.heldout_codeeval import pass_at_1

        metrics["pass_at_1"] = pass_at_1(_make_generate(cfg["base_model"], adapter_dir))
        base_score = pass_at_1(_make_generate(cfg["base_model"], None))
        metrics["base_pass_at_1"] = base_score
        # The baseline artifact the gate reads — base's held-out score under the compared metric key.
        with open(os.path.join(job_dir, "baseline_eval.json"), "w", encoding="utf-8") as f:
            json.dump({"pass_at_1": base_score}, f, indent=2)
    except Exception as e:
        metrics["eval_error"] = str(e)[:300]

    # Pin + publish: digest the adapter and, when a prefix is configured, upload it to a JOB-SCOPED
    # path so the serving step pulls exactly THIS gated job's adapter (verified by hash) — never a
    # fixed mutable prefix that could serve a stale/poisoned adapter for a passing gate.
    digest = adapter_digest(adapter_dir)
    published = adapter_dir
    prefix = os.getenv("ADAPTER_GCS_PREFIX", "").strip().rstrip("/")
    if prefix:
        import subprocess

        job_id = os.path.basename(job_dir.rstrip("/"))
        dest = f"{prefix}/{job_id}"
        try:
            subprocess.check_call(["gsutil", "-m", "cp", "-r", f"{adapter_dir}/.", dest])
            published = dest
        except Exception as e:
            metrics["publish_error"] = str(e)[:200]
    build_model_card(job_dir, cfg, metrics, adapter_path=published, adapter_sha256=digest)
    return metrics
