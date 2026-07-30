"""LA IMAGEN (T-1.8): espiral de transferencia + vectores de empuje.

Vista polar del plano de la eclíptica (es decir, vista "desde el polo":
proyección x-y en el marco eclíptico, no necesariamente los ejes polares
de matplotlib -- ver la nota de implementación más abajo): orbitas de
Tierra/Marte en gris, espiral en color, flechas de empuje escaladas por
magnitud, y anotaciones (fechas, dv efectivo, m_f/m_0, TOF).
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
        thrust_vectors: direccion/magnitud de empuje a lo largo de
            r_transfer, mismo largo M. Puede ser un array vacio (M=0) para
            trayectorias sin empuje (coasting puro).
        departure_date, arrival_date: para las anotaciones.
        delta_v_km_s, mass_ratio, tof_days: metricas para las anotaciones.

    Returns:
        Figura de matplotlib lista para `savefig("benchmarks/m1_spiral.png")`.
    """
    fig = Figure(figsize=(8, 8))
    ax = fig.add_subplot(111)

    ax.plot(r_earth[:, 0], r_earth[:, 1], color="0.6", lw=1.0, label="Earth orbit")
    ax.plot(r_mars[:, 0], r_mars[:, 1], color="0.4", lw=1.0, label="Mars orbit")
    ax.plot(
        r_transfer[:, 0], r_transfer[:, 1], color="tab:orange", lw=2.0, label="Transfer trajectory"
    )

    ax.scatter([0.0], [0.0], color="gold", edgecolor="k", s=200, marker="*", zorder=5, label="Sun")
    ax.scatter(
        [r_transfer[0, 0]], [r_transfer[0, 1]], color="tab:blue", s=50, zorder=5, label="Departure"
    )
    ax.scatter(
        [r_transfer[-1, 0]], [r_transfer[-1, 1]], color="tab:red", s=50, zorder=5, label="Arrival"
    )

    if thrust_vectors is not None and len(thrust_vectors) > 0:
        n_points = len(r_transfer)
        stride = max(1, n_points // 40)
        magnitudes = np.linalg.norm(thrust_vectors, axis=1)
        max_magnitude = magnitudes.max()
        if max_magnitude > 0:
            span = max(np.ptp(r_transfer[:, 0]), np.ptp(r_transfer[:, 1]))
            scale = 0.12 * span / max_magnitude
            ax.quiver(
                r_transfer[::stride, 0],
                r_transfer[::stride, 1],
                thrust_vectors[::stride, 0] * scale,
                thrust_vectors[::stride, 1] * scale,
                color="tab:green",
                angles="xy",
                scale_units="xy",
                scale=1,
                width=0.004,
                label="Thrust",
                zorder=4,
            )

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x [AU]")
    ax.set_ylabel("y [AU]")
    ax.set_title("Low-thrust transfer trajectory")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)

    annotation = (
        f"Departure: {departure_date}\n"
        f"Arrival: {arrival_date}\n"
        f"$\\Delta v_{{eff}} \\approx$ {delta_v_km_s:.2f} km/s\n"
        f"$m_f/m_0$ = {mass_ratio:.1%}\n"
        f"TOF $\\approx$ {tof_days:.0f} d"
    )
    ax.text(
        0.02,
        0.98,
        annotation,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )

    fig.tight_layout()
    return fig
