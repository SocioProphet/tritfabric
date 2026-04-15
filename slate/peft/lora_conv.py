from __future__ import annotations

from typing import Optional
import torch
import torch.nn as nn


class LoRAConv2d(nn.Module):
    """LoRA adapter for Conv2d.

    Implementation: base Conv2d + (alpha/r) * B(A(x))
    where:
      A: 1x1 conv reduces channels to rank r
      B: kxk conv projects back to out_channels

    This is a pragmatic adapter; not the only possible conv-LoRA design.
    """

    def __init__(self, base: nn.Conv2d, r: int = 8, alpha: float = 16.0):
        super().__init__()
        if r <= 0:
            raise ValueError("r must be > 0")
        self.base = base
        self.r = int(r)
        self.alpha = float(alpha)
        self.scaling = self.alpha / float(self.r)

        self.A = nn.Conv2d(base.in_channels, self.r, kernel_size=1, bias=False)
        self.B = nn.Conv2d(
            self.r,
            base.out_channels,
            kernel_size=base.kernel_size,
            stride=base.stride,
            padding=base.padding,
            dilation=base.dilation,
            groups=base.groups,
            bias=False,
        )

        # Init: A small, B zeros (common LoRA convention)
        nn.init.kaiming_uniform_(self.A.weight, a=5**0.5)
        nn.init.zeros_(self.B.weight)

    def forward(self, x):
        return self.base(x) + self.scaling * self.B(self.A(x))


def add_lora_to_resblock_tail(block: nn.Module, r: int = 8, alpha: float = 16.0) -> nn.Module:
    """Patch a torchvision-style ResNet BasicBlock/Bottleneck by LoRA-wrapping its last conv.

    This function is intentionally conservative: it only looks for `conv2` or `conv3`.
    """
    if hasattr(block, "conv3"):
        block.conv3 = LoRAConv2d(block.conv3, r=r, alpha=alpha)  # type: ignore
    elif hasattr(block, "conv2"):
        block.conv2 = LoRAConv2d(block.conv2, r=r, alpha=alpha)  # type: ignore
    else:
        raise ValueError("block has no conv2/conv3")
    return block
