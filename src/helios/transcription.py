"""Transcripcion directa del control continuo (Sims-Flanagan, T-1.2).

Discretiza el arco en N segmentos de empuje constante e impone matching
(continuidad de estado) en el punto medio de cada segmento: se propaga
hacia adelante desde el estado inicial a traves de la primera mitad de
segmentos, hacia atras desde el estado final a traves de la segunda
mitad, y el defecto es la diferencia de estado en el punto de encuentro.
Todo en unidades canonicas (D-3); ver dynamics.py para la convencion de
control y de unidades de empuje/masa.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .dynamics import equations_of_motion

PROPAGATION_RTOL = 1e-10
PROPAGATION_ATOL = 1e-12


def _propagate_segment(
    state: np.ndarray,
    control: np.ndarray,
    duration_tu: float,
    isp_s: float,
    mu: float,
) -> np.ndarray:
    """Integra un segmento de empuje constante; `duration_tu` < 0 propaga
    hacia atras (scipy integra con normalidad un t_span decreciente)."""
    thrust, alpha, beta = control

    def thrust_fn(_t: float, _s: np.ndarray) -> tuple[float, float, float]:
        return thrust, alpha, beta

    sol = solve_ivp(
        equations_of_motion,
        t_span=(0.0, duration_tu),
        y0=state,
        method="DOP853",
        rtol=PROPAGATION_RTOL,
        atol=PROPAGATION_ATOL,
        args=(thrust_fn, isp_s, mu),
    )
    if not sol.success:
        raise RuntimeError(f"segment propagation failed: {sol.message}")
    return sol.y[:, -1]


def matching_defect(
    controls: np.ndarray,
    state_initial: np.ndarray,
    state_final: np.ndarray,
    n_segments: int,
    tof_tu: float,
    isp_s: float,
    mu: float = 1.0,
) -> np.ndarray:
    """Defecto de matching (forward-backward shooting) en el punto medio.

    Args:
        controls: array (n_segments, 3) de [T, alpha, beta] por segmento,
            T en unidades canonicas de fuerza (ver
            dynamics.thrust_to_canonical).
        state_initial: estado en t0 (canonico, [r(3), v(3), m]).
        state_final: estado objetivo en tf (rendezvous), mismo formato.
        n_segments: numero de segmentos N.
        tof_tu: tiempo de vuelo total, en TU. Se reparte en N segmentos
            de igual duracion (la duracion variable por segmento es un
            refinamiento de una fase posterior, no de T-1.2).
        isp_s: impulso especifico [s], pasado a la EDO de cada segmento.
        mu: parametro gravitacional canonico (1.0 por definicion DU/TU).

    Returns:
        Vector de defectos (7,); el optimizador los restringe a ~0.
    """
    controls = np.asarray(controls, dtype=float).reshape(n_segments, 3)
    segment_duration = tof_tu / n_segments
    n_forward = (n_segments + 1) // 2

    state = np.asarray(state_initial, dtype=float)
    for i in range(n_forward):
        state = _propagate_segment(state, controls[i], segment_duration, isp_s, mu)
    forward_midpoint = state

    state = np.asarray(state_final, dtype=float)
    for i in reversed(range(n_forward, n_segments)):
        state = _propagate_segment(state, controls[i], -segment_duration, isp_s, mu)
    backward_midpoint = state

    return forward_midpoint - backward_midpoint
