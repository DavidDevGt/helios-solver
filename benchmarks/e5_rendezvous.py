"""E5 (PLAN.md sec. 3, escalera de realismo): 3D, rendezvous completo
(posicion Y velocidad) -> M1, "LA IMAGEN".

Ultimo escalon: a diferencia de E4 (solo posicion), aqui el objetivo es
un rendezvous real -- posicion Y velocidad de Marte, ambas al mismo
tiempo. El control tambien se vuelve completo por primera vez: el
throttle (`T` entre 0 y T_max) pasa a ser variable de decision segmento
a segmento, no fijo a T_max como en E1-E4 -- coastear cuando conviene
es necesario para un rendezvous preciso Y eficiente en propelente
(ver "hallazgos de la busqueda" mas abajo).

**Formulacion en dos etapas** (no una eleccion arbitraria -- la
alternativa directa fallo, ver abajo):

1. **Arranque**: direccion-solamente (`alpha`, `beta` libres, T fijo en
   T_max), objetivo blando = minimizar el error cuadratico combinado de
   posicion Y velocidad. Converge de forma confiable y precisa (~5 km,
   <0.001 m/s) pero gasta mucho mas propelente del necesario (throttle
   siempre al 100%, sin poder bajarlo).
2. **Refinamiento**: partiendo de (1) como semilla, se libera el
   throttle y se cambia a restricciones *duras* de SLSQP (posicion Y
   velocidad final = las de Marte, 6 componentes) con objetivo real:
   maximizar masa final. Sin el warm-start del paso 1, esta
   restriccion de 6 componentes no converge desde una semilla ingenua
   (mismo problema que se documento en E4 para 3 componentes, peor
   aqui); con el warm-start, converge limpio.

**Hallazgos de la busqueda de TOF** (no se uso el TOF heredado de E4,
256 dias -- resulto ser demasiado corto para un rendezvous real):
con 256 dias, la combinacion posicion+velocidad no converge a nada
cercano al objetivo (millones de km, miles de m/s) sin importar
cuantos segmentos, semillas o si se agrega throttle -- una
verificacion de aislamiento (matching de *solo* velocidad, ignorando
posicion) SI converge perfecto, lo que descarta un bug de unidades y
confirma que es un problema real de alcanzabilidad conjunta con ese
TOF. Un barrido de TOF (300-500 dias, el rango que el propio PLAN.md
sec. 3 ya anticipaba: "TOF ~= 300-400 dias") encontro que 350-400 dias
si convergen limpio; se eligio 350 (mejor masa final entre los dos).

**Sobre la fraccion de masa final** (~62%, no el ~80% que PLAN.md
sec. 3 usa como calculo de cordura): el propio PLAN.md ya anticipa
esto como diagnostico, no como bug -- "si sale por debajo de 0.70,
sospechar control ineficiente o demasiadas revoluciones". Es
exactamente lo que pasa: 12 segmentos con perfil de arranque
siempre-a-full-throttle es un punto de partida ineficiente para el
refinamiento de masa; el resultado final (0.62) mejora bastante sobre
el arranque (0.49) pero sigue sin ser el optimo global de propelente.
Cerrar esa brecha es trabajo de multi-start real (T-1.5) y busqueda
global (Fase 2), no de este escalon -- **el criterio de aceptacion
real de T-1.7 es la precision del rendezvous (|Δr|<1000km, |Δv|<1m/s),
no la fraccion de masa**, y eso si se cumple con margen de 3+ ordenes
de magnitud.

**T-1.9 (verificacion final)**: la solucion se re-integra con
`rtol=1e-12` (no solo la `rtol=1e-11` de "verificacion" de los
escalones anteriores) antes de aceptarla -- ver `tests/test_e5_scenario.py`.
Ninguna solucion se publica sin este paso (regla dura de PLAN.md).

Uso: `uv run python benchmarks/e5_rendezvous.py`
Genera: benchmarks/e5_rendezvous.png y benchmarks/m1_spiral.png (identicas
-- m1_spiral.png es el nombre que pide T-1.8 para LA IMAGEN de M1).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

from helios.constants import DAY_S, DU_KM, G0_KM_S2, TU_S
from helios.dynamics import equations_of_motion, thrust_direction, thrust_to_canonical
from helios.ephemeris import state_vector
from helios.viz import plot_trajectory

ISP_S = 3000.0
T_MAX_N = 0.5
M0_KG = 1000.0
N_SEGMENTS = 12
N_PLOT_POINTS_PER_SEGMENT = 40

DEPARTURE = dt.datetime(2029, 1, 1)
TOF_DAYS = 350.0
ARRIVAL = DEPARTURE + dt.timedelta(days=TOF_DAYS)

ANGLE_BOUND_RAD = 2.0 * np.pi  # ver docs/adr y e3_free_tof.py

SEARCH_RTOL = 1e-7
SEARCH_ATOL = 1e-9
VERIFY_RTOL = 1e-12  # T-1.9: mas fino que la verificacion "estandar" de E1-E4
VERIFY_ATOL = 1e-14

POSITION_TOLERANCE_KM = 1000.0  # T-1.7
VELOCITY_TOLERANCE_KM_S = 0.001  # T-1.7: |Δv| < 1 m/s


def boundary_states() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(state_initial canonico, r_objetivo canonico, v_objetivo canonico)."""
    r0_km, v0_km_s = state_vector("earth", DEPARTURE)
    r_target_km, v_target_km_s = state_vector("mars", ARRIVAL)

    state_initial = np.concatenate([r0_km / DU_KM, v0_km_s * TU_S / DU_KM, [1.0]])
    r_target = r_target_km / DU_KM
    v_target = v_target_km_s * TU_S / DU_KM
    return state_initial, r_target, v_target


