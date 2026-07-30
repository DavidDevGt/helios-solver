"""E1 (PLAN.md sec. 3, escalera de realismo): 2D, orbitas circulares
coplanares, empuje constante, tiempo de vuelo fijo.

No hay optimizacion aqui -- E1 es deliberadamente la simulacion mas
simple posible: empuje tangencial constante (magnitud Y direccion fijas)
desde la orbita circular de la Tierra, integrado hacia adelante con la
EDO real de dynamics.py. Sirve para validar que la maquinaria (dynamics +
viz) produce una espiral fisicamente sensata antes de introducir
cualquier NLP (E2 en adelante).

Caso de referencia (PLAN.md sec. 3): Isp = 3000 s, T_max = 0.5 N,
m0 = 1000 kg. El TOF (180 dias) se eligio por busqueda directa como el
punto en el que esta espiral *naive* cruza el radio orbital de Marte
-- no es una optimizacion, es una eleccion deliberada para que la
primera figura de la escalera sea legible. El cruce de radio NO es un
rendezvous (posicion y velocidad reales de Marte); eso es exactamente lo
que E4/E5 tienen que resolver con un NLP real.

Uso: `uv run python benchmarks/e1_constant_tangential_thrust.py`
Genera: benchmarks/e1_constant_tangential_thrust.png
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from helios.constants import DAY_S, G0_KM_S2, MARS_SEMI_MAJOR_AXIS_AU, TU_S
from helios.dynamics import (
    constant_tangential_thrust,
    equations_of_motion,
    thrust_direction,
    thrust_to_canonical,
)
from helios.viz import plot_trajectory

ISP_S = 3000.0
T_MAX_N = 0.5
M0_KG = 1000.0
TOF_DAYS = 180.0
N_PLOT_POINTS = 400


def simulate():
    """Corre la propagacion de E1 y devuelve `(sol, thrust_canonical)`.

    Separado de `render()` para que tests/test_e1_scenario.py pueda
    verificar la fisica sin tocar el disco.
    """
    thrust_canonical = thrust_to_canonical(T_MAX_N, M0_KG)
    thrust_fn = constant_tangential_thrust(thrust_canonical)

    state0 = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0])
    tof_tu = TOF_DAYS * DAY_S / TU_S
    t_eval = np.linspace(0.0, tof_tu, N_PLOT_POINTS)

    sol = solve_ivp(
        equations_of_motion,
        t_span=(0.0, tof_tu),
        y0=state0,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        args=(thrust_fn, ISP_S, 1.0),
        t_eval=t_eval,
    )
    if not sol.success:
        raise RuntimeError(f"E1 propagation failed: {sol.message}")
    return sol, thrust_canonical


def render(sol, thrust_canonical) -> Path:
    """Construye LA figura de E1 y la guarda en benchmarks/."""
    r_transfer = sol.y[0:2, :].T  # (N, 2), AU (canonical DU == AU)
    thrust_vectors = np.array(
        [
            thrust_canonical * thrust_direction(sol.y[0:3, i], sol.y[3:6, i], 0.0, 0.0)[0:2]
            for i in range(sol.y.shape[1])
        ]
    )

    theta = np.linspace(0.0, 2.0 * np.pi, 200)
    r_earth = np.column_stack([np.cos(theta), np.sin(theta)])
    r_mars = MARS_SEMI_MAJOR_AXIS_AU * np.column_stack([np.cos(theta), np.sin(theta)])

    mass_ratio = sol.y[6, -1]
    # Delta-v efectivo via Tsiolkovsky (independiente de la forma de la
    # trayectoria; ver docs/numerical-methods.md sec. 1) -- no la
    # diferencia de velocidades instantaneas, que no tiene ese significado.
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
    fig.axes[0].set_title("E1 -- constant tangential thrust (no optimization)")

    out_path = Path(__file__).parent / "e1_constant_tangential_thrust.png"
    fig.savefig(out_path, dpi=150)
    return out_path


if __name__ == "__main__":
    sol, thrust_canonical = simulate()
    r_final = np.linalg.norm(sol.y[0:3, -1])
    print(f"r_final = {r_final:.4f} DU (Mars = {MARS_SEMI_MAJOR_AXIS_AU} DU)")
    print(f"mass_ratio (m_f/m_0) = {sol.y[6, -1]:.3f}")
    out_path = render(sol, thrust_canonical)
    print(f"saved {out_path}")
