"""E5 / M1 / T-1.9: rendezvous completo, verificacion de alta precision.

A diferencia de E1-E4, este archivo NO corre un barrido multi-semilla
(el patron de test_e2_scenario.py / test_e3_scenario.py /
test_e4_scenario.py): cada resolucion completa de E5 (arranque +
refinamiento con restricciones duras) toma ~100 s, y una semilla es
suficiente para probar lo que T-1.9 pide -- que *la* solucion publicada
pasa la verificacion de alta precision, no que el problema sea
robusto a la semilla (eso sigue siendo trabajo de T-1.5, ver el
docstring de e5_rendezvous.py). Decision deliberada de alcance, no un
descuido.

Regla dura de PLAN.md: "Ninguna solucion se publica sin este paso" --
la solucion se re-integra con `rtol=1e-12` (T-1.9) y se verifica contra
el criterio literal de T-1.7: |Δr| < 1000 km y |Δv| < 1 m/s.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

from helios.constants import DU_KM, TU_S
from helios.ephemeris import state_vector

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))
import e5_rendezvous as e5  # noqa: E402

POSITION_TOLERANCE_KM = 1000.0  # T-1.7
VELOCITY_TOLERANCE_KM_S = 0.001  # T-1.7: |Δv| < 1 m/s


@pytest.fixture(scope="module")
def solution() -> np.ndarray:
    return e5.solve()


@pytest.fixture(scope="module")
def boundary() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return e5.boundary_states()


def test_e5_rendezvous_satisfies_t17_tolerance_at_t19_precision(solution, boundary):
    """T-1.9: re-integra a rtol=1e-12 (no la rtol=1e-11 de "verificacion
    estandar" de E1-E4) antes de aceptar la solucion; T-1.7: |Δr|<1000km
    y |Δv|<1m/s."""
    state_initial, r_target, v_target = boundary
    state_final = e5.terminal_state(
        solution, state_initial, rtol=e5.VERIFY_RTOL, atol=e5.VERIFY_ATOL
    )

    position_error_km = np.linalg.norm(state_final[0:3] - r_target) * DU_KM
    velocity_error_km_s = np.linalg.norm(state_final[3:6] - v_target) * DU_KM / TU_S

    assert position_error_km < POSITION_TOLERANCE_KM
    assert velocity_error_km_s < VELOCITY_TOLERANCE_KM_S


def test_e5_mass_ratio_is_physically_sane(solution, boundary):
    """No es el ~80% idealizado de PLAN.md sec. 3 (ver el docstring de
    e5_rendezvous.py: el punto de partida de la busqueda es ineficiente,
    trabajo de T-1.5/Fase 2 mejorarlo) pero debe seguir siendo un valor
    fisico razonable, no un artefacto (masa negativa, >1, o ~0 por
    quedarse sin propelente a medio camino)."""
    state_initial, _r_target, _v_target = boundary
    state_final = e5.terminal_state(
        solution, state_initial, rtol=e5.VERIFY_RTOL, atol=e5.VERIFY_ATOL
    )

    assert 0.3 < state_final[6] < 1.0


def test_e5_trajectory_is_genuinely_three_dimensional(solution, boundary):
    state_initial, _r_target, _v_target = boundary
    state_final = e5.terminal_state(
        solution, state_initial, rtol=e5.VERIFY_RTOL, atol=e5.VERIFY_ATOL
    )

    assert abs(state_final[2]) * DU_KM > 1000.0


def test_e5_uses_variable_throttle_not_always_on(solution):
    """A diferencia de E1-E4 (T fijo en T_max), E5 introduce el throttle
    como variable de decision real -- si el resultado converge con
    throttle siempre en 1.0, la etapa de refinamiento de masa no esta
    aportando nada."""
    throttle = solution[: e5.N_SEGMENTS]

    assert throttle.min() < 0.95


def test_e5_boundary_states_match_real_ephemeris(boundary):
    state_initial, _r_target, _v_target = boundary
    r0_km, v0_km_s = state_vector("earth", e5.DEPARTURE)

    assert np.allclose(state_initial[0:3] * DU_KM, r0_km)
    assert np.allclose(state_initial[3:6] * DU_KM / TU_S, v0_km_s)
