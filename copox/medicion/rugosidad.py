"""SENKU · rugosidad de la piel alrededor de la boca, comparada con la mejilla.

Usa la curvatura por vértice de CHXP (Sesion.geo). rugosidad = desviación estándar de la curvatura.
Una boca "sin bultos" tiene la rugosidad del anillo de la boca parecida a la de la mejilla (razón ≈ 1–2).
Se excluye la franja de la rendija (|dy| < 3 mm·u), que es un corte a propósito.
"""
from __future__ import annotations
import numpy as np

ED, YC, Y0, KY, XW = 0.1348, 0.6252, 0.5325, 8.75, 0.031


def piel_cara(sesion):
    """Máscara de los vértices de la piel grande de la cara (la primitiva con más vértices y morphs)."""
    tam = [len(p.pos) for p in sesion.m.prims]
    k = max(range(len(tam)), key=lambda i: tam[i] if sesion.m.prims[i].morphs else 0)
    m = np.zeros(sum(tam), bool); o = sum(tam[:k]); m[o:o + tam[k]] = True
    return m


def zonas(P):
    yr = Y0 + KY * P[:, 0] ** 2
    dy = P[:, 1] - yr
    u = P[:, 0] / ED
    frente = P[:, 2] > 0.11
    r = np.sqrt((u / 0.75) ** 2 + ((dy / ED) / 0.40) ** 2)
    anillo = frente & (r < 1.0) & (np.abs(dy) > 0.003) & (P[:, 1] < 0.565)   # sin la base de la nariz
    mejilla = frente & (np.abs(P[:, 0] - 0.085) < 0.02) & (np.abs(P[:, 1] - 0.565) < 0.02)
    return anillo, mejilla


def medir(sesion, morphs=()):
    g = sesion.geo(None, 0.0, tuple(morphs))
    P = g.P if hasattr(g, "P") else g[0]
    curv = g.curv if hasattr(g, "curv") else g[2]
    a, m = zonas(P)
    cara = piel_cara(sesion)
    a, m = a & cara, m & cara
    ra, rm = float(np.std(curv[a])), float(np.std(curv[m]))
    return {"anillo": ra, "mejilla": rm, "razon": ra / max(rm, 1e-9), "n": int(a.sum())}
