"""SENKU · quiebres alrededor de la boca y en la quijada (escalones, "U", marcas en las comisuras).

Un quiebre es un cambio brusco de forma o de luz que no sigue a sus vecinos. Se mide con un pasa-altos sobre la
malla soldada: |v − promedio local de v| (6 pasadas de suavizado por aristas), para dos campos:
  - curvatura (forma, como el modo `quiebres` de CHXP)
  - luz del juego (N·sol con las normales del archivo, como las usa Godot; el sol del visor, ver render/modos.py)
Se compara la zona boca-quijada (sin la rendija, que es un corte a propósito) contra un parche de mejilla:
razón ≈ 1 es piel tan lisa como la mejilla. La V29 (con la "U" bajo la boca) sirve de referencia de falla.
"""
from __future__ import annotations
import numpy as np

from .rugosidad import Y0, KY, piel_cara

UMBRAL_LUZ = 2.5      # razón p95 zona/mejilla de la luz de juego por encima de la cual se ve el quiebre en Godot


def pasa_altos(sesion, v, pasadas=6):
    """|v − suave(v)| por vértice (soldando costuras)."""
    w = sesion._soldadura(np.concatenate([p.pos for p in sesion.m.prims]))
    n = w.max() + 1
    Fw = w[sesion.F]
    E = np.unique(np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1), axis=0)
    c = np.bincount(w, minlength=n)
    k = np.zeros(n); np.add.at(k, w, v); k /= np.maximum(c, 1)
    deg = np.bincount(E.ravel(), minlength=n)
    ks = k.copy()
    for _ in range(pasadas):
        sm = np.zeros(n); np.add.at(sm, E[:, 0], ks[E[:, 1]]); np.add.at(sm, E[:, 1], ks[E[:, 0]])
        ks = 0.5 * ks + 0.5 * sm / np.maximum(deg, 1)
    return np.abs(k - ks)[w]


def zonas(P, Na):
    dy = P[:, 1] - (Y0 + KY * P[:, 0] ** 2)
    frente = (P[:, 2] > 0.09) & (Na[:, 2] > 0.2)
    boca = frente & (np.abs(P[:, 0]) < 0.075) & (P[:, 1] > 0.497) & (P[:, 1] < 0.562) & (np.abs(dy) > 0.004)
    comisuras = boca & (np.abs(np.abs(P[:, 0]) - 0.031) < 0.012) & (np.abs(dy) < 0.014)
    mejilla = frente & (np.abs(P[:, 0] - 0.085) < 0.02) & (np.abs(P[:, 1] - 0.565) < 0.02)
    return boca, comisuras, mejilla


def medir(sesion, morphs=()):
    from copox.render.modos import SOL
    g = sesion.geo(None, 0.0, tuple(morphs))
    Na = g.Na / np.maximum(np.linalg.norm(g.Na, axis=1, keepdims=True), 1e-12)
    cara = piel_cara(sesion)
    boca, com, mej = (z & cara for z in zonas(g.P, Na))
    qf = pasa_altos(sesion, g.curv)
    ql = pasa_altos(sesion, np.clip(Na @ SOL, 0, 1))
    p95 = lambda q, m: float(np.percentile(q[m], 95))
    r = {"forma": p95(qf, boca) / max(p95(qf, mej), 1e-9),
         "luz": p95(ql, boca) / max(p95(ql, mej), 1e-9),
         "luz_comisuras": p95(ql, com) / max(p95(ql, mej), 1e-9),
         "n": int(boca.sum())}
    r["veredicto"] = "PASS" if max(r["luz"], r["luz_comisuras"]) <= UMBRAL_LUZ else "FAIL"
    return r
