"""SENKU · ropa ajustada por superficie desplazada del cuerpo (prueba de vestuario sobre Adán, 19 oct 2026).

Skill alth-meta-vestuario-cabello, caso "ajustada → skinning": la prenda es una cáscara a `holgura` mm sobre la unión
suave de las piezas del cuerpo que cubre, recortada por regiones (planos) y con pesos transferidos del cuerpo. Así la
tela sigue al rig sin simulación y nunca flota ni se entierra en reposo. Puños y dobladillos: un anillo más grueso en
la franja de la orilla (como la manga arremangada y el pantalón con vuelta de la hoja de Theo).

Distancia con signo de cada pieza: plano local de sus k vecinos (posición y normal promediadas). Unión: smin.
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Pieza:
    """Distancia con signo a una pieza del cuerpo. Con T, la superficie se muestrea densa (lado ≤ `lado`) con normales
    interpoladas: el plano local sale de puntos a ~1 mm, sin los bultos de una malla de vértices espaciados."""

    def __init__(self, V, N, T=None, k=6, lado=0.0012, J=None, W=None):
        from scipy.spatial import cKDTree
        V = np.asarray(V, float); N = np.asarray(N, float)
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        self.V0, self.J, self.W = V, J, W
        if T is not None:
            T = np.asarray(T, np.int64)
            Ps, Ns = [V], [N]
            L = np.max([np.linalg.norm(V[T[:, a]] - V[T[:, b]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], 0)
            m = np.ceil(L / lado).astype(int)
            for n in np.unique(m[m > 1]):
                t = T[m == n]
                u, v = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
                ok = (u + v) <= n
                a = (u[ok] / n)[None, :, None]; b = (v[ok] / n)[None, :, None]; c = 1 - a - b
                Ps.append((c * V[t[:, 0]][:, None] + a * V[t[:, 1]][:, None] + b * V[t[:, 2]][:, None]).reshape(-1, 3))
                Ns.append((c * N[t[:, 0]][:, None] + a * N[t[:, 1]][:, None] + b * N[t[:, 2]][:, None]).reshape(-1, 3))
            V = np.vstack(Ps); N = np.vstack(Ns)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        self.V, self.N = V, N
        self.arbol = cKDTree(self.V); self.k = k

    def sdf(self, P):
        d, j = self.arbol.query(P, k=self.k)
        w = np.exp(-(d / (d[:, :1] + 0.0015)) ** 2); w /= w.sum(1, keepdims=True)
        S = (w[..., None] * self.V[j]).sum(1); N = (w[..., None] * self.N[j]).sum(1)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        dp = np.einsum("ij,ij->i", P - S, N)
        # lejos de la pieza el plano local no sirve (piezas abiertas: el signo sale al azar) → afuera; el interior lejano
        # lo resuelve el relleno por conexión de Prenda.malla.
        return np.where(d[:, 0] > self.confianza, d[:, 0], dp)

    confianza = 0.012


class Prenda:
    """piezas: lista de Pieza; region(P) <= 0 dentro de la prenda; orilla(P) en [0, 1] = peso del puño/dobladillo.
    extra(P): sdf adicional que la prenda debe cubrir (p. ej. otra prenda debajo), o None."""

    def __init__(self, piezas, region, orilla=None, holgura=0.0025, adentro=0.0015, puno=0.0030, k=0.010,
                 extra=None):
        self.piezas, self.region, self.orilla = piezas, region, orilla
        self.holgura, self.adentro, self.puno, self.k, self.extra = holgura, adentro, puno, k, extra

    def cuerpo(self, P):
        d = self.piezas[0].sdf(P)
        for p in self.piezas[1:]:
            d = smin(d, p.sdf(P), self.k)
        if self.extra is not None:
            d = np.minimum(d, self.extra(P))
        return d

    def sdf(self, P):
        d = self.cuerpo(P)
        h = self.holgura + (self.puno * self.orilla(P) if self.orilla is not None else 0.0)
        # sólido (cuerpo inflado), no cáscara delgada: el simplificador no junta las dos caras ni abre hoyos. Las tapas
        # de los cortes (cuello, mangas, dobladillos) quedan dentro del cuerpo, invisibles; la orilla se ve con grosor.
        return np.maximum(d - h, self.region(P))

    def malla(self, lo, hi, paso=0.0013, banda=0.012, pulido=6):
        from scipy.spatial import cKDTree
        from skimage.measure import marching_cubes
        from .mano_geo import taubin
        todos = cKDTree(np.vstack([p.V0 for p in self.piezas]))
        lo = np.asarray(lo, float); hi = np.asarray(hi, float)
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.full(n, 1.0, np.float32)
        B = np.zeros(n, bool)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            d0, _ = todos.query(g, distance_upper_bound=banda)
            cerca = np.isfinite(d0)
            if self.extra is not None:
                cerca |= np.abs(self.extra(g)) < banda
            f = np.ones(len(g), np.float32)
            if cerca.any():
                f[cerca] = self.sdf(g[cerca])
            F[ix] = f.reshape(n[1], n[2]); B[ix] = cerca.reshape(n[1], n[2])
        # fuera de la banda: adentro si no conecta con el borde de la caja (sin superficies fantasma en el interior)
        from scipy.ndimage import label
        lab, _ = label(~B | (F > 0))
        borde = np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                          lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
        F[(~B) & ~np.isin(lab, borde)] = -1.0
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


def pesos_por_dueno(V, piezas, n_huesos, k=4):
    """Cada vértice de la prenda toma los pesos de la pieza de la que es cáscara (la de menor distancia), con sus k
    vértices más cercanos: la tela se deforma como esa piel y no se cruza con ella."""
    from scipy.spatial import cKDTree
    D = np.stack([p.sdf(V) for p in piezas], 1)
    dueno = D.argmin(1)
    J4 = np.zeros((len(V), 4), np.uint16); W4 = np.zeros((len(V), 4), np.float32)
    for i, p in enumerate(piezas):
        sel = np.where(dueno == i)[0]
        if not len(sel):
            continue
        Wd = np.zeros((len(p.V0), n_huesos))
        Ws = p.W / np.maximum(p.W.sum(1, keepdims=True), 1e-9)
        np.add.at(Wd, (np.repeat(np.arange(len(p.V0)), 4), p.J.ravel().astype(int)), Ws.ravel())
        d, j = cKDTree(p.V0).query(V[sel], k=k)
        w = 1 / np.maximum(d, 1e-5); w /= w.sum(1, keepdims=True)
        Wv = np.einsum("nk,nkh->nh", w, Wd[j])
        top = np.argsort(-Wv, axis=1)[:, :4]
        Wt = np.take_along_axis(Wv, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
        J4[sel] = top; W4[sel] = Wt
    return J4, W4, np.bincount(dueno, minlength=len(piezas))
