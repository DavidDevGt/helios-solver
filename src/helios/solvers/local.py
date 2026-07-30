"""Wrappers de NLP local: SLSQP (scipy) primero, IPOPT (cyipopt) despues (T-1.3/T-1.6)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.optimize import minimize


def solve_slsqp(
    objective: Callable[[np.ndarray], float],
    constraints: list,
    x0: np.ndarray,
    *,
    bounds: list[tuple[float, float]] | None = None,
    options: dict | None = None,
) -> np.ndarray:
    """Resuelve el NLP con scipy.optimize.minimize(method="SLSQP").

    Args:
        objective: funcion de costo (p.ej. -m_f) sobre el vector de control.
        constraints: lista de dicts estilo scipy (matching, rendezvous),
            cada uno con al menos {"type": "eq"|"ineq", "fun": ...}.
        x0: semilla inicial.
        bounds: limites por variable (p.ej. 0 <= T <= T_max), opcional.
        options: pasado directo a scipy (maxiter, ftol, ...).

    Returns:
        Vector de control optimo.
    """
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        constraints=constraints,
        bounds=bounds,
        options=options,
    )
    if not result.success:
        raise RuntimeError(f"SLSQP no convergio: {result.message}")
    return result.x


def solve_ipopt(
    objective: Callable[[np.ndarray], float],
    constraints: list,
    x0: np.ndarray,
) -> np.ndarray:
    """Igual que solve_slsqp pero via cyipopt (flag --solver=ipopt, T-1.6)."""
    raise NotImplementedError("Pendiente T-1.6: activar cuando SLSQP se quede corto.")
