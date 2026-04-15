from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn.functional as F


def softmax_T(logits: torch.Tensor, T: float) -> torch.Tensor:
    return F.softmax(logits / float(T), dim=-1)


def kl_div_T(student_logits: torch.Tensor, teacher_logits: torch.Tensor, T: float, topk: Optional[int] = None) -> torch.Tensor:
    """KL( teacher || student ) with temperature T.

    If topk is set, we compute KL only on top-k teacher probabilities (renormalized).
    """
    T = float(T)
    t = softmax_T(teacher_logits, T)
    s_log = F.log_softmax(student_logits / T, dim=-1)

    if topk is not None and topk > 0 and topk < t.shape[-1]:
        vals, idx = torch.topk(t, k=int(topk), dim=-1)
        t = vals / (vals.sum(dim=-1, keepdim=True) + 1e-12)
        s_log = torch.gather(s_log, dim=-1, index=idx)

    return F.kl_div(s_log, t, reduction="batchmean") * (T * T)


def adaptive_temperature(teacher_logits: torch.Tensor, Tmin: float = 1.0, Tmax: float = 8.0) -> torch.Tensor:
    """Compute a per-sample temperature based on teacher entropy.

    High-entropy teacher => higher temperature (softer targets).
    Low-entropy teacher => lower temperature.
    """
    p = F.softmax(teacher_logits, dim=-1)
    ent = -(p * (p + 1e-12).log()).sum(dim=-1)  # [batch]
    ent_norm = ent / (ent.max().detach() + 1e-12)
    T = Tmin + (Tmax - Tmin) * ent_norm
    return T.detach()


def kd_loss(
    student_logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    hard_labels: Optional[torch.Tensor] = None,
    alpha: float = 0.5,
    T: float = 4.0,
    topk: Optional[int] = None,
    adaptive_T: bool = False,
) -> torch.Tensor:
    """Knowledge distillation loss.

    L = alpha * KL_T + (1-alpha) * CE_hard
    """
    if adaptive_T:
        Ts = adaptive_temperature(teacher_logits, Tmin=max(1.0, T/2), Tmax=max(2.0, T*2))
        # average KL across batch with per-sample T
        kls = []
        for i in range(student_logits.shape[0]):
            kls.append(kl_div_T(student_logits[i:i+1], teacher_logits[i:i+1], float(Ts[i].item()), topk=topk))
        kd = torch.stack(kls).mean()
    else:
        kd = kl_div_T(student_logits, teacher_logits, float(T), topk=topk)

    if hard_labels is None:
        return kd

    ce = F.cross_entropy(student_logits, hard_labels)
    return float(alpha) * kd + (1.0 - float(alpha)) * ce
