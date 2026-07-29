"""Generadores aleatorios con semilla fija (T-0.8).

Toda fuente de aleatoriedad del proyecto (multi-start, datagen del
surrogate) debe pasar por aqui para que las corridas sean reproducibles
bit-a-bit entre ejecuciones de CI.
"""

import numpy as np

DEFAULT_SEED = 42


def get_rng(seed: int = DEFAULT_SEED) -> np.random.Generator:
    """Crea un generador NumPy (PCG64) con semilla fija."""
    return np.random.default_rng(seed)
