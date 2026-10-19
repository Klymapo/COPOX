"""Compuerta de cobertura del pelo (Admin, 19 oct 2026: "Asegúrate de siempre cubrir toda el área de pelo en todos los
modelos"). El área de pelo es la máscara de la guía capilar (PeloOrilla.Md > 0.5: donde el pelo de referencia tapa la
piel). Desde el centro de la cabeza se lanza un rayo por cada dirección del área; cada rayo debe chocar con la malla del
pelo. Un peinado que deja ver cuero cabelludo en el área NO pasa (FAIL), aunque se vea bien de frente.
"""
from __future__ import annotations

import numpy as np

MINIMO = 0.995            # fracción de direcciones del área que deben quedar cubiertas


def _choca(O, D, V, T, lote=None, distancia=False):
    """Möller–Trumbore vectorizado: True si el rayo O + t·D (t > 0) cruza algún triángulo (o, con distancia=True, el
    t del choque más lejano; -inf si no choca)."""
    lote = lote or max(1, int(3e6 // max(len(T), 1)))       # memoria acotada (~3 M pares por bloque)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = B - A, C - A
    s = O - A
    hit = np.zeros(len(D), bool)
    tmax = np.full(len(D), -np.inf)
    for k in range(0, len(D), lote):
        d = D[k:k + lote][:, None, :]
        p = np.cross(d, e2[None])
        det = np.einsum("ijk,jk->ij", p, e1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        u = np.einsum("jk,ijk->ij", s, p) * inv
        q = np.cross(s, e1)
        v = np.einsum("ik,jk->ij", D[k:k + lote], q) * inv
        t = np.einsum("jk,jk->j", e2, q)[None] * inv
        bien = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        hit[k:k + lote] = bien.any(1)
        tmax[k:k + lote] = np.where(bien, t, -np.inf).max(1)
    return tmax if distancia else hit


def cobertura(V, T, centro, D, Md, umbral=0.5, n=3000, semilla=0, piel=None, Rd=None):
    """-> dict con fracción cubierta, PASS/FAIL y direcciones descubiertas (az/el en grados, para corregir).
    Con piel=(Vs, Ts) y Rd (radio del pelo por dirección): un rayo también pasa si lo último que toca es piel que llega
    al nivel del pelo (oreja, cara): eso no es cuero cabelludo. Lo que falla es cuero/cabeza sin pelo encima."""
    sel = Md > umbral
    area, marea = D[sel], Md[sel]
    if len(area) > n:
        k = np.random.default_rng(semilla).choice(len(area), n, replace=False)
        area, marea = area[k], marea[k]
    c = np.asarray(centro, float)
    th = _choca(c, area, np.asarray(V, float), np.asarray(T), distancia=True)
    hit = np.isfinite(th)
    if piel is not None:
        ts = _choca(c, area, np.asarray(piel[0], float), np.asarray(piel[1]), distancia=True)
        from scipy.spatial import cKDTree
        _, jd = cKDTree(D).query(area)
        hit = (th >= ts) | (np.isfinite(ts) & (ts >= Rd[jd] - 0.002))
    f = float(hit.mean())
    mal = area[~hit]
    az = np.degrees(np.arctan2(mal[:, 0], mal[:, 2])); el = np.degrees(np.arcsin(np.clip(mal[:, 1], -1, 1)))
    return {"cobertura": round(f, 4), "veredicto": "PASS" if f >= MINIMO else "FAIL", "rayos": int(len(area)),
            "mascara_descubiertas": [round(float(x), 2) for x in marea[~hit][:20]],
            "descubiertas": [[round(float(a)), round(float(e))] for a, e in zip(az[:20], el[:20])]}