def _segment_duration_tu() -> float:
    return (TOF_DAYS * DAY_S / TU_S) / N_SEGMENTS


def terminal_state(
    x: np.ndarray, state_initial: np.ndarray, *, rtol: float, atol: float
) -> np.ndarray:
    """x = [throttle_1..throttle_N (0..1), alpha_1..N, beta_1..N]."""
    thrust_max_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    throttle = x[:N_SEGMENTS]
    alphas = x[N_SEGMENTS : 2 * N_SEGMENTS]
    betas = x[2 * N_SEGMENTS :]
    segment_duration = _segment_duration_tu()
    state = state_initial.copy()
    for th, alpha, beta in zip(throttle, alphas, betas, strict=True):
        thrust_value = th * thrust_max_canonical

        def thrust_fn(_t, _s, T=thrust_value, a=alpha, b=beta):
            return T, a, b

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


def _direction_only_warm_start(
    state_initial: np.ndarray, r_target: np.ndarray, v_target: np.ndarray
):
    """Etapa 1: throttle fijo en 1.0 (T_max), solo direccion libre,
    objetivo blando de matching combinado posicion+velocidad."""

    def full_x(alpha_beta: np.ndarray) -> np.ndarray:
        return np.concatenate([np.ones(N_SEGMENTS), alpha_beta])

    def combined_error(alpha_beta: np.ndarray) -> float:
        state = terminal_state(
            full_x(alpha_beta), state_initial, rtol=SEARCH_RTOL, atol=SEARCH_ATOL
        )
        return float(np.sum((state[0:3] - r_target) ** 2) + np.sum((state[3:6] - v_target) ** 2))

    result = minimize(
        combined_error,
        np.zeros(2 * N_SEGMENTS),
        method="SLSQP",
        bounds=[(-ANGLE_BOUND_RAD, ANGLE_BOUND_RAD)] * (2 * N_SEGMENTS),
        options={"maxiter": 250, "ftol": 1e-14},
    )
    if not result.success:
        raise RuntimeError(f"warm-start (direction-only) no convergio: {result.message}")
    return full_x(result.x)


