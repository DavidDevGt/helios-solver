"""Smoke test para viz.plot_trajectory (parte de T-1.8).

No valida contenido visual (eso lo hace la inspeccion humana de la
figura versionada en benchmarks/), solo que la funcion no rompe con
entradas de forma razonable y que produce los elementos que el DoD pide:
la figura debe poder guardarse.
"""

import numpy as np

from helios.viz import plot_trajectory


def test_plot_trajectory_smoke():
    theta = np.linspace(0.0, 2.0 * np.pi, 50)
    r_earth = np.column_stack([np.cos(theta), np.sin(theta)])
    r_mars = 1.524 * np.column_stack([np.cos(theta), np.sin(theta)])
    r_transfer = np.column_stack([np.linspace(1.0, 1.5, 30), np.linspace(0.0, 0.5, 30)])
    thrust_vectors = np.tile([0.01, 0.0], (30, 1))

    fig = plot_trajectory(
        r_earth,
        r_mars,
        r_transfer,
        thrust_vectors,
        departure_date="2026-01-01",
        arrival_date="2026-07-01",
        delta_v_km_s=5.6,
        mass_ratio=0.8,
        tof_days=180.0,
    )

    assert len(fig.axes) == 1
    assert fig.axes[0].has_data()


def test_plot_trajectory_smoke_without_thrust():
    theta = np.linspace(0.0, 2.0 * np.pi, 50)
    r_earth = np.column_stack([np.cos(theta), np.sin(theta)])
    r_mars = 1.524 * np.column_stack([np.cos(theta), np.sin(theta)])
    r_transfer = np.column_stack([np.linspace(1.0, 1.5, 30), np.linspace(0.0, 0.5, 30)])

    fig = plot_trajectory(
        r_earth,
        r_mars,
        r_transfer,
        np.empty((0, 2)),
        departure_date="2026-01-01",
        arrival_date="2026-07-01",
        delta_v_km_s=5.6,
        mass_ratio=0.8,
        tof_days=180.0,
    )

    assert fig.axes[0].has_data()
