"""T-0.5: Hohmann heliocentrico impulsivo Tierra->Marte.

Oraculo de todo el proyecto (PLAN.md sec. 2, Gate 0->1): si esto no
cierra al 1%, hay un bug de unidades o de signo y nada de lo que sigue
importa.

Deliberadamente NO usa ephemeris.py: el propio PLAN.md fija los valores
de referencia para orbitas *circulares coplanares* idealizadas
(r_tierra = 1 AU, r_marte = 1.524 AU), no para la posicion instantanea
real de los planetas (cuya excentricidad -- ~0.093 en Marte -- movera el
resultado bastante mas alla del 1% de tolerancia). Es un calculo
cerrado de vis-viva, independiente del resto del pipeline.

Valores de referencia (calculados con orbitas circulares coplanares,
r_tierra = 1 AU, r_marte = 1.524 AU):
    dv_salida  ~= 2.94 km/s
    dv_llegada ~= 2.65 km/s
    dv_total   ~= 5.6  km/s
    tof        ~= 259 dias
"""

import numpy as np
import pytest

from helios.constants import AU_KM, DAY_S, MARS_SEMI_MAJOR_AXIS_AU, MU_SUN

DV_SALIDA_REF_KM_S = 2.94
DV_LLEGADA_REF_KM_S = 2.65
DV_TOTAL_REF_KM_S = 5.6
TOF_REF_DAYS = 259
TOLERANCE = 0.01


def _hohmann_transfer(r1_km: float, r2_km: float, mu_km3_s2: float) -> tuple[float, float, float]:
    """Delta-v de salida/llegada y tiempo de vuelo de una transferencia de
    Hohmann entre dos orbitas circulares coplanares de radios r1 -> r2.

    Returns:
        (dv_departure_km_s, dv_arrival_km_s, tof_s)
    """
    v1_circular = np.sqrt(mu_km3_s2 / r1_km)
    v2_circular = np.sqrt(mu_km3_s2 / r2_km)

    a_transfer = (r1_km + r2_km) / 2.0
    v_periapsis = np.sqrt(mu_km3_s2 * (2.0 / r1_km - 1.0 / a_transfer))
    v_apoapsis = np.sqrt(mu_km3_s2 * (2.0 / r2_km - 1.0 / a_transfer))

    dv_departure = v_periapsis - v1_circular
    dv_arrival = v2_circular - v_apoapsis
    tof_s = np.pi * np.sqrt(a_transfer**3 / mu_km3_s2)
    return dv_departure, dv_arrival, tof_s


def test_hohmann_delta_v():
    r1 = AU_KM
    r2 = MARS_SEMI_MAJOR_AXIS_AU * AU_KM
    dv_departure, dv_arrival, _tof_s = _hohmann_transfer(r1, r2, MU_SUN)
    dv_total = dv_departure + dv_arrival

    assert dv_departure == pytest.approx(DV_SALIDA_REF_KM_S, rel=TOLERANCE)
    assert dv_arrival == pytest.approx(DV_LLEGADA_REF_KM_S, rel=TOLERANCE)
    assert dv_total == pytest.approx(DV_TOTAL_REF_KM_S, rel=TOLERANCE)


def test_hohmann_time_of_flight():
    r1 = AU_KM
    r2 = MARS_SEMI_MAJOR_AXIS_AU * AU_KM
    _dv_departure, _dv_arrival, tof_s = _hohmann_transfer(r1, r2, MU_SUN)
    tof_days = tof_s / DAY_S

    assert tof_days == pytest.approx(TOF_REF_DAYS, rel=TOLERANCE)
