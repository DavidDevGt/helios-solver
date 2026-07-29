"""T-0.5: Hohmann heliocentrico impulsivo Tierra->Marte.

Oraculo de todo el proyecto (PLAN.md sec. 2, Gate 0->1): si esto no
cierra al 1%, hay un bug de unidades o de signo y nada de lo que sigue
importa.

Valores de referencia (calculados con orbitas circulares coplanares,
r_tierra = 1 AU, r_marte = 1.524 AU):
    dv_salida  ~= 2.94 km/s
    dv_llegada ~= 2.65 km/s
    dv_total   ~= 5.6  km/s
    tof        ~= 259 dias
"""

import pytest

DV_SALIDA_REF_KM_S = 2.94
DV_LLEGADA_REF_KM_S = 2.65
DV_TOTAL_REF_KM_S = 5.6
TOF_REF_DAYS = 259
TOLERANCE = 0.01


@pytest.mark.skip(reason="Pendiente: requiere ephemeris.py (T-0.4) implementado (D-1).")
def test_hohmann_delta_v():
    pass


@pytest.mark.skip(reason="Pendiente: requiere ephemeris.py (T-0.4) implementado (D-1).")
def test_hohmann_time_of_flight():
    pass
