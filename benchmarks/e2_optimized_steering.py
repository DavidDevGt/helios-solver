"""E2 (PLAN.md sec. 3, escalera de realismo): 2D, direccion de empuje
variable (control discretizado), tiempo de vuelo fijo.

A diferencia de E1 (empuje tangencial fijo), aqui la direccion de empuje
`alpha` es una variable de decision por segmento -- el thrust magnitude
sigue fijo en T_max ("empuje constante" en el sentido de PLAN.md sec. 3;
solo la *direccion* varia, tal como dice el nombre de E2). Con el
thrust siempre encendido a T_max, la masa consumida es independiente del
perfil de direccion, asi que "masa final" no es un objetivo util aqui.

Formulacion (la forma estandar de plantear este tipo de problema, no una
eleccion arbitraria): **minimizar el esfuerzo de control**
`sum(alpha_i^2)` **sujeto a** dos restricciones de igualdad duras --
radio final = radio de Marte, rapidez final = velocidad circular en ese
radio (insercion cuasi-circular, no solo cruzar el radio como hacia E1).
Con restricciones duras via SLSQP en vez de un residuo blando en el
objetivo, la convergencia es mucho mas precisa (error de radio/velocidad
~1e-10 en unidades canonicas, contra ~1e-6 de una version anterior con
penalizacion blanda).

**Hallazgo importante (auditoria, ver PLAN.md / docs): el optimo NO es
unico.** El problema tiene 2 restricciones y 8 variables de control -- un
subespacio de soluciones de 6 grados de libertad. Probado con tres
formulaciones distintas del objetivo (feasibilidad pura, penalizacion
blanda a tres pesos, y esta version de restricciones duras), semillas
distintas convergen de forma repetible y precisa a las restricciones
(objetivo/residuo ~0 en las tres formulaciones) pero a **perfiles de
direccion distintos** entre si (hasta ~240 grados de diferencia punto a
punto). Esto no es un bug de esta implementacion: es exactamente la
no-convexidad que IDEA.md sec. 2 anticipa ("miles de minimos locales"),
y es la razon de ser de T-1.5 (multi-start) y de la Fase 2 (busqueda
global con pygmo) -- un solo SLSQP local no alcanza para explorar el
espacio de soluciones, solo para converger a *una* de ellas de forma
confiable. Ver tests/test_e2_scenario.py para la verificacion permanente
de ambos hechos (convergencia confiable Y no-unicidad).

Caso de referencia (igual que E1, PLAN.md sec. 3): Isp = 3000 s,
T_max = 0.5 N, m0 = 1000 kg, TOF = 180 dias (mismo TOF que E1, para
comparar de forma directa el beneficio de optimizar la direccion).

Uso: `uv run python benchmarks/e2_optimized_steering.py`
Genera: benchmarks/e2_optimized_steering.png
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
TOF_DAYS = 180.0
N_SEGMENTS = 8
N_PLOT_POINTS_PER_SEGMENT = 50

# Tolerancia de integracion *durante la busqueda* (SLSQP llama al
# objetivo cientos de veces; una tolerancia mas floja aqui es
# deliberada -- ver docs/numerical-methods.md sec 2). La verificacion
# final (render/tests) re-integra con tolerancia mas fina.
SEARCH_RTOL = 1e-8
SEARCH_ATOL = 1e-10
VERIFY_RTOL = 1e-11
VERIFY_ATOL = 1e-13


def _segment_duration_tu() -> float:
    return (TOF_DAYS * DAY_S / TU_S) / N_SEGMENTS


def v_circular_at_mars() -> float:
    return np.sqrt(1.0 / MARS_SEMI_MAJOR_AXIS_AU)  # canonico, mu=1


def terminal_state(alphas: np.ndarray, *, rtol: float, atol: float) -> np.ndarray:
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    segment_duration = _segment_duration_tu()
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


def radius_constraint(alphas: np.ndarray) -> float:
    state = terminal_state(alphas, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)
    return np.linalg.norm(state[0:3]) - MARS_SEMI_MAJOR_AXIS_AU


def speed_constraint(alphas: np.ndarray) -> float:
    state = terminal_state(alphas, rtol=SEARCH_RTOL, atol=SEARCH_ATOL)
    return np.linalg.norm(state[3:6]) - v_circular_at_mars()


def control_effort(alphas: np.ndarray) -> float:
    """Objetivo primario: minimizar el esfuerzo de direccion, sujeto a
    las restricciones de insercion cuasi-circular (ver docstring del
    modulo). No hay un unico minimizador -- ver el hallazgo de la
    auditoria arriba."""
    return float(np.sum(alphas**2))


def solve(x0: np.ndarray | None = None) -> np.ndarray:
    """Optimiza el perfil de direccion `alpha_i` (minimo esfuerzo sujeto
    a insercion cuasi-circular en Marte); devuelve los angulos (rad)."""
    if x0 is None:
        x0 = np.zeros(N_SEGMENTS)
    constraints = [
        {"type": "eq", "fun": radius_constraint},
        {"type": "eq", "fun": speed_constraint},
    ]
    return solve_slsqp(
        control_effort,
        constraints,
        x0,
        bounds=[(-np.pi, np.pi)] * N_SEGMENTS,
        options={"maxiter": 300, "ftol": 1e-12},
    )


def simulate(alphas: np.ndarray):
    """Re-propaga la solucion optimizada con tolerancia fina y devuelve
    `(trajectory, segment_of_row, thrust_canonical)` para verificacion /
    graficado. `segment_of_row[i]` es el indice de segmento que produjo
    la fila `trajectory[i]` (para poder reconstruir el vector de empuje
    real en cada punto al graficar)."""
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    segment_duration = _segment_duration_tu()
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
        new_rows = sol.y[:, 1:].T  # sin el primer punto: duplica el ultimo del segmento anterior
        trajectory_rows.extend(new_rows)
        segment_of_row.extend([segment_idx] * len(new_rows))
        state = sol.y[:, -1]

    return np.array(trajectory_rows), np.array(segment_of_row), thrust_canonical


def render(
    alphas: np.ndarray, trajectory: np.ndarray, segment_of_row: np.ndarray, thrust_canonical: float
) -> Path:
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
        arrival_date=f"t0 + {TOF_DAYS:.0f} d",
        delta_v_km_s=delta_v_km_s,
        mass_ratio=mass_ratio,
        tof_days=TOF_DAYS,
    )
    fig.axes[0].set_title("E2 -- SLSQP-optimized steering (quasi-circular insertion)")

    out_path = Path(__file__).parent / "e2_optimized_steering.png"
    fig.savefig(out_path, dpi=150)
    return out_path


if __name__ == "__main__":
    segment_duration = _segment_duration_tu()
    print(f"segments={N_SEGMENTS}  segment_duration={segment_duration:.4f} TU")

    alphas_opt = solve()
    print("alpha (deg):", np.degrees(alphas_opt))

    trajectory, segment_of_row, thrust_canonical = simulate(alphas_opt)
    final = trajectory[-1]
    r_final = np.linalg.norm(final[0:3])
    v_final = np.linalg.norm(final[3:6])
    print(f"r_final = {r_final:.6f} DU (Mars = {MARS_SEMI_MAJOR_AXIS_AU} DU)")
    print(f"v_final = {v_final:.6f} DU/TU (circular target = {v_circular_at_mars():.6f})")
    print(f"mass_ratio (m_f/m_0) = {final[6]:.4f}")

    out_path = render(alphas_opt, trajectory, segment_of_row, thrust_canonical)
    print(f"saved {out_path}")
