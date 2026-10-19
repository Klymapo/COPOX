"""SENKU · pelo que baja a cubrir la nuca y se sella contra la piel (Adán V45).

El pelo de Adán son dos cáscaras sobre la cabeza (RELLENO: volumen; CONTORNO: franja del nacimiento) y la piel de la
cabeza está recortada debajo. En la nuca, el borde del pelo y el de la piel no se tocaban: quedaba una rendija por la que
se veía el interior (en Godot, una línea rojiza) y, debajo del pelo, una franja de piel abultada (~20 % del alto de la
cabeza de espalda; en la hoja, ~12 %).

No se crea geometría. La franja baja del pelo (alto `banda`) se estira hacia abajo `delta` en el centro de la nuca
(desvanecido hacia las orejas):
- lo que sigue por encima del borde original se desliza sobre la superficie original del pelo;
- lo que queda por debajo se acuesta sobre la piel, a `holgura` de distancia.
Cada punto se proyecta al punto más cercano EXACTO de la superficie (triángulos), no a una interpolación.
El borde nuevo queda pegado a la piel: sin rendija ni escalón. Lo que está arriba de la franja no se mueve.
Marco: Y arriba, frente +Z.
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def mas_cercano(P, V, T, k=12):
    """Punto más cercano de cada P sobre la malla (V, T), y la normal de su triángulo (orientada por T)."""
    from scipy.spatial import cKDTree
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    arbol = cKDTree((A + B + C) / 3)
    _, cand = arbol.query(P, k=k)
    best = np.full(len(P), np.inf); Q = np.zeros_like(P); Nq = np.zeros_like(P)
    for j in range(k):
        t = cand[:, j]
        q = _tri_cercano(P, A[t], B[t], C[t])
        d = np.einsum("ij,ij->i", q - P, q - P)
        m = d < best
        best[m] = d[m]; Q[m] = q[m]
        n = np.cross(B[t] - A[t], C[t] - A[t]); Nq[m] = n[m]
    Nq /= np.maximum(np.linalg.norm(Nq, axis=1, keepdims=True), 1e-12)
    return Q, Nq


def _tri_cercano(p, a, b, c):
    """Ericson, Real-Time Collision Detection 5.1.5, vectorizado."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
    den = np.where(np.abs(va + vb + vc) < 1e-20, 1e-20, va + vb + vc)
    v = vb / den; w = vc / den
    out = a + ab * v[:, None] + ac * w[:, None]                         # dentro de la cara
    def pon(m, val):
        out[m] = val[m]
    sv = d1 - d3; sw = d6 - d5
    # regiones de aristas
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(np.abs(sv) < 1e-20, 1e-20, d1 - d3); pon(m, a + ab * t[:, None])
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(np.abs(d2 - d6) < 1e-20, 1e-20, d2 - d6); pon(m, a + ac * t[:, None])
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where(np.abs((d4 - d3) + (d5 - d6)) < 1e-20, 1e-20, (d4 - d3) + (d5 - d6)); pon(m, b + (c - b) * t[:, None])
    # regiones de vértices (al final: tienen prioridad)
    pon((d6 >= 0) & (d5 <= d6), c)
    pon((d3 >= 0) & (d4 <= d3), b)
    pon((d1 <= 0) & (d2 <= 0), a)
    del sw
    return out


def borde_por_angulo(Vb, zc=0.005, sectores=144):
    """Altura del borde del pelo por ángulo alrededor de la cabeza (θ = 0 atrás al centro)."""
    th = np.degrees(np.arctan2(Vb[:, 0], -(Vb[:, 2] - zc)))
    edges = np.linspace(-180, 180, sectores + 1)
    idx = np.clip(np.digitize(th, edges) - 1, 0, sectores - 1)
    bt, by = [], []
    for k in np.unique(idx):
        m = idx == k
        bt.append(th[m].mean()); by.append(Vb[m, 1].min())
    o = np.argsort(bt)
    bt, by = np.array(bt)[o], np.array(by)[o]
    # suavizado del borde (sin dientes)
    by = np.convolve(np.r_[by[-2:], by, by[:2]], np.ones(5) / 5, mode="valid")
    return lambda t: np.interp(t, bt, by)


def mover(P, pelo, piel, borde_y, off=None, delta=0.024, banda=0.020, ancho_th=75.0, holgura=0.0006, zc=0.005):
    """P: vértices de una capa del pelo. pelo/piel: (V, T) de la superficie original del RELLENO y de la piel.
    off: resalte de cada vértice sobre el RELLENO (CONTORNO); None = 0. Devuelve P' y la máscara de movidos."""
    th = np.degrees(np.arctan2(P[:, 0], -(P[:, 2] - zc)))
    e = borde_y(th)
    d = delta * _ss(1 - np.abs(th) / ancho_th) * (P[:, 2] < zc + 0.03)
    s = (P[:, 1] - e) / banda
    mov = (s < 1) & (d > 1e-6)
    out = P.copy()
    if not mov.any():
        return out, mov
    Pm, em, dm = P[mov], e[mov], d[mov]
    of = np.zeros(len(Pm)) if off is None else off[mov]
    y2 = (em + banda) - (em + banda - Pm[:, 1]) * (banda + dm) / banda
    q = Pm.copy(); q[:, 1] = y2
    Qh, Nh = mas_cercano(q, *pelo)
    Qs, Ns = mas_cercano(q, *piel)
    # normales hacia afuera (lejos del eje de la cabeza)
    for N, Q in ((Nh, Qh), (Ns, Qs)):
        fuera = np.c_[Q[:, 0], np.zeros(len(Q)), Q[:, 2] - zc]
        N *= np.sign(np.einsum("ij,ij->i", N, fuera))[:, None] + (np.einsum("ij,ij->i", N, fuera) == 0)[:, None]
    w = _ss((em - y2) / 0.004)                                   # 0 sobre el borde original, 1 debajo
    arriba = Qh + Nh * of[:, None]
    abajo = Qs + Ns * (holgura + of * (1 - _ss((em - y2) / 0.008)))[:, None]
    out[mov] = arriba * (1 - w)[:, None] + abajo * w[:, None]
    return out, mov
