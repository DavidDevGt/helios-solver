"""T-0.6: conservacion de energia sin empuje.

Criterio: deriva relativa de energia < 1e-10 en 1 anio simulado con
DOP853 (rtol=1e-12). Este test debe pasar antes de anadir empuje a la
dinamica (T-1.1).
"""

import pytest

ENERGY_DRIFT_TOLERANCE = 1e-10
INTEGRATION_RTOL = 1e-12


@pytest.mark.skip(reason="Pendiente: requiere dynamics.py (T-1.1) implementado.")
def test_energy_conservation_no_thrust():
    pass
