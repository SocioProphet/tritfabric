from __future__ import annotations

from typing import Dict
import torch


State = Dict[str, torch.Tensor]


def task_vector(base: State, tuned: State) -> State:
    """Compute tuned - base for matching keys."""
    vec: State = {}
    for k, v in tuned.items():
        if k in base and torch.is_floating_point(v) and torch.is_floating_point(base[k]):
            if v.shape == base[k].shape:
                vec[k] = (v - base[k]).detach().clone()
    return vec


def apply_task_vector(base: State, vec: State, alpha: float = 1.0) -> State:
    """Return base + alpha * vec for matching keys."""
    out: State = {}
    for k, v in base.items():
        if k in vec and torch.is_floating_point(v) and vec[k].shape == v.shape:
            out[k] = (v + float(alpha) * vec[k]).detach().clone()
        else:
            out[k] = v.detach().clone() if torch.is_tensor(v) else v
    return out
