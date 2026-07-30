"""T-0.7: efemerides vs. JPL Horizons, fixture congelado.

Criterio (PLAN.md Gate 0->1): error de posicion < 1000 km contra los
valores de Horizons congelados en tests/fixtures/horizons_reference.csv.
Sin llamadas de red -- ver la cabecera de ese fixture para el origen de
los datos y la fecha en que se generaron.
"""

import csv
import datetime as dt
from pathlib import Path

import numpy as np
import pytest
from jplephem.exceptions import OutOfRangeError

from helios.ephemeris import state_vector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "horizons_reference.csv"
POSITION_TOLERANCE_KM = 1000.0


def _load_fixture_rows() -> list[dict]:
    with FIXTURE_PATH.open(newline="", encoding="utf-8") as f:
        data_lines = (line for line in f if not line.startswith("#"))
        return list(csv.DictReader(data_lines, skipinitialspace=True))


@pytest.mark.parametrize("row", _load_fixture_rows(), ids=lambda r: f"{r['body']}@{r['epoch_utc']}")
def test_state_vector_matches_horizons(row):
    epoch = dt.datetime.fromisoformat(row["epoch_utc"])
    r_ref = np.array([float(row["x_km"]), float(row["y_km"]), float(row["z_km"])])
    v_ref = np.array([float(row["vx_km_s"]), float(row["vy_km_s"]), float(row["vz_km_s"])])

    r, v = state_vector(row["body"], epoch)

    position_error_km = np.linalg.norm(r - r_ref)
    assert position_error_km < POSITION_TOLERANCE_KM, (
        f"{row['body']}@{row['epoch_utc']}: position error {position_error_km:.1f} km "
        f"exceeds {POSITION_TOLERANCE_KM} km tolerance"
    )
    # Not part of T-0.7's stated criterion, but a velocity bug wouldn't show
    # up in a position-only check and would silently corrupt every
    # downstream dynamics/transcription computation -- catch it here too.
    velocity_error_km_s = np.linalg.norm(v - v_ref)
    assert velocity_error_km_s < 0.01, (
        f"{row['body']}@{row['epoch_utc']}: velocity error "
        f"{velocity_error_km_s:.6f} km/s exceeds 0.01 km/s"
    )


def test_unknown_body_raises_value_error():
    with pytest.raises(ValueError, match="cuerpo desconocido"):
        state_vector("jupiter", dt.datetime(2026, 1, 1))


def test_epoch_outside_kernel_range_fails_loudly():
    """El kernel embebido solo cubre 2020-01-01..2035-01-01 (ver
    ephemeris.py). Fuera de rango debe fallar ruidosamente, no
    extrapolar en silencio -- exactamente el tipo de fallo silencioso
    que README.md (Validation philosophy) advierte."""
    with pytest.raises(OutOfRangeError):
        state_vector("earth", dt.datetime(2050, 1, 1))
