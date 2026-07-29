"""Wrappers de NLP local: SLSQP (scipy) primero, IPOPT (cyipopt) despues (T-1.3/T-1.6)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def solve_slsqp(
    objective: Callable[[np.ndarray], float],
    constraints: list,
    x0: np.ndarray,
) -> np.ndarray:
    """Resuelve el NLP con scipy.optimize.minimize(method="SLSQP").

    Args:
        objective: funcion de costo (p.ej. -m_f) sobre el vector de control.
        constraints: lista de dicts estilo scipy (matching, rendezvous).
        x0: semilla inicial.

    Returns:
        Vector de control optimo.
    """
    raise NotImplementedError("Pendiente T-1.3: validar gradientes por diferencias finitas.")


def solve_ipopt(
    objective: Callable[[np.ndarray], float],
    constraints: list,
    x0: np.ndarray,
) -> np.ndarray:
    """Igual que solve_slsqp pero via cyipopt (flag --solver=ipopt, T-1.6)."""
    raise NotImplementedError("Pendiente T-1.6: activar cuando SLSQP se quede corto.")
