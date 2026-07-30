"""Regresion para E1 (PLAN.md sec. 3, escalera de realismo).

No es un criterio de aceptacion propio de una tarea del PLAN (E1 no
tiene un T-x.y dedicado, es el primer escalon de T-1.4), pero
`benchmarks/e1_constant_tangential_thrust.py` es la primera trayectoria
real que produce el pipeline -- generar la figura de un escalon sin un
test que lo respalde va contra la regla de T-1.4/DoD de que nada cuenta
como resuelto si no es verificable.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))
import e1_constant_tangential_thrust as e1  # noqa: E402

RADIUS_TOLERANCE_DU = 0.01
# Regresion contra el valor medido al fijar TOF_DAYS=180 (ver el modulo):
# no es un criterio fisico independiente, es una guarda para detectar si
# un cambio futuro en dynamics.py mueve el resultado sin querer.
EXPECTED_MASS_RATIO = 0.736


def test_e1_reaches_mars_orbital_radius():
    sol, _thrust_canonical = e1.simulate()
    r_final = np.linalg.norm(sol.y[0:3, -1])

    assert abs(r_final - e1.MARS_SEMI_MAJOR_AXIS_AU) < RADIUS_TOLERANCE_DU
    # Coplanar por construccion (RTN de un estado inicial con z=0, vz=0,
    # empuje sin componente beta no puede sacar la trayectoria del plano).
    assert abs(sol.y[2, -1]) < 1e-10


def test_e1_mass_consumption_is_physically_sane():
    sol, _thrust_canonical = e1.simulate()
    mass_ratio = sol.y[6, -1]

    # No deberia quedarse sin propelente a mitad de camino (E1 no esta
    # optimizado, pero el caso de referencia de PLAN.md sec. 3 asume que
    # SI llega con margen) ni "gastar" masa negativa ni de mas.
    assert 0.0 < mass_ratio < 1.0
    assert mass_ratio == pytest.approx(EXPECTED_MASS_RATIO, abs=0.01)
