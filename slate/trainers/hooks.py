from __future__ import annotations

from typing import Any, Dict, Optional

import torch.nn as nn

from slate.peft.lora_conv import add_lora_to_resblock_tail
from slate.peft.ia3_conv import add_ia3_to_conv


def apply_peft(model: nn.Module, peft: Optional[Dict[str, Any]] = None) -> nn.Module:
    """Apply parameter-efficient fine-tuning (PEFT) adapters.

    Supported:
    - lora_conv_tail: LoRA wrapping of the tail conv in ResNet blocks
    - ia3_conv: IA3 multiplicative gates on Conv2d outputs
    """
    peft = peft or {}
    kind = str(peft.get("kind", "")).lower()

    if kind in ("", "none"):
        return model

    if kind == "lora_conv_tail":
        r = int(peft.get("r", 8))
        alpha = float(peft.get("alpha", 16.0))
        # Patch common ResNet patterns: layer1..layer4 blocks
        for layer_name in ("layer1", "layer2", "layer3", "layer4"):
            if hasattr(model, layer_name):
                layer = getattr(model, layer_name)
                for b in layer:
                    add_lora_to_resblock_tail(b, r=r, alpha=alpha)
        return model

    if kind == "ia3_conv":
        return add_ia3_to_conv(model)

    raise ValueError(f"unknown peft kind: {kind}")


def freeze_base_params(model: nn.Module) -> None:
    """Freeze all parameters except adapters (heuristic)."""
    for n, p in model.named_parameters():
        # Allow LoRA/IA3 params to train
        if any(tag in n.lower() for tag in ("a.weight", "b.weight", "gate")):
            p.requires_grad = True
        else:
            p.requires_grad = False
