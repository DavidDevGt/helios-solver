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

# --- Marco de referencia (usado en ephemeris.py) ---
# Oblicuidad media de la eclíptica en J2000.0: 84381.448 arcsec.
# Fuente: IAU 1976 (Lieske et al.), el mismo valor que usa JPL Horizons para
# su marco "Ecliptic of J2000.0" (ECLIPJ2000) -- verificado por
# comparacion directa contra Horizons en tests/test_ephemeris.py.
ECLIPTIC_OBLIQUITY_J2000_DEG = 84381.448 / 3600.0

# Offset fijo TT - UTC = (TAI - UTC) + 32.184 s = 37 s + 32.184 s.
# Fuente: IERS (37 segundos intercalares acumulados desde el ultimo salto,
# 2016-12-31) + definicion fija TT-TAI de la Resolucion IAU 1991. TDB - TT
# difiere de esto en <= ~1.7 ms (terminos periodicos), despreciable frente
# a la tolerancia de 1000 km de T-0.7 (a ~30 km/s, 1.7 ms ~= 0.05 km).
# Si se agregan nuevos segundos intercalares tras la fecha de esta nota,
# este offset debe actualizarse.
UTC_TO_TDB_OFFSET_S = 37.0 + 32.184

# Semieje mayor medio de la orbita de Marte [AU]. Fuente: JPL Solar System
# Dynamics "Planetary Fact Sheet" / elementos orbitales medios J2000.
# Usado como radio de la orbita circular idealizada en el oraculo de
# Hohmann (T-0.5), no como posicion instantanea real (la excentricidad de
# Marte, ~0.093, es demasiado grande para eso).
MARS_SEMI_MAJOR_AXIS_AU = 1.523679
