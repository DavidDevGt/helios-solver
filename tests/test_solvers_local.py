"""T-1.3: wrapper SLSQP + validacion de gradientes por diferencias finitas.

Dos cosas separadas, ambas parte del criterio de aceptacion de T-1.3:
1. `solve_slsqp` converge en un caso trivial con solucion analitica
   conocida (valida el wrapper en si).
2. El patron de validacion "diferencias finitas vs. derivada analitica en
   un caso trivial" que se reutilizara cuando el objetivo/restricciones
   reales del problema de trayectoria (E1/E2 en adelante) tengan
   gradientes propios.
"""

import numpy as np
import pytest
from scipy.optimize import approx_fprime

from helios.solvers.local import solve_slsqp


def test_solve_slsqp_trivial_equality_constrained_qp():
    # min x^2 + y^2  s.t.  x + y = 1  ->  optimo analitico en (0.5, 0.5).
    def objective(x):
        return x[0] ** 2 + x[1] ** 2

    constraints = [{"type": "eq", "fun": lambda x: x[0] + x[1] - 1.0}]
    x0 = np.array([0.0, 1.0])

    x_opt = solve_slsqp(objective, constraints, x0)

    assert np.allclose(x_opt, [0.5, 0.5], atol=1e-6)


def test_solve_slsqp_raises_on_non_convergence():
    # x=1 y x=2 simultaneas: infeasible por construccion, SLSQP debe
    # reportar result.success=False y solve_slsqp debe convertir eso en
    # una excepcion en vez de devolver silenciosamente un x sin sentido.
    constraints = [
        {"type": "eq", "fun": lambda x: x[0] - 1.0},
        {"type": "eq", "fun": lambda x: x[0] - 2.0},
    ]
    with pytest.raises(RuntimeError, match="no convergio"):
        solve_slsqp(lambda x: x[0] ** 2, constraints, np.array([0.0]))


def test_finite_difference_gradient_matches_analytical_on_trivial_case():
    def f(x):
        return x[0] ** 2 * x[1] + np.sin(x[1])

    def grad_f_analytical(x):
        return np.array([2.0 * x[0] * x[1], x[0] ** 2 + np.cos(x[1])])

    x_test = np.array([1.3, -0.7])
    grad_fd = approx_fprime(x_test, f, epsilon=1e-6)
    grad_analytical = grad_f_analytical(x_test)

    assert np.allclose(grad_fd, grad_analytical, atol=1e-5)
