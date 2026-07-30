"""T-1.4 (segunda mitad): E2, direccion de empuje optimizada por SLSQP.

Formulacion real (ver el docstring de benchmarks/e2_optimized_steering.py
para el porque): minimizar esfuerzo de control `sum(alpha_i^2)` sujeto a
dos restricciones de igualdad duras (radio final = radio de Marte,
rapidez final = velocidad circular en ese radio).

El criterio literal de T-1.4 ("converge desde al menos 3 semillas
distintas al mismo optimo, ±1% en masa final") se cumple en el sentido
de que la masa final es identica entre semillas -- pero eso es un hecho
casi estructural (la masa depende de T_max y TOF, no de la direccion),
no evidencia de que SLSQP haya encontrado un optimo unico. La auditoria
que motivo esta version encontro, probando tres formulaciones distintas
del objetivo, que el *perfil* de direccion optimo NO es unico (2
restricciones, 8 variables -> subespacio de soluciones de 6 grados de
libertad); distintas semillas convergen de forma repetible y precisa a
las restricciones, pero a perfiles distintos entre si. Este archivo
prueba ambos hechos honestamente en vez de solo el que "sale bien".
"""

import sys
from pathlib import Path

import numpy as np
import pytest

from helios.constants import MARS_SEMI_MAJOR_AXIS_AU

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))
import e2_optimized_steering as e2  # noqa: E402

CONSTRAINT_TOLERANCE = 1e-6  # en unidades canonicas (radio: DU, rapidez: DU/TU)
MASS_RATIO_SPREAD_TOLERANCE = 0.01  # ±1%, literal de T-1.4


@pytest.fixture(scope="module")
def multi_seed_solutions() -> list[np.ndarray]:
    """4 SLSQP solves (1 semilla nula + 3 aleatorias), compartidas entre
    los tres tests de abajo -- cada solve toma unos segundos; recalcularlo
    por test triplicaba el tiempo de la suite sin ganar nada."""
    rng = np.random.default_rng(1)
    seeds = [np.zeros(e2.N_SEGMENTS)] + [rng.uniform(-1.5, 1.5, e2.N_SEGMENTS) for _ in range(3)]
    return [e2.solve(x0) for x0 in seeds]


def test_e2_satisfies_terminal_constraints_from_every_seed(multi_seed_solutions):
    """Lo que SI es verdad y confiable: cada semilla converge, con
    precision, a la restriccion de insercion cuasi-circular. Esto es lo
    que hace a E2 mejor que E1 (que ni siquiera lo intenta)."""
    for alphas_opt in multi_seed_solutions:
        assert abs(e2.radius_constraint(alphas_opt)) < CONSTRAINT_TOLERANCE
        assert abs(e2.speed_constraint(alphas_opt)) < CONSTRAINT_TOLERANCE


def test_e2_mass_ratio_matches_across_seeds(multi_seed_solutions):
    """La parte de T-1.4 que SI se cumple literalmente: masa final
    identica (±1%) entre semillas -- porque el thrust es siempre T_max,
    la masa consumida no depende del perfil de direccion encontrado."""
    mass_ratios = [
        e2.terminal_state(alphas, rtol=e2.VERIFY_RTOL, atol=e2.VERIFY_ATOL)[6]
        for alphas in multi_seed_solutions
    ]
    assert max(mass_ratios) - min(mass_ratios) < MASS_RATIO_SPREAD_TOLERANCE


def test_e2_steering_profile_is_not_unique_across_seeds(multi_seed_solutions):
    """Hallazgo de auditoria, verificado permanentemente: el perfil de
    direccion optimo NO es unico. Si esta asercion alguna vez falla (todas
    las semillas convergen al mismo perfil), no es un problema -- hay que
    *relajar* el test, no alarmarse; significaria que el problema dejo de
    ser degenerado (p.ej. si se agregan mas restricciones). Lo que si
    seria un problema real es que esto pase desapercibido y el README/PLAN
    vuelvan a afirmar "converge al mismo optimo" sin esta salvedad."""
    profiles = np.array(multi_seed_solutions)
    max_pairwise_diff_deg = np.degrees(np.max(np.abs(profiles[:, None, :] - profiles[None, :, :])))
    assert max_pairwise_diff_deg > 30.0


def test_e2_reaches_quasi_circular_insertion_at_mars():
    alphas_opt = e2.solve()
    state_final = e2.terminal_state(alphas_opt, rtol=e2.VERIFY_RTOL, atol=e2.VERIFY_ATOL)

    r_final = np.linalg.norm(state_final[0:3])
    v_final = np.linalg.norm(state_final[3:6])

    assert r_final == pytest.approx(MARS_SEMI_MAJOR_AXIS_AU, rel=1e-6)
    assert v_final == pytest.approx(e2.v_circular_at_mars(), rel=1e-6)


def test_e2_beats_e1_baseline():
    """El punto de E2 es que la direccion optimizada logra una insercion
    mejor que la del empuje puramente tangencial de E1 (misma T_max,
    mismo TOF, mismo propelente consumido) -- si esto no mejora, no hay
    razon para el escalon."""
    e1_baseline_state = e2.terminal_state(
        np.zeros(e2.N_SEGMENTS), rtol=e2.VERIFY_RTOL, atol=e2.VERIFY_ATOL
    )
    e1_r_error = abs(np.linalg.norm(e1_baseline_state[0:3]) - MARS_SEMI_MAJOR_AXIS_AU)
    e1_v_error = abs(np.linalg.norm(e1_baseline_state[3:6]) - e2.v_circular_at_mars())

    alphas_opt = e2.solve()
    state_final = e2.terminal_state(alphas_opt, rtol=e2.VERIFY_RTOL, atol=e2.VERIFY_ATOL)
    e2_r_error = abs(np.linalg.norm(state_final[0:3]) - MARS_SEMI_MAJOR_AXIS_AU)
    e2_v_error = abs(np.linalg.norm(state_final[3:6]) - e2.v_circular_at_mars())

    assert e2_r_error < e1_r_error / 100
    assert e2_v_error < e1_v_error / 100
