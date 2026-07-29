"""Estado (posicion, velocidad) de los cuerpos del sistema solar.

Pendiente D-1 (PLAN.md sec. 1): backend por pykep o hapsira+jplephem.
Unidades de salida: posicion en km, velocidad en km/s, en el marco
ecliptico J2000 heliocentrico.
"""

from __future__ import annotations

import datetime as dt

import numpy as np


def state_vector(body: str, epoch: dt.datetime) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (r, v) de `body` en `epoch`.

    Args:
        body: nombre del cuerpo ("earth", "mars").
        epoch: fecha/hora UTC.

    Returns:
        r: posicion heliocentrica [km], shape (3,).
        v: velocidad heliocentrica [km/s], shape (3,).
    """
    raise NotImplementedError("Pendiente T-0.2/T-0.4: elegir backend (D-1) e implementar.")
