"""T-0.6: conservacion de energia sin empuje.

Criterio: deriva relativa de energia < 1e-10 en 1 anio simulado con
DOP853 (rtol=1e-12). Este test debe pasar antes de anadir empuje a la
dinamica (T-1.1) -- que es exactamente lo que valida: se corre el mismo
`equations_of_motion` de T-1.1, con `thrust_fn` = `zero_thrust`.

Tambien cubre el segundo criterio de aceptacion de T-1.1 ("con empuje
tangencial constante la energia crece monotona"), porque ambos casos
comparten la misma EDO y el archivo natural para probarla es este.
"""

import datetime as dt

import numpy as np
from scipy.integrate import solve_ivp

from helios.constants import DAY_S, DU_KM, TU_S
from helios.dynamics import constant_tangential_thrust, equations_of_motion, zero_thrust
from helios.ephemeris import state_vector

ENERGY_DRIFT_TOLERANCE = 1e-10
INTEGRATION_RTOL = 1e-12
INTEGRATION_ATOL = 1e-13

ONE_YEAR_TU = (365.25 * DAY_S) / TU_S


def _earth_initial_state_canonical() -> np.ndarray:
    r_km, v_km_s = state_vector("earth", dt.datetime(2026, 1, 1))
    r_canonical = r_km / DU_KM
    v_canonical = v_km_s * TU_S / DU_KM
    return np.concatenate([r_canonical, v_canonical, [1.0]])


def _specific_energy(state: np.ndarray, mu: float = 1.0) -> float:
    r = state[0:3]
    v = state[3:6]
    return 0.5 * np.dot(v, v) - mu / np.linalg.norm(r)


def test_energy_conservation_no_thrust():
    state0 = _earth_initial_state_canonical()
    e0 = _specific_energy(state0)

    sol = solve_ivp(
        equations_of_motion,
        t_span=(0.0, ONE_YEAR_TU),
        y0=state0,
        method="DOP853",
        rtol=INTEGRATION_RTOL,
        atol=INTEGRATION_ATOL,
        args=(zero_thrust, 3000.0),
        dense_output=False,
    )
    assert sol.success, f"integration failed: {sol.message}"

    e_final = _specific_energy(sol.y[:, -1])
    relative_drift = abs(e_final - e0) / abs(e0)
    assert relative_drift < ENERGY_DRIFT_TOLERANCE, (
        f"relative energy drift {relative_drift:.3e} exceeds {ENERGY_DRIFT_TOLERANCE:.0e}"
    )


def test_constant_tangential_thrust_increases_energy_monotonically():
    state0 = _earth_initial_state_canonical()
    # Empuje deliberadamente grande (no representativo de una nave real)
    # para que el crecimiento de energia sea inequivoco frente al ruido
    # numerico de integracion en un test corto.
    thrust_fn = constant_tangential_thrust(thrust_canonical=1e-3)

    n_checkpoints = 50
    t_eval = np.linspace(0.0, 0.1 * ONE_YEAR_TU, n_checkpoints)
    sol = solve_ivp(
        equations_of_motion,
        t_span=(t_eval[0], t_eval[-1]),
        y0=state0,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        args=(thrust_fn, 3000.0),
        t_eval=t_eval,
    )
    assert sol.success, f"integration failed: {sol.message}"

    energies = np.array([_specific_energy(sol.y[:, i]) for i in range(n_checkpoints)])
    assert np.all(np.diff(energies) > 0), (
        "energy must increase monotonically under constant tangential thrust"
    )
