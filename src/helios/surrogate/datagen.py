"""Generacion masiva de tramos (estado, control, duracion) -> (estado final, masa) (T-3.2).

Particion train/val/test por region del espacio de estados (no aleatoria),
para medir generalizacion real del surrogate.
"""

from __future__ import annotations

from pathlib import Path


def generate_segments(n_segments: int, out_path: Path, seed: int) -> None:
    """Integra `n_segments` tramos aleatorios y los guarda en Parquet.

    Args:
        n_segments: cantidad de tramos a generar (objetivo: >= 1e6).
        out_path: destino Parquet (bajo data/, gitignored).
        seed: semilla (via helios.rng.get_rng) para reproducibilidad.
    """
    raise NotImplementedError("Pendiente T-3.2: pipeline paralelo de integracion.")
