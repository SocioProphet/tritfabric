from __future__ import annotations

import torch
import torch.nn as nn


class IA3Gate2d(nn.Module):
    """IA³-style multiplicative gate for Conv2d outputs.

    Gate is a per-output-channel scale initialized to 1.0.
    Forward: y = conv(x) * gate
    """

    def __init__(self, conv: nn.Conv2d):
        super().__init__()
        self.conv = conv
        self.gate = nn.Parameter(torch.ones(1, conv.out_channels, 1, 1))

    def forward(self, x):
        return self.conv(x) * self.gate


def add_ia3_to_conv(module: nn.Module) -> nn.Module:
    """Replace Conv2d modules with IA3-wrapped versions."""
    for name, child in list(module.named_children()):
        if isinstance(child, nn.Conv2d):
            setattr(module, name, IA3Gate2d(child))
        else:
            add_ia3_to_conv(child)
    return module
