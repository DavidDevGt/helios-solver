"""Estado (posicion, velocidad) de los cuerpos del sistema solar.

D-1 (PLAN.md sec. 1) resuelta: pykep instala pero su wheel de PyPI (3.0.1)
esta rota (falla en `import pykep`, falta un data file empaquetado
-- ver docs/adr/0001-orbital-mechanics-library.md). Backend real: lectura
directa de un kernel SPICE/NAIF via `jplephem`, sin pasar por `hapsira`
(su version 0.18.0 tampoco importa limpiamente contra las versiones
actuales de astropy/numpy/scipy resolubles por uv -- misma clase de
problema, documentado en el mismo ADR).

El kernel usado es un recorte (`kernels/de440s_excerpt.bsp`, ~750 KB) del
DE440s de JPL/NAIF, generado una sola vez con
`python -m jplephem excerpt 2020/1/1 2035/1/1 <url de de440s.bsp> ...`
y versionado en el repo -- no se descarga nada en tiempo de ejecucion ni
en CI. Solo cubre 2020-01-01..2035-01-01 y los cuerpos Sol/Tierra/Marte;
extenderlo (mas cuerpos, mas rango) es cuestion de regenerar el archivo.

Unidades de salida: posicion en km, velocidad en km/s, en el marco
ecliptico J2000 heliocentrico (mismo marco que "ECLIPJ2000" de Horizons;
verificado por comparacion directa en tests/test_ephemeris.py).
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

import numpy as np
from jplephem.spk import SPK

from .constants import DAY_S, ECLIPTIC_OBLIQUITY_J2000_DEG, UTC_TO_TDB_OFFSET_S

DEFAULT_KERNEL_PATH = Path(__file__).parent / "kernels" / "de440s_excerpt.bsp"

# NAIF SPK chains (center, target) from the Solar System Barycenter (0) to
# each body, matching the segments present in DEFAULT_KERNEL_PATH. Earth
# needs the extra Earth-Moon-barycenter -> Earth hop because the two are
# offset by up to ~4671 km (well above our 1000 km tolerance); Mars does
# not, because the Mars-system barycenter and Mars itself are offset by
# only meters (Phobos/Deimos are negligible mass) -- see
# docs/domain/glossary.md.
_SUN_CHAIN = ((0, 10),)
_BODY_CHAINS = {
    "earth": ((0, 3), (3, 399)),
    "mars": ((0, 4),),
}

_eps = np.radians(ECLIPTIC_OBLIQUITY_J2000_DEG)
_cos_eps, _sin_eps = np.cos(_eps), np.sin(_eps)
# Rotates ICRF/equatorial-J2000 vectors into the mean-ecliptic-of-J2000
# frame (rotation about the X axis by the mean obliquity). Verified against
# JPL Horizons' own "Ecliptic of J2000.0" output in tests/test_ephemeris.py.
_ICRF_TO_ECLIPJ2000 = np.array(
    [
        [1.0, 0.0, 0.0],
        [0.0, _cos_eps, _sin_eps],
        [0.0, -_sin_eps, _cos_eps],
    ]
)


@lru_cache(maxsize=4)
def _open_kernel(kernel_path: str) -> SPK:
    return SPK.open(kernel_path)


def _julian_date_tdb(epoch: dt.datetime) -> float:
    """Fecha juliana TDB para un `epoch` interpretado como UTC.

    Aproximacion de offset fijo (ver constants.UTC_TO_TDB_OFFSET_S); valida
    para fechas sin segundos intercalares nuevos desde 2017-01-01.
    """
    tdb = epoch + dt.timedelta(seconds=UTC_TO_TDB_OFFSET_S)
    days_since_epoch = (tdb - dt.datetime(1899, 12, 31, 12, 0, 0)).total_seconds() / DAY_S
    # JD de 1899-12-31 12:00 (epoca de Dublin) = 2415020.0
    return 2415020.0 + days_since_epoch


def _ssb_state(kernel: SPK, chain: tuple[tuple[int, int], ...], jd_tdb: float):
    """Posicion [km] y velocidad [km/s] relativas al SSB, sumando `chain`."""
    r = np.zeros(3)
    v = np.zeros(3)
    for center, target in chain:
        r_hop, v_hop = kernel[center, target].compute_and_differentiate(jd_tdb)
        r += r_hop
        v += v_hop / DAY_S  # jplephem deriva en km/dia; convertir a km/s
    return r, v


def state_vector(
    body: str,
    epoch: dt.datetime,
    *,
    kernel_path: Path | str = DEFAULT_KERNEL_PATH,
) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (r, v) de `body` en `epoch`.

    Args:
        body: nombre del cuerpo ("earth", "mars").
        epoch: fecha/hora UTC.
        kernel_path: ruta a un kernel SPK; por defecto el recorte
            versionado del DE440s (2020-01-01..2035-01-01).

    Returns:
        r: posicion heliocentrica [km], shape (3,).
        v: velocidad heliocentrica [km/s], shape (3,).
    """
    key = body.lower()
    if key not in _BODY_CHAINS:
        raise ValueError(f"cuerpo desconocido {body!r}; soportados: {sorted(_BODY_CHAINS)}")

    kernel = _open_kernel(str(kernel_path))
    jd_tdb = _julian_date_tdb(epoch)

    r_body, v_body = _ssb_state(kernel, _BODY_CHAINS[key], jd_tdb)
    r_sun, v_sun = _ssb_state(kernel, _SUN_CHAIN, jd_tdb)

    r_helio_icrf = r_body - r_sun
    v_helio_icrf = v_body - v_sun

    r_ecl = _ICRF_TO_ECLIPJ2000 @ r_helio_icrf
    v_ecl = _ICRF_TO_ECLIPJ2000 @ v_helio_icrf
    return r_ecl, v_ecl
