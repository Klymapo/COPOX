"""SENKU · "liso y plano": cuánto quiebre (bulto, hoyo, escalón) hay por región del cuerpo.

Regla de Admin (18 oct 2026): sin bultos ni huecos, todo liso y plano. Se mide con el mismo pasa-altos de curvatura
que el modo `quiebres` de CHXP (quiebres.pasa_altos) sobre la malla en reposo, por región, excluyendo los cortes
intencionales (dedos de manos y pies, orejas, pretina y cordón, ojos, cejas, boca).
Resultado por región: p95 del quiebre y % de área "caliente" (sobre UMBRAL). Compara versiones: menos es más liso.
"""
from __future__ import annotations

import numpy as np

UMBRAL = 1.5          # quiebre (curvatura pasa-altos, unidades de CHXP) desde el cual se ve una marca con luz de juego

REGIONES = {
    "nuca":   lambda P: (P[:, 2] < -0.02) & (P[:, 1] > 0.47) & (P[:, 1] < 0.62) & (np.abs(P[:, 0]) < 0.12),
    "brazos": lambda P: (np.abs(P[:, 0]) > 0.11) & (np.abs(P[:, 0]) < 0.262) & (P[:, 1] > 0.37) & (P[:, 1] < 0.50),
    "manos":  lambda P: (np.abs(P[:, 0]) > 0.272) & (P[:, 1] > 0.35) & (P[:, 1] < 0.50),
    "torso":  lambda P: (np.abs(P[:, 0]) < 0.11) & (P[:, 1] > 0.28) & (P[:, 1] < 0.46),
    "piernas": lambda P: (P[:, 1] > 0.07) & (P[:, 1] < 0.16),
    "pies":   lambda P: (P[:, 1] < 0.07),
}
EXCLUIR_MAT = ("BOCA", "DIENTES", "OJO", "CEJA", "PARPADO", "CORDON", "PRETINA", "LENGUA")


def medir(sesion, umbral=UMBRAL):
    from .quiebres import pasa_altos
    g = sesion.geo(None, 0.0, ())
    q = pasa_altos(sesion, g.curv)                      # por vértice (orden de g.P)
    F = sesion.F
    qf = q[F].mean(1)
    Pc = g.P[F].mean(1)
    A = 0.5 * np.linalg.norm(np.cross(g.P[F[:, 1]] - g.P[F[:, 0]], g.P[F[:, 2]] - g.P[F[:, 0]]), axis=1)
    mat = np.array(sesion.mat_nombre)[sesion.prim]
    nodo = np.array(sesion.nodoF)
    vis = ~sesion.ocultoF if hasattr(sesion, "ocultoF") else np.ones(len(F), bool)
    ok = vis & ~np.array([any(x in m.upper() for x in EXCLUIR_MAT) for m in mat]) & ~np.char.startswith(nodo, "MANO_PUNO") \
        & ~np.char.startswith(nodo, "MANO_SENALAR")
    out = {}
    for nombre, f in REGIONES.items():
        m = ok & f(Pc)
        if nombre in ("manos", "pies"):
            # sólo palma / empeine: se excluyen las puntas de los dedos (cortes a propósito)
            m &= (np.abs(Pc[:, 0]) < 0.36) if nombre == "manos" else (Pc[:, 2] < 0.105)
        if not m.any():
            continue
        out[nombre] = {"p95": round(float(np.percentile(qf[m], 95)), 3),
                       "caliente_%": round(float(100 * A[m][qf[m] > umbral].sum() / A[m].sum()), 2)}
    return out
