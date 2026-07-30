"""E3 (PLAN.md sec. 3, escalera de realismo): 2D, tiempo de vuelo libre.

Extiende E2 agregando el tiempo de vuelo total (TOF) como variable de
decision adicional junto a los angulos de direccion `alpha_i` -- sigue
2D, orbitas circulares idealizadas, empuje siempre encendido a T_max
(la magnitud sigue sin ser variable de decision; eso lo introduciria un
escalon aparte, no definido en la escalera de PLAN.md).

Objetivo: a diferencia de E2 (donde con TOF fijo y T_max siempre
encendido la masa consumida no dependia de la direccion, asi que hubo
que inventar un objetivo de "esfuerzo de control"), aqui **minimizar el
TOF es maximizar la masa final** de forma directa y genuina: con empuje
de magnitud constante, m_f = m_0 - k*TOF, asi que menos tiempo quemando
propelente para llegar a la misma insercion cuasi-circular es
literalmente "max m(t_f)" (el objetivo real del proyecto, README.md
Abstract), no un proxy. Restricciones (duras, via SLSQP): radio final =
radio de Marte, rapidez final = velocidad circular en ese radio -- igual
que E2.

**Nota de robustez de la formulacion (aprendida auditando E2, ver
docs/adr y benchmarks/e2_optimized_steering.py):** los angulos `alpha_i`
son variables periodicas (una direccion fisica se repite cada 2*pi).
Acotarlos ingenuamente a `[-pi, pi]` puede hacer que SLSQP se quede
pegado en un borde artificial en vez de seguir explorando -- se
verifico empiricamente (moviendo el borde y viendo que la solucion
mejoraba) antes de fijar `[-2*pi, 2*pi]` como cota real. Con esa cota,
la convergencia multi-semilla es mucho mas consistente que en E2 (ver
tests/test_e3_scenario.py): most semillas caen en el *mismo* optimo a
varios decimales, no solo en el mismo valor de objetivo.

Caso de referencia (igual que E1/E2, PLAN.md sec. 3): Isp = 3000 s,
T_max = 0.5 N, m0 = 1000 kg. La semilla de arranque es el perfil
convergido de E2 (TOF=180 dias) -- calentar cada escalon con el anterior,
no empezar de cero.

Uso: `uv run python benchmarks/e3_free_tof.py`
Genera: benchmarks/e3_free_tof.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from helios.constants import DAY_S, G0_KM_S2, MARS_SEMI_MAJOR_AXIS_AU, TU_S
from helios.dynamics import equations_of_motion, thrust_direction, thrust_to_canonical
from helios.solvers.local import solve_slsqp
from helios.viz import plot_trajectory

ISP_S = 3000.0
T_MAX_N = 0.5
M0_KG = 1000.0
N_SEGMENTS = 8
N_PLOT_POINTS_PER_SEGMENT = 50

# Semilla de arranque: perfil convergido de E2 (benchmarks/e2_optimized_steering.py) a TOF=180d.
SEED_ALPHA_DEG = [23.35, 31.60, 39.65, 46.74, 52.46, 57.05, -79.01, -81.08]
SEED_TOF_DAYS = 180.0

TOF_BOUNDS_DAYS = (30.0, 400.0)
ALPHA_BOUND_RAD = 2.0 * np.pi  # ver nota de robustez en el docstring del modulo

SEARCH_RTOL = 1e-8
SEARCH_ATOL = 1e-10
VERIFY_RTOL = 1e-11
VERIFY_ATOL = 1e-13


def v_circular_at_mars() -> float:
    return np.sqrt(1.0 / MARS_SEMI_MAJOR_AXIS_AU)  # canonico, mu=1


def default_seed() -> np.ndarray:
    return np.concatenate([np.radians(SEED_ALPHA_DEG), [SEED_TOF_DAYS * DAY_S / TU_S]])


def terminal_state(x: np.ndarray, *, rtol: float, atol: float) -> np.ndarray:
    """x = [alpha_1..alpha_N, tof_tu]."""
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    alphas = x[:N_SEGMENTS]
    tof_tu = x[N_SEGMENTS]
    segment_duration = tof_tu / N_SEGMENTS
    state = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0])
    for alpha in alphas:

        def thrust_fn(_t, _s, a=alpha):
            return thrust_canonical, a, 0.0

        sol = solve_ivp(
            equations_of_motion,
            t_span=(0.0, segment_duration),
            y0=state,
            method="DOP853",
            rtol=rtol,
            atol=atol,
            args=(thrust_fn, ISP_S, 1.0),
        )
        if not sol.success:
            raise RuntimeError(f"segment propagation failed: {sol.message}")
        state = sol.y[:, -1]
    return state


def radius_constraint(x: np.ndarray) -> float:
    state = terminal_state(x, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)
    return np.linalg.norm(state[0:3]) - MARS_SEMI_MAJOR_AXIS_AU


def speed_constraint(x: np.ndarray) -> float:
    state = terminal_state(x, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)
    return np.linalg.norm(state[3:6]) - v_circular_at_mars()


def tof_objective(x: np.ndarray) -> float:
    return float(x[N_SEGMENTS])


def solve(x0: np.ndarray | None = None) -> np.ndarray:
    """Optimiza `[alpha_1..alpha_N, TOF]`: minimo TOF (= masa final
    maxima) sujeto a insercion cuasi-circular en Marte."""
    if x0 is None:
        x0 = default_seed()
    bounds = [(-ALPHA_BOUND_RAD, ALPHA_BOUND_RAD)] * N_SEGMENTS + [
        (TOF_BOUNDS_DAYS[0] * DAY_S / TU_S, TOF_BOUNDS_DAYS[1] * DAY_S / TU_S)
    ]
    constraints = [
        {"type": "eq", "fun": radius_constraint},
        {"type": "eq", "fun": speed_constraint},
    ]
    return solve_slsqp(
        tof_objective,
        constraints,
        x0,
        bounds=bounds,
        options={"maxiter": 400, "ftol": 1e-13},
    )


def simulate(x: np.ndarray):
    """Re-propaga la solucion optimizada con tolerancia fina; devuelve
    `(trajectory, segment_of_row, thrust_canonical)` (ver
    e2_optimized_steering.simulate, mismo esquema)."""
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    alphas = x[:N_SEGMENTS]
    tof_tu = x[N_SEGMENTS]
    segment_duration = tof_tu / N_SEGMENTS
    state = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0])

    trajectory_rows = [state]
    segment_of_row = [0]
    for segment_idx, alpha in enumerate(alphas):

        def thrust_fn(_t, _s, a=alpha):
            return thrust_canonical, a, 0.0

        t_eval = np.linspace(0.0, segment_duration, N_PLOT_POINTS_PER_SEGMENT)
        sol = solve_ivp(
            equations_of_motion,
            t_span=(0.0, segment_duration),
            y0=state,
            method="DOP853",
            rtol=VERIFY_RTOL,
            atol=VERIFY_ATOL,
            args=(thrust_fn, ISP_S, 1.0),
            t_eval=t_eval,
        )
        if not sol.success:
            raise RuntimeError(f"segment propagation failed: {sol.message}")
        new_rows = sol.y[:, 1:].T
        trajectory_rows.extend(new_rows)
        segment_of_row.extend([segment_idx] * len(new_rows))
        state = sol.y[:, -1]

    return np.array(trajectory_rows), np.array(segment_of_row), thrust_canonical


def render(
    x: np.ndarray, trajectory: np.ndarray, segment_of_row: np.ndarray, thrust_canonical: float
) -> Path:
    alphas = x[:N_SEGMENTS]
    tof_days = x[N_SEGMENTS] * TU_S / DAY_S

    r_transfer = trajectory[:, 0:2]
    thrust_vectors = np.zeros((len(trajectory), 2))
    for idx in range(len(trajectory)):
        alpha = alphas[segment_of_row[idx]]
        r_vec = trajectory[idx, 0:3]
        v_vec = trajectory[idx, 3:6]
        thrust_vectors[idx] = thrust_canonical * thrust_direction(r_vec, v_vec, alpha, 0.0)[0:2]

    theta = np.linspace(0.0, 2.0 * np.pi, 200)
    r_earth = np.column_stack([np.cos(theta), np.sin(theta)])
    r_mars = MARS_SEMI_MAJOR_AXIS_AU * np.column_stack([np.cos(theta), np.sin(theta)])

    mass_ratio = trajectory[-1, 6]
    delta_v_km_s = ISP_S * G0_KM_S2 * np.log(1.0 / mass_ratio)

    fig = plot_trajectory(
        r_earth,
        r_mars,
        r_transfer,
        thrust_vectors,
        departure_date="t0 + 0 d",
        arrival_date=f"t0 + {tof_days:.1f} d",
        delta_v_km_s=delta_v_km_s,
        mass_ratio=mass_ratio,
        tof_days=tof_days,
    )
    fig.axes[0].set_title("E3 -- free time of flight (minimum TOF / maximum m_f)")

    out_path = Path(__file__).parent / "e3_free_tof.png"
    fig.savefig(out_path, dpi=150)
    return out_path


if __name__ == "__main__":
    x_opt = solve()
    tof_days_opt = x_opt[N_SEGMENTS] * TU_S / DAY_S
    print("alpha (deg):", np.degrees(x_opt[:N_SEGMENTS]))
    print(f"TOF = {tof_days_opt:.4f} days (E2 baseline was fixed at {SEED_TOF_DAYS:.0f} days)")

    trajectory, segment_of_row, thrust_canonical = simulate(x_opt)
    final = trajectory[-1]
    r_final = np.linalg.norm(final[0:3])
    v_final = np.linalg.norm(final[3:6])
    print(f"r_final = {r_final:.6f} DU (Mars = {MARS_SEMI_MAJOR_AXIS_AU} DU)")
    print(f"v_final = {v_final:.6f} DU/TU (circular target = {v_circular_at_mars():.6f})")
    print(f"mass_ratio (m_f/m_0) = {final[6]:.4f}")

    out_path = render(x_opt, trajectory, segment_of_row, thrust_canonical)
    print(f"saved {out_path}")
