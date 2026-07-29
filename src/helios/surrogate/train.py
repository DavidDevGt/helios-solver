"""Entrenamiento del SegmentMLP (T-3.3).

Criterio de aceptacion: error mediano < 1% en masa consumida sobre el
held-out set; reportar tambien p99, no solo la media.
"""

from __future__ import annotations

from pathlib import Path


def train(train_parquet: Path, val_parquet: Path, epochs: int = 100) -> Path:
    """Entrena el modelo y devuelve la ruta al checkpoint guardado."""
    raise NotImplementedError("Pendiente T-3.3: requiere datagen.py (T-3.2) primero.")
