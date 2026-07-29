"""Constantes fisicas. Toda constante cita su fuente (DoD, PLAN.md sec. 8).

Unidades SI salvo que se indique lo contrario (D-3: el solver interno
trabaja en unidades canonicas adimensionales, definidas mas abajo).
"""

# Parametro gravitacional estandar del Sol, GM_sol [km^3/s^2].
# Fuente: JPL DE440 / IAU 2015 nominal solar mass parameter.
MU_SUN = 1.32712440018e11

# Unidad astronomica [km]. Fuente: definicion IAU 2012.
AU_KM = 149_597_870.7

# Segundos por dia solar medio [s].
DAY_S = 86_400.0

# Gravedad estandar g0, usada en la ecuacion del cohete (Tsiolkovsky) [km/s^2].
# Fuente: CODATA / definicion ISO de standard gravity (9.80665 m/s^2).
G0_KM_S2 = 9.80665e-3

# --- Unidades canonicas (D-3) ---
# TU: unidad de tiempo canonica tal que mu_sun = 1 en unidades DU^3/TU^2
# con DU = AU_KM. Se define y usa en dynamics.py / transcription.py.
DU_KM = AU_KM
TU_S = (DU_KM**3 / MU_SUN) ** 0.5
