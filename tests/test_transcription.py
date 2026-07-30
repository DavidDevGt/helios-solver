"""T-1.2: transcripcion Sims-Flanagan, defecto de matching.

Criterio de aceptacion (PLAN.md): "con la solucion de Hohmann como
entrada, el defecto de matching es ~0". Se construye la transferencia de
Hohmann real (misma fisica que tests/test_hohmann.py, pero ahora en
unidades canonicas y propagada con la EDO de dynamics.py en vez de la
formula cerrada) como una trayectoria balistica (T=0 en todo el arco):
si transcription.matching_defect hace bien el forward/backward shooting,
coastear desde el estado inicial y desde el estado final deben
encontrarse en el punto medio a nivel de tolerancia de integracion, sin
importar en cuantos segmentos se parta el arco.
"""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from helios.constants import MARS_SEMI_MAJOR_AXIS_AU
from helios.dynamics import equations_of_motion, zero_thrust
from helios.transcription import _propagate_segment, matching_defect

ISP_S = 3000.0
MU = 1.0
MATCHING_TOLERANCE = 1e-7


def _hohmann_coast_states() -> tuple[np.ndarray, np.ndarray, float]:
    """Estados inicial/final canonicos de una Hohmann Tierra->Marte
    balistica, mas el TOF en TU. `state_final` se obtiene propagando
    `state_initial` con la propia EDO (no con la formula cerrada), para
    que el test de matching sea independiente de un segundo oraculo."""
    r1 = 1.0
    r2 = MARS_SEMI_MAJOR_AXIS_AU
    a_transfer = (r1 + r2) / 2.0
    v_periapsis = np.sqrt(MU * (2.0 / r1 - 1.0 / a_transfer))
    tof_tu = np.pi * np.sqrt(a_transfer**3 / MU)

    state_initial = np.array([r1, 0.0, 0.0, 0.0, v_periapsis, 0.0, 1.0])

    sol = solve_ivp(
        equations_of_motion,
        t_span=(0.0, tof_tu),
        y0=state_initial,
        method="DOP853",
        rtol=1e-12,
        atol=1e-13,
        args=(zero_thrust, ISP_S, MU),
    )
    assert sol.success
    state_final = sol.y[:, -1]

    # Verificacion cruzada contra el oraculo cerrado: al llegar, el radio
    # debe ser el de Marte y la trayectoria debe seguir siendo Kepleriana
    # (masa sin consumir, ya que fue puro coasting).
    assert np.linalg.norm(state_final[0:3]) == pytest.approx(r2, rel=1e-6)
    assert state_final[6] == pytest.approx(1.0)

    return state_initial, state_final, tof_tu


@pytest.mark.parametrize("n_segments", [1, 2, 4, 7])
def test_matching_defect_near_zero_for_hohmann_coast(n_segments):
    state_initial, state_final, tof_tu = _hohmann_coast_states()
    controls = np.zeros((n_segments, 3))

    defect = matching_defect(controls, state_initial, state_final, n_segments, tof_tu, ISP_S, MU)

    assert np.linalg.norm(defect) < MATCHING_TOLERANCE


@pytest.mark.parametrize("n_segments", [4, 5])
def test_matching_defect_near_zero_under_real_thrust(n_segments):
    """La transferencia balistica (arriba) nunca ejercita `m_dot != 0`, asi
    que no prueba nada sobre si el matching de *masa* funciona cuando el
    empuje esta realmente encendido -- en particular, que la integracion
    hacia atras "reconstruya" masa correctamente (dm/dt es el mismo signo
    en ambas direcciones; scipy con t_span decreciente debe invertirlo).
    Se construye un `state_final` auto-consistente encadenando los mismos
    N segmentos hacia adelante con controles no triviales y variados por
    segmento (no todos iguales, para no ocultar un bug de indexado)."""
    rng = np.random.default_rng(0)
    controls = np.column_stack(
        [
            rng.uniform(0.01, 0.05, n_segments),  # thrust
            rng.uniform(-0.3, 0.3, n_segments),  # alpha
            rng.uniform(-0.1, 0.1, n_segments),  # beta
        ]
    )
    tof_tu = 0.5
    segment_duration = tof_tu / n_segments

    state = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0])
    for i in range(n_segments):
        state = _propagate_segment(state, controls[i], segment_duration, ISP_S, MU)
    state_final = state
    assert state_final[6] < 1.0  # de verdad quemo propelente

    state_initial = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0])
    defect = matching_defect(controls, state_initial, state_final, n_segments, tof_tu, ISP_S, MU)

    assert np.linalg.norm(defect) < MATCHING_TOLERANCE
