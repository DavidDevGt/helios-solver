"""LA IMAGEN (T-1.8): espiral de transferencia + vectores de empuje.

Vista polar del plano de la ecliptica: orbitas de Tierra/Marte en gris,
espiral en color, flechas de empuje escaladas por magnitud, y
anotaciones (fechas, dv efectivo, m_f/m_0, TOF).
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure


def plot_trajectory(
    r_earth: np.ndarray,
    r_mars: np.ndarray,
    r_transfer: np.ndarray,
    thrust_vectors: np.ndarray,
    *,
    departure_date: str,
    arrival_date: str,
    delta_v_km_s: float,
    mass_ratio: float,
    tof_days: float,
) -> Figure:
    """Genera la figura de la espiral convergida.

    Args:
        r_earth, r_mars: orbitas de referencia (N, 2) o (N, 3).
        r_transfer: trayectoria optimizada (M, 2) o (M, 3).
        thrust_vectors: direccion/magnitud de empuje a lo largo de r_transfer.
        departure_date, arrival_date: para las anotaciones.
        delta_v_km_s, mass_ratio, tof_days: metricas para las anotaciones.

    Returns:
        Figura de matplotlib lista para `savefig("benchmarks/m1_spiral.png")`.
    """
    raise NotImplementedError("Pendiente T-1.8: implementar tras converger E5.")
