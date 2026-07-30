"""EDOs del problema: gravedad solar + empuje continuo + consumo de masa.

Estado x = [r (3,), v (3,), m (1,)]. Control u = [T, alpha, beta].
Unidades canonicas (D-3, ver constants.py): DU = 1 AU, TU tal que mu_sol = 1.

Convencion de direccion de empuje: `alpha`/`beta` son angulos de cono en el
marco RTN local (Radial-Transverse-Normal, definido por `_rtn_frame`),
la misma parametrizacion que usa el `sims_flanagan` de pykep y es estandar
en la literatura de bajo empuje (p.ej. GTOC). `alpha` es el angulo en el
plano orbital medido desde la direccion transversal T (la direccion de
"empuje tangencial" que T-1.1 usa como caso de prueba: alpha=beta=0);
`beta` es el angulo fuera del plano medido desde ese plano hacia N.

Convencion de unidades canonicas de masa/fuerza (no fijada en constants.py
porque depende de la masa inicial m0 de cada problema, no es una constante
universal): la unidad de masa canonica MU = m0 [kg] de la nave, de modo que
el `m` del estado es la fraccion m/m0 (arranca en 1.0). La unidad de fuerza
canonica correspondiente es MU*DU/TU^2 (convertido a Newtons via DU en
metros); ver `thrust_to_canonical` para el conversor SI -> canonico que se
usa en la frontera (D-3: SI solo en I/O, canonico dentro del solver).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .constants import DU_KM, G0_KM_S2, TU_S

# g0 en unidades canonicas de aceleracion (DU/TU^2). Ver derivacion en el
# docstring del modulo: mantiene todo el sistema (G0_KM_S2 en km/s^2,
# DU_KM en km, TU_S en s) en la misma base de km, sin mezclar con metros.
G0_CANONICAL = G0_KM_S2 * TU_S**2 / DU_KM

ThrustFn = Callable[[float, np.ndarray], tuple[float, float, float]]


def thrust_to_canonical(thrust_n: float, m0_kg: float) -> float:
    """Convierte un empuje en Newtons a unidades canonicas de fuerza.

    Frontera SI -> canonico (D-3): usar esto para construir el `T` que
    `thrust_fn` le entrega a `equations_of_motion`, nunca pasar Newtons
    directamente al integrador.

    Args:
        thrust_n: empuje [N].
        m0_kg: masa inicial de la nave [kg] -- define la unidad de masa
            canonica de este problema.

    Returns:
        Empuje en unidades canonicas de fuerza (MU*DU/TU^2).
    """
    canonical_force_unit_n = m0_kg * (DU_KM * 1000.0) / TU_S**2
    return thrust_n / canonical_force_unit_n


def zero_thrust(_t: float, _state: np.ndarray) -> tuple[float, float, float]:
    """`thrust_fn` trivial para el caso sin empuje (T-0.6)."""
    return 0.0, 0.0, 0.0


def constant_tangential_thrust(thrust_canonical: float) -> ThrustFn:
    """Fabrica un `thrust_fn` de empuje constante puramente tangencial.

    Caso de prueba de T-1.1: con esto la energia debe crecer de forma
    monotona (el empuje siempre tiene componente positiva a lo largo de la
    velocidad orbital).
    """

    def thrust_fn(_t: float, _state: np.ndarray) -> tuple[float, float, float]:
        return thrust_canonical, 0.0, 0.0

    return thrust_fn


def _rtn_frame(r: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Marco local Radial-Transverse-Normal (unitario, ortonormal)."""
    r_hat = r / np.linalg.norm(r)
    h = np.cross(r, v)
    n_hat = h / np.linalg.norm(h)
    t_hat = np.cross(n_hat, r_hat)
    return r_hat, t_hat, n_hat


def thrust_direction(r: np.ndarray, v: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """Vector unitario de empuje a partir de los angulos de cono RTN.

    Publica (no solo de uso interno) porque viz.py / los scripts de
    benchmarks necesitan reconstruir el vector de empuje 3D real a partir
    de (T, alpha, beta) para dibujar las flechas de LA IMAGEN.
    """
    r_hat, t_hat, n_hat = _rtn_frame(r, v)
    return np.cos(beta) * (np.cos(alpha) * t_hat + np.sin(alpha) * r_hat) + np.sin(beta) * n_hat


def equations_of_motion(
    t: float,
    state: np.ndarray,
    thrust_fn: ThrustFn,
    isp_s: float,
    mu: float = 1.0,
) -> np.ndarray:
    """d(state)/dt para integrar con scipy.integrate.solve_ivp.

    Args:
        t: tiempo actual (unidades canonicas, TU).
        state: [rx, ry, rz, vx, vy, vz, m] (DU, DU/TU, masa canonica).
        thrust_fn: callable(t, state) -> (T, alpha, beta); T en unidades
            canonicas de fuerza.
        isp_s: impulso especifico [s], se convierte internamente a TU.
        mu: parametro gravitacional canonico (1.0 por definicion de DU/TU).

    Returns:
        d(state)/dt, mismo shape que `state`.
    """
    r = state[0:3]
    v = state[3:6]
    m = state[6]

    r_norm = np.linalg.norm(r)
    a_grav = -mu * r / r_norm**3

    thrust, alpha, beta = thrust_fn(t, state)
    if thrust > 0.0 and m > 0.0:
        u_hat = thrust_direction(r, v, alpha, beta)
        a_thrust = (thrust / m) * u_hat
        isp_tu = isp_s / TU_S
        m_dot = -thrust / (isp_tu * G0_CANONICAL)
    else:
        a_thrust = np.zeros(3)
        m_dot = 0.0

    v_dot = a_grav + a_thrust
    return np.concatenate([v, v_dot, [m_dot]])
