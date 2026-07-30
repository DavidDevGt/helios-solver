"""E4: 3D con efemerides reales, fechas fijas.

A diferencia de E1-E3 (orbitas circulares idealizadas), el estado
inicial y el objetivo vienen de `ephemeris.state_vector` en fechas de
calendario reales -- este archivo prueba que el pipeline completo
(efemerides -> dinamica -> optimizacion) cierra con datos reales, no
solo con el caso de juguete.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

from helios.constants import DU_KM, TU_S
from helios.ephemeris import state_vector

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))
import e4_real_ephemerides as e4  # noqa: E402

POSITION_TOLERANCE_KM = 1000.0  # mismo estandar que T-0.7
MASS_RATIO_SPREAD_TOLERANCE = 0.01


@pytest.fixture(scope="module")
def boundary() -> tuple[np.ndarray, np.ndarray]:
    return e4.boundary_states()


@pytest.fixture(scope="module")
def multi_seed_solutions() -> list[np.ndarray]:
    rng = np.random.default_rng(5)
    seeds = [np.zeros(2 * e4.N_SEGMENTS)] + [
        rng.uniform(-0.5, 0.5, 2 * e4.N_SEGMENTS) for _ in range(3)
    ]
    return [e4.solve(x0) for x0 in seeds]


def test_e4_reaches_mars_real_position_within_tolerance(boundary, multi_seed_solutions):
    state_initial, r_target = boundary
    for x_opt in multi_seed_solutions:
        state_final = e4.terminal_state(
            x_opt, state_initial, rtol=e4.VERIFY_RTOL, atol=e4.VERIFY_ATOL
        )
        position_error_km = np.linalg.norm(state_final[0:3] - r_target) * DU_KM
        assert position_error_km < POSITION_TOLERANCE_KM


def test_e4_mass_ratio_consistent_across_seeds(boundary, multi_seed_solutions):
    state_initial, _r_target = boundary
    mass_ratios = [
        e4.terminal_state(x_opt, state_initial, rtol=e4.VERIFY_RTOL, atol=e4.VERIFY_ATOL)[6]
        for x_opt in multi_seed_solutions
    ]
    assert max(mass_ratios) - min(mass_ratios) < MASS_RATIO_SPREAD_TOLERANCE


def test_e4_trajectory_is_genuinely_three_dimensional(boundary, multi_seed_solutions):
    """A diferencia de E1-E3 (z=0 por construccion), E4 debe salirse del
    plano porque las orbitas reales de Tierra/Marte no son coplanares."""
    state_initial, _r_target = boundary
    state_final = e4.terminal_state(
        multi_seed_solutions[0], state_initial, rtol=e4.VERIFY_RTOL, atol=e4.VERIFY_ATOL
    )
    assert abs(state_final[2]) * DU_KM > 1000.0  # z final, en km: claramente fuera del plano


def test_e4_departure_state_matches_earth_ephemeris(boundary):
    """El estado inicial del problema es de verdad la efemeride real de
    la Tierra en DEPARTURE, no un valor idealizado -- lo re-verifica
    contra ephemeris.state_vector independientemente."""
    state_initial, _r_target = boundary
    r0_km, v0_km_s = state_vector("earth", e4.DEPARTURE)

    assert np.allclose(state_initial[0:3] * DU_KM, r0_km)
    assert np.allclose(state_initial[3:6] * DU_KM / TU_S, v0_km_s)
