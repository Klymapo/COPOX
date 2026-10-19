"""SENKU · pelo por mechones (prueba, 19 oct 2026): skill alth-meta-vestuario-cabello, paso 6: "Theo mechones gruesos
de raíz ancha y punta suave; evitar pelo realista de hebras".

Cada mechón es una cadena de elipsoides (unión suave) que corre sobre la cáscara del pelo de V48.3 desde una raíz cerca
de la coronilla hasta una punta: ancho y grueso bajan hacia la punta; a media altura se levanta un poco. El pelo es la
unión suave de la cáscara base (un poco hundida) y los mechones. Direcciones en grados: azimut 0 = frente, +90 = lado
izquierdo del personaje (+x); elevación desde el ecuador de la cabeza.
"""
from __future__ import annotations

import numpy as np

from .ropa_ajustada import smin

# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm): disposición tipo hoja de Theo (copete al frente que
# barre hacia su izquierda, mechones que bajan a los lados y atrás, tres en la coronilla).
MECHONES = [
    (-45, 70, -20, 24, 30, 9), (-18, 74, 8, 21, 32, 10), (8, 74, 34, 23, 30, 9), (32, 70, 55, 27, 28, 8),
    (70, 58, 96, 8, 30, 8), (102, 52, 112, 2, 28, 8), (-70, 58, -96, 8, 30, 8), (-102, 52, -112, 2, 28, 8),
    (150, 62, 160, -22, 32, 9), (180, 62, 180, -28, 34, 9), (-150, 62, -160, -22, 32, 9),
    (125, 52, 136, -12, 28, 8), (-125, 52, -136, -12, 28, 8),
    (0, 86, 120, 62, 30, 10), (90, 80, 168, 56, 28, 9), (-90, 80, -168, 56, 28, 9),
]


def _dir(az, el):
    a, e = np.radians(az), np.radians(el)
    return np.stack([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)], -1)


def _elipsoide(Q, r):
    k0 = np.linalg.norm(Q / r, axis=1); k1 = np.linalg.norm(Q / (r * r), axis=1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-12)


class PeloMechones:
    def __init__(self, base, mechones=MECHONES, hundir=0.0, n_bolas=14, k_mechon=0.008, k_union=0.004,
                 levanta=0.6, escala=1.6):
        """base: PeloOrilla (u otra con .c, ._radio(D) vía Rd/arbol y .sdf)."""
        self.base, self.hundir, self.k_union = base, hundir, k_union
        self.cadenas = []
        for az0, el0, az1, el1, ancho, grueso in mechones:
            s = np.linspace(0, 1, n_bolas)
            az = az0 + (az1 - az0) * s; el = el0 + (el1 - el0) * s
            D = _dir(az, el)
            R = self._R(D)
            g = escala * grueso / 1000 * (1 - 0.7 * s)
            w = escala * ancho / 1000 * np.maximum((1 - s) ** 0.7, 0.15)
            lift = levanta * g * np.sin(np.pi * s) - g * 0.15
            C = base.c + D * (R + lift)[:, None]
            Tg = np.gradient(C, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
            B = np.cross(D, Tg); B /= np.linalg.norm(B, axis=1, keepdims=True)
            paso = np.linalg.norm(np.diff(C, axis=0), axis=1).mean()
            self.cadenas.append((C, Tg, D, B, np.stack([np.full(n_bolas, paso * 1.5), g, w / 2], 1)))
        self.k_mechon = k_mechon
        todos = np.vstack([c[0] for c in self.cadenas])
        from scipy.spatial import cKDTree
        self.centros = cKDTree(todos); self.rmax = max(float(c[4].max()) for c in self.cadenas) + 0.01

    def _R(self, D):
        dist, j = self.base.arbol.query(D, k=16)
        w = np.exp(-(dist / 0.012) ** 2) + 1e-12; w /= w.sum(1, keepdims=True)
        return (w * self.base.Rd[j]).sum(1)

    def sdf_mechones(self, P):
        d = np.full(len(P), 1.0)
        cerca, _ = self.centros.query(P, distance_upper_bound=self.rmax + 0.02)
        idx = np.where(np.isfinite(cerca))[0]
        if not len(idx):
            return d
        Q = P[idx]
        for C, Tg, D, B, r in self.cadenas:
            dm = np.full(len(Q), 1.0)
            for i in range(len(C)):
                L = Q - C[i]
                loc = np.stack([L @ Tg[i], L @ D[i], L @ B[i]], 1)
                dm = smin(dm, _elipsoide(loc, r[i]), self.k_mechon)
            d[idx] = np.minimum(d[idx], dm)
        return d

    def sdf(self, P):
        return smin(self.base.sdf(P) + self.hundir, self.sdf_mechones(P), self.k_union)

    def malla(self, paso=0.0012, pulido=2):
        from skimage.measure import marching_cubes
        from .mano_geo import taubin
        rmax = float(self.base.Rd.max()) + 0.03
        c = self.base.c
        lo = c - rmax; hi = c + rmax
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.full(n, 1.0, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            r = np.linalg.norm(g - c, axis=1)
            cerca = (r > self.base.Rd.min() - 0.03) & (r < rmax)
            f = np.ones(len(g), np.float32)
            if cerca.any():
                f[cerca] = self.sdf(g[cerca])
            F[ix] = f.reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            V = taubin(V, T, pulido)
        return V, T

    def normales(self, V, h=0.0004):
        g = np.zeros_like(V)
        for i in range(3):
            e = np.zeros(3); e[i] = h
            g[:, i] = self.sdf(V + e) - self.sdf(V - e)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
