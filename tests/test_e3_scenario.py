"""E3: tiempo de vuelo libre, minimo TOF (= masa final maxima).

A diferencia de E2 (ver tests/test_e2_scenario.py), aqui el objetivo
(minimizar TOF) es genuino, no un proxy -- y por eso, a diferencia de
E2, las semillas SI convergen de forma consistente al mismo optimo, no
solo al mismo valor de objetivo. Este archivo verifica precisamente esa
diferencia con E2 (ademas de las restricciones terminales y la mejora
sobre el baseline de E2).
"""

import sys
from pathlib import Path

import numpy as np
import pytest

from helios.constants import DAY_S, MARS_SEMI_MAJOR_AXIS_AU, TU_S

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))
import e2_optimized_steering as e2  # noqa: E402
import e3_free_tof as e3  # noqa: E402

CONSTRAINT_TOLERANCE = 1e-6
TOF_SPREAD_TOLERANCE_DAYS = 2.0  # generoso; el valor medido es ~0.01 d entre semillas iguales


def _seeds() -> list[np.ndarray]:
    rng = np.random.default_rng(2)
    seeds = [e3.default_seed()]
    for _ in range(3):
        alphas = rng.uniform(-np.pi, np.pi, e3.N_SEGMENTS)
        tof_tu = rng.uniform(100.0, 300.0) * DAY_S / TU_S
        seeds.append(np.concatenate([alphas, [tof_tu]]))
    return seeds


@pytest.fixture(scope="module")
def multi_seed_solutions() -> list[np.ndarray]:
    return [e3.solve(x0) for x0 in _seeds()]


def test_e3_satisfies_terminal_constraints_from_every_seed(multi_seed_solutions):
    for x_opt in multi_seed_solutions:
        assert abs(e3.radius_constraint(x_opt)) < CONSTRAINT_TOLERANCE
        assert abs(e3.speed_constraint(x_opt)) < CONSTRAINT_TOLERANCE


def test_e3_converges_to_the_same_tof_across_seeds(multi_seed_solutions):
    """A diferencia de E2 (objetivo degenerado -> perfiles distintos),
    aqui el objetivo es real (minimo TOF fisico) y el problema resulta
    mucho mejor condicionado: distintas semillas deben coincidir en el
    TOF optimo dentro de un margen chico, no solo en las restricciones."""
    tofs_days = [x_opt[e3.N_SEGMENTS] * TU_S / DAY_S for x_opt in multi_seed_solutions]
    assert max(tofs_days) - min(tofs_days) < TOF_SPREAD_TOLERANCE_DAYS


def test_e3_beats_e2_fixed_tof_baseline_on_mass_ratio(multi_seed_solutions):
    """El punto de E3: dejar el TOF libre debe encontrar una insercion
    igual de valida (misma restriccion cuasi-circular) consumiendo menos
    propelente que el TOF fijo de 180 dias de E2 -- si no, no hay razon
    para el escalon."""
    state_e3 = e3.terminal_state(multi_seed_solutions[0], rtol=e3.VERIFY_RTOL, atol=e3.VERIFY_ATOL)

    alphas_e2 = e2.solve()
    state_e2 = e2.terminal_state(alphas_e2, rtol=e2.VERIFY_RTOL, atol=e2.VERIFY_ATOL)

    assert state_e3[6] > state_e2[6]


def test_e3_reaches_quasi_circular_insertion_at_mars(multi_seed_solutions):
    state_final = e3.terminal_state(
        multi_seed_solutions[0], rtol=e3.VERIFY_RTOL, atol=e3.VERIFY_ATOL
    )

    r_final = np.linalg.norm(state_final[0:3])
    v_final = np.linalg.norm(state_final[3:6])

    assert r_final == pytest.approx(MARS_SEMI_MAJOR_AXIS_AU, rel=1e-6)
    assert v_final == pytest.approx(e3.v_circular_at_mars(), rel=1e-6)


def test_e3_tof_is_shorter_than_e2_fixed_tof(multi_seed_solutions):
    tof_days = multi_seed_solutions[0][e3.N_SEGMENTS] * TU_S / DAY_S

    assert 0.0 < tof_days < e3.SEED_TOF_DAYS
