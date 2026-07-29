"""EDOs del problema: gravedad solar + empuje continuo + consumo de masa.

Estado x = [r (3,), v (3,), m (1,)]. Control u = [T, alpha, beta].
Unidades canonicas (D-3, ver constants.py): DU = 1 AU, TU tal que mu_sol = 1.
"""

from __future__ import annotations

import numpy as np


def equations_of_motion(
    t: float,
    state: np.ndarray,
    thrust_fn,
    isp_s: float,
    mu: float = 1.0,
) -> np.ndarray:
    """d(state)/dt para integrar con scipy.integrate.solve_ivp.

    Args:
        t: tiempo actual (unidades canonicas, TU).
        state: [rx, ry, rz, vx, vy, vz, m] (DU, DU/TU, masa canonica).
        thrust_fn: callable(t, state) -> (T, alpha, beta); T en unidades
            canonicas de fuerza.
        isp_s: impulso especifico [s], se convierte internamente a TU.
        mu: parametro gravitacional canonico (1.0 por definicion de DU/TU).

    Returns:
        d(state)/dt, mismo shape que `state`.
    """
    raise NotImplementedError("Pendiente T-1.1: implementar dinamica + validar con T-0.6.")
