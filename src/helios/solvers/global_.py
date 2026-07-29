"""Busqueda global con pygmo: archipielago de islas en paralelo (T-2.1/T-2.2).

El mismo problema debe correr en solvers/local.py (SLSQP/IPOPT) y aqui
sin duplicar la definicion de objetivo/restricciones (T-2.1).
"""

from __future__ import annotations


class TrajectoryProblem:
    """Envoltorio compatible con la interfaz `pygmo.problem`."""

    def fitness(self, x):
        raise NotImplementedError("Pendiente T-2.1: envolver transcription.py + dynamics.py.")

    def get_bounds(self):
        raise NotImplementedError("Pendiente T-2.1.")


def run_archipelago(problem: TrajectoryProblem, n_islands: int, generations: int):
    """Corre un archipielago (DE / self-adaptive DE / CMA-ES) con migracion (T-2.2)."""
    raise NotImplementedError("Pendiente T-2.2: configuracion en YAML.")
