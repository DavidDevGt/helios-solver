"""E4 (PLAN.md sec. 3, escalera de realismo): 3D con efemerides reales,
fechas fijas.

Primer escalon que deja de usar orbitas circulares idealizadas: el
estado de salida es la posicion/velocidad REAL de la Tierra
(`ephemeris.state_vector`) en una fecha de calendario fija, y el
objetivo es la posicion REAL de Marte (no su radio orbital medio) en
una fecha de llegada tambien fija. Las fechas no son arbitrarias -- se
eligieron verificando la geometria real Tierra-Marte (ver mas abajo),
no solo tomando dos fechas cualquiera.

Sigue las convenciones heredadas de la escalera: empuje siempre
encendido a T_max (la magnitud no es variable de decision en ningun
escalon hasta ahora), tiempo de vuelo *fijo* (por eso "fechas fijas":
a diferencia de E3, aqui no se optimiza el TOF -- ver D-4 /
docs/adr/0004, cada escalon aisla una sola dimension de realismo
nueva). A diferencia de E1-E3, el control ahora es genuinamente 3D:
`alpha` (angulo en el plano RTN local) *y* `beta` (angulo fuera del
plano) son ambos variables de decision, porque las orbitas reales de
Tierra y Marte no son exactamente coplanares.

**Objetivo: por que no es "restricciones duras + esfuerzo minimo" como
E2.** Se probo esa formulacion (analoga a E2) y SLSQP fallo de forma
repetible ("Positive directional derivative for linesearch" / limite de
iteraciones) para la restriccion vectorial de 3 componentes (posicion
final = posicion de Marte) -- un problema numerico real de esa
formulacion en este caso, no solo una semilla mala (se intento tambien
con warm-start desde una solucion casi-factible y siguio fallando). En
cambio, minimizar directamente el error cuadratico de posicion
`|r_final - r_objetivo|^2` (un objetivo blando, pero genuino: la
calidad del match de posicion *es* literalmente lo que E4 tiene que
demostrar, no un proxy inventado como el "esfuerzo de control" de E2)
convergio de forma robusta y consistente desde multiples semillas
(~26-29 km de error final, mismo `mass_ratio` a 4 decimales entre
semillas). Con TOF y magnitud de empuje fijos, la masa final tampoco
depende del perfil de dirreccion aqui -- igual que en E2 -- asi que no
hay una alternativa de "maximizar masa" disponible en este escalon.

**Fechas y geometria de la ventana de lanzamiento** (no arbitrarias):
salida 2029-01-01, llegada 2029-09-14 (TOF = 256 dias, cerca de la
estimacion de Hohmann usando el radio *real* de la Tierra en esa fecha).
Verificado antes de fijarlas: el angulo Tierra(salida)-Sol-Marte(llegada)
es ~170.6 grados (el ideal de Hohmann es 180), y ambos puntos estan cerca
del plano de la eclíptica (Marte a solo -0.03 AU en z al llegar) -- una
ventana de transferencia real y razonable, no un par de fechas que
casualmente "funciona" en la optimizacion.

Solo posicion, no rendezvous completo: coincidir tambien velocidad
(magnitud y direccion) es exactamente lo que E5 (T-1.9, M1) tiene que
resolver.

Uso: `uv run python benchmarks/e4_real_ephemerides.py`
Genera: benchmarks/e4_real_ephemerides.png
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
N_SEGMENTS = 8
N_PLOT_POINTS_PER_SEGMENT = 50

DEPARTURE = dt.datetime(2029, 1, 1)
ARRIVAL = dt.datetime(2029, 9, 14)
TOF_DAYS = (ARRIVAL - DEPARTURE).days

ALPHA_BETA_BOUND_RAD = 2.0 * np.pi  # ver docs/adr y e3_free_tof.py: evita atascos en el borde

SEARCH_RTOL = 1e-8
SEARCH_ATOL = 1e-10
VERIFY_RTOL = 1e-11
VERIFY_ATOL = 1e-13

POSITION_TOLERANCE_KM = 1000.0  # mismo estandar que T-0.7 (tests/test_ephemeris.py)


def boundary_states() -> tuple[np.ndarray, np.ndarray]:
    """(state_initial canonico, r_objetivo canonico) a partir de
    efemerides reales en las fechas fijas del modulo."""
    r0_km, v0_km_s = state_vector("earth", DEPARTURE)
    r_target_km, _v_target_km_s = state_vector("mars", ARRIVAL)

    r0 = r0_km / DU_KM
    v0 = v0_km_s * TU_S / DU_KM
    r_target = r_target_km / DU_KM

    state_initial = np.concatenate([r0, v0, [1.0]])
    return state_initial, r_target


def _segment_duration_tu() -> float:
    return (TOF_DAYS * DAY_S / TU_S) / N_SEGMENTS


def terminal_state(
    x: np.ndarray, state_initial: np.ndarray, *, rtol: float, atol: float
) -> np.ndarray:
    """x = [alpha_1..alpha_N, beta_1..beta_N]."""
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    alphas = x[:N_SEGMENTS]
    betas = x[N_SEGMENTS:]
    segment_duration = _segment_duration_tu()
    state = state_initial.copy()
    for alpha, beta in zip(alphas, betas, strict=True):

        def thrust_fn(_t, _s, a=alpha, b=beta):
            return thrust_canonical, a, b

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


def position_error_squared(x: np.ndarray, state_initial: np.ndarray, r_target: np.ndarray) -> float:
    state = terminal_state(x, state_initial, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)
    return float(np.sum((state[0:3] - r_target) ** 2))


def solve(x0: np.ndarray | None = None) -> np.ndarray:
    """Optimiza `[alpha_1..alpha_N, beta_1..beta_N]` minimizando el
    error cuadratico de posicion final contra Marte en `ARRIVAL`."""
    state_initial, r_target = boundary_states()
    if x0 is None:
        x0 = np.zeros(2 * N_SEGMENTS)
    bounds = [(-ALPHA_BETA_BOUND_RAD, ALPHA_BETA_BOUND_RAD)] * (2 * N_SEGMENTS)
    result = minimize(
        position_error_squared,
        x0,
        args=(state_initial, r_target),
        method="SLSQP",
        bounds=bounds,
        options={"maxiter": 300, "ftol": 1e-13},
    )
    if not result.success:
        raise RuntimeError(f"SLSQP no convergio: {result.message}")
    return result.x


def simulate(x: np.ndarray):
    """Re-propaga con tolerancia fina; devuelve `(trajectory,
    segment_of_row, thrust_canonical, state_initial)`."""
    state_initial, _r_target = boundary_states()
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    alphas = x[:N_SEGMENTS]
    betas = x[N_SEGMENTS:]
    segment_duration = _segment_duration_tu()
    state = state_initial.copy()

    trajectory_rows = [state]
    segment_of_row = [0]
    for segment_idx, (alpha, beta) in enumerate(zip(alphas, betas, strict=True)):

        def thrust_fn(_t, _s, a=alpha, b=beta):
            return thrust_canonical, a, b

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

    return np.array(trajectory_rows), np.array(segment_of_row), thrust_canonical, state_initial


def render(
    x: np.ndarray,
    trajectory: np.ndarray,
    segment_of_row: np.ndarray,
    thrust_canonical: float,
) -> Path:
    alphas = x[:N_SEGMENTS]
    betas = x[N_SEGMENTS:]

    r_transfer = trajectory[:, 0:2]  # proyeccion x-y; el modulo si es 3D (ver trajectory[:,2])
    thrust_vectors = np.zeros((len(trajectory), 2))
    for idx in range(len(trajectory)):
        alpha = alphas[segment_of_row[idx]]
        beta = betas[segment_of_row[idx]]
        r_vec = trajectory[idx, 0:3]
        v_vec = trajectory[idx, 3:6]
        thrust_vectors[idx] = thrust_canonical * thrust_direction(r_vec, v_vec, alpha, beta)[0:2]

    theta = np.linspace(0.0, 2.0 * np.pi, 200)
    r_earth_ring = np.column_stack(
        [np.cos(theta), np.sin(theta)]
    )  # referencia visual, no la orbita real
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
    fig.axes[0].set_title("E4 -- real 3D ephemerides, fixed dates (x-y projection)")

    out_path = Path(__file__).parent / "e4_real_ephemerides.png"
    fig.savefig(out_path, dpi=150)
    return out_path


if __name__ == "__main__":
    _state_initial, r_target = boundary_states()
    print(f"departure={DEPARTURE.date()}  arrival={ARRIVAL.date()}  TOF={TOF_DAYS} days")

    x_opt = solve()
    trajectory, segment_of_row, thrust_canonical, state_initial = simulate(x_opt)
    final = trajectory[-1]

    position_error_km = np.linalg.norm(final[0:3] - r_target) * DU_KM
    print(f"position error = {position_error_km:.1f} km (tolerance {POSITION_TOLERANCE_KM} km)")
    print(f"mass_ratio (m_f/m_0) = {final[6]:.4f}")
    print(f"final z = {final[2] * DU_KM:.0f} km (out-of-plane component, nonzero by construction)")

    out_path = render(x_opt, trajectory, segment_of_row, thrust_canonical)
    print(f"saved {out_path}")
