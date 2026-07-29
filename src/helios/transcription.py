"""Transcripcion directa del control continuo (Sims-Flanagan, T-1.2).

Discretiza el arco en N segmentos de empuje constante e impone matching
(continuidad de estado) en el punto medio de cada segmento.
"""

from __future__ import annotations

import numpy as np


def matching_defect(
    controls: np.ndarray,
    state_initial: np.ndarray,
    state_final: np.ndarray,
    n_segments: int,
) -> np.ndarray:
    """Defecto de matching (forward-backward shooting) en el punto medio.

    Args:
        controls: array (n_segments, 3) de [T, alpha, beta] por segmento.
        state_initial: estado en t0.
        state_final: estado objetivo en tf (rendezvous).
        n_segments: numero de segmentos N.

    Returns:
        Vector de defectos; el optimizador los restringe a ~0.
    """
    raise NotImplementedError("Pendiente T-1.2: implementar y validar con la solucion de Hohmann.")