def solve(x0: np.ndarray | None = None) -> np.ndarray:
    """Devuelve `x = [throttle_1..N, alpha_1..N, beta_1..N]` que
    maximiza la masa final sujeto a rendezvous completo (posicion Y
    velocidad de Marte), via el warm-start de dos etapas del docstring
    del modulo."""
    state_initial, r_target, v_target = boundary_states()

    if x0 is None:
        x0 = _direction_only_warm_start(state_initial, r_target, v_target)

    def r_constraint(x):
        return terminal_state(x, state_initial, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)[0:3] - r_target

    def v_constraint(x):
        return terminal_state(x, state_initial, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)[3:6] - v_target

    def negative_final_mass(x):
        return -terminal_state(x, state_initial, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)[6]

    bounds = (
        [(0.0, 1.0)] * N_SEGMENTS
        + [(-ANGLE_BOUND_RAD, ANGLE_BOUND_RAD)] * N_SEGMENTS
        + [(-ANGLE_BOUND_RAD, ANGLE_BOUND_RAD)] * N_SEGMENTS
    )
    constraints = [
        {"type": "eq", "fun": r_constraint},
        {"type": "eq", "fun": v_constraint},
    ]
    result = minimize(
        negative_final_mass,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 300, "ftol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"refinamiento (restricciones duras) no convergio: {result.message}")
    return result.x


def simulate(x: np.ndarray):
    """Re-propaga con tolerancia T-1.9 (`VERIFY_RTOL=1e-12`); devuelve
    `(trajectory, segment_of_row, thrust_max_canonical, state_initial)`."""
    state_initial, _r_target, _v_target = boundary_states()
    thrust_max_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    throttle = x[:N_SEGMENTS]
    alphas = x[N_SEGMENTS : 2 * N_SEGMENTS]
    betas = x[2 * N_SEGMENTS :]
    segment_duration = _segment_duration_tu()
    state = state_initial.copy()

    trajectory_rows = [state]
    segment_of_row = [0]
    for segment_idx, (th, alpha, beta) in enumerate(zip(throttle, alphas, betas, strict=True)):
        thrust_value = th * thrust_max_canonical

        def thrust_fn(_t, _s, T=thrust_value, a=alpha, b=beta):
            return T, a, b

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

    return np.array(trajectory_rows), np.array(segment_of_row), thrust_max_canonical, state_initial


def render(
    x: np.ndarray,
    trajectory: np.ndarray,
    segment_of_row: np.ndarray,
    thrust_max_canonical: float,
    out_name: str = "e5_rendezvous.png",
) -> Path:
    throttle = x[:N_SEGMENTS]
    alphas = x[N_SEGMENTS : 2 * N_SEGMENTS]
    betas = x[2 * N_SEGMENTS :]

    r_transfer = trajectory[:, 0:2]
    thrust_vectors = np.zeros((len(trajectory), 2))
    for idx in range(len(trajectory)):
        seg = segment_of_row[idx]
        r_vec = trajectory[idx, 0:3]
        v_vec = trajectory[idx, 3:6]
        thrust_vectors[idx] = (
            throttle[seg]
            * thrust_max_canonical
            * thrust_direction(r_vec, v_vec, alphas[seg], betas[seg])[0:2]
        )

    theta = np.linspace(0.0, 2.0 * np.pi, 200)
    r_earth_ring = np.column_stack([np.cos(theta), np.sin(theta)])
    r_mars_ring = 1.523679 * np.column_stack([np.cos(theta), np.sin(theta)])

    mass_ratio = trajectory[-1, 6]
    delta_v_km_s = ISP_S * G0_KM_S2 * np.log(1.0 / mass_ratio)

    fig = plot_trajectory(
        r_earth_ring,
        r_mars_ring,
        r_transfer,
        thrust_vectors,
        departure_date=DEPARTURE.date().isoformat(),
        arrival_date=ARRIVAL.date().isoformat(),
        delta_v_km_s=delta_v_km_s,
        mass_ratio=mass_ratio,
        tof_days=TOF_DAYS,
    )
    fig.axes[0].set_title("E5 / M1 -- full rendezvous (position + velocity), real ephemerides")

    out_path = Path(__file__).parent / out_name
    fig.savefig(out_path, dpi=150)
    return out_path


if __name__ == "__main__":
    _state_initial, r_target, v_target = boundary_states()
    print(f"departure={DEPARTURE.date()}  arrival={ARRIVAL.date()}  TOF={TOF_DAYS:.0f} days")

    x_opt = solve()
    trajectory, segment_of_row, thrust_max_canonical, state_initial = simulate(x_opt)
    final = trajectory[-1]

    position_error_km = np.linalg.norm(final[0:3] - r_target) * DU_KM
    velocity_error_km_s = np.linalg.norm(final[3:6] - v_target) * DU_KM / TU_S
    print(f"position error = {position_error_km:.3f} km (tolerance {POSITION_TOLERANCE_KM} km)")
    print(f"velocity error = {velocity_error_km_s * 1000:.4f} m/s (tolerance 1 m/s)")
    print(f"mass_ratio (m_f/m_0) = {final[6]:.4f}")

    out_path = render(x_opt, trajectory, segment_of_row, thrust_max_canonical)
    m1_path = render(
        x_opt, trajectory, segment_of_row, thrust_max_canonical, out_name="m1_spiral.png"
    )
    print(f"saved {out_path}")
    print(f"saved {m1_path}")
