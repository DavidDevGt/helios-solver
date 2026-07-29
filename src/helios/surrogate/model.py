"""MLP baseline (PyTorch) para predecir costo/factibilidad de un tramo (T-3.3).

Entrada: ~14 floats (estado inicial normalizado, control, duracion).
Salida: 7 floats (estado final, masa consumida).
"""

from __future__ import annotations

import torch
from torch import nn


class SegmentMLP(nn.Module):
    """MLP modesto; entrenar antes de considerar arquitecturas mas grandes."""

    def __init__(self, in_dim: int = 14, out_dim: int = 7, hidden: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
