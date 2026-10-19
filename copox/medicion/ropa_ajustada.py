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


def solo_mayor(V, T):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = len(V)
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    _, lab = connected_components(A, directed=False)
    tl = lab[T[:, 0]]
    mayor = np.bincount(tl).argmax()
    T = T[tl == mayor]
    u = np.unique(T); mp = -np.ones(n, np.int64); mp[u] = np.arange(len(u))
    return V[u], mp[T]


class Pieza:
    """Distancia con signo a una pieza del cuerpo. Con T, la superficie se muestrea densa (lado ≤ `lado`) con normales
    interpoladas: el plano local sale de puntos a ~1 mm, sin los bultos de una malla de vértices espaciados."""

    def __init__(self, V, N, T=None, k=4, lado=0.002, J=None, W=None):
        from scipy.spatial import cKDTree
        V = np.asarray(V, float); N = np.asarray(N, float)
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        self.V0, self.J, self.W = V, J, W
        self.vert = [np.c_[np.arange(len(V)), np.arange(len(V)), np.arange(len(V))]]
        self.bar = [np.c_[np.ones(len(V)), np.zeros(len(V)), np.zeros(len(V))]]
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
                k_ = ok.sum()
                self.vert.append(np.repeat(t, k_, axis=0))
                self.bar.append(np.tile(np.c_[c[0, :, 0], a[0, :, 0], b[0, :, 0]], (len(t), 1)))
            V = np.vstack(Ps); N = np.vstack(Ns)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        self.vert = np.vstack(self.vert); self.bar = np.vstack(self.bar)
        self.V, self.N = V, N
        self.arbol = cKDTree(self.V); self.k = k

    def sdf(self, P):
        out = np.full(len(P), 0.03)                   # lejos: afuera (ver nota abajo)
        d, j = self.arbol.query(P, k=self.k, workers=-1, distance_upper_bound=self.confianza)
        ok = np.isfinite(d[:, 0])
        if ok.any():
            d, j, Q = d[ok], j[ok], P[ok]
            fin = np.isfinite(d)
            j = np.where(fin, j, 0); d = np.where(fin, d, 1.0)
            w = np.exp(-(d / (d[:, :1] + 0.0015)) ** 2) * fin; w /= w.sum(1, keepdims=True)
            S = (w[..., None] * self.V[j]).sum(1); N = (w[..., None] * self.N[j]).sum(1)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            out[ok] = np.einsum("ij,ij->i", Q - S, N)
        # lejos de la pieza el plano local no sirve (piezas abiertas: el signo sale al azar) → afuera; el interior lejano
        # lo resuelve el relleno por conexión de Prenda.malla.
        return out

    confianza = 0.012

    def pesos(self, idx, n_huesos):
        """Pesos (densos) en las muestras idx: interpolación baricéntrica de los 3 vértices de su triángulo."""
        Wn = self.W / np.maximum(self.W.sum(1, keepdims=True), 1e-9)
        out = np.zeros((len(idx), n_huesos))
        for c in range(3):
            v = self.vert[idx, c]
            for q in range(4):
                np.add.at(out, (np.arange(len(idx)), self.J[v, q].astype(int)), Wn[v, q] * self.bar[idx, c])
        return out


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

    def malla(self, lo, hi, paso=0.0014, banda=0.010, pulido=6):
        from .malla_rapida import malla_banda
        V, T = malla_banda(self.sdf, lo, hi, paso, pulido=0, rellenar=True, etiqueta="ropa")
        V, T = solo_mayor(V, T)            # fuera las superficies fantasma internas (p. ej. el brazo metido en el torso)
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            from .mano_geo import taubin
            V = taubin(V, T, pulido)
        return V, T

    def normales(self, V, h=0.0004):
        g = np.zeros_like(V)
        for i in range(3):
            e = np.zeros(3); e[i] = h
            g[:, i] = self.sdf(V + e) - self.sdf(V - e)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


def pesos_por_piel_visible(V, piezas, n_huesos, respaldo=(), lejos=0.015, k=4):
    """Pesos de la piel que la prenda tapa: el punto de piel VISIBLE más cercano (muestras de cada pieza que no quedan
    dentro de otra pieza: el brazo metido en el torso no cuenta, cuenta el torso). `respaldo`: piezas que no son piel
    (p. ej. el short) y solo se usan donde no hay piel visible a menos de `lejos`."""
    from scipy.spatial import cKDTree

    def nube(grupo, filtrar):
        P, ref = [], []
        for a, p in enumerate(grupo):
            m = np.ones(len(p.V), bool)
            if filtrar:
                for b, q in enumerate(grupo):
                    if b != a:
                        m &= q.sdf(p.V) > -0.0005
            P.append(p.V[m]); ref.append(np.c_[np.full(m.sum(), a), np.where(m)[0]])
        return np.vstack(P), np.vstack(ref)

    def evaluar(grupo, ref, j):
        Wv = np.zeros((len(j), n_huesos))
        for a, p in enumerate(grupo):
            s_ = ref[j, 0] == a
            if s_.any():
                Wv[s_] = p.pesos(ref[j[s_], 1], n_huesos)
        return Wv

    P, ref = nube(piezas, True)
    d, j = cKDTree(P).query(V, workers=-1)                   # el punto de piel exacto debajo (muestras a ≤ 2 mm)
    Wv = evaluar(piezas, ref, j)
    if respaldo:
        Pr, rr = nube(list(respaldo), False)
        sel = d > lejos
        if sel.any():
            _, jr = cKDTree(Pr).query(V[sel], workers=-1)
            Wv[sel] = evaluar(list(respaldo), rr, jr)
    top = np.argsort(-Wv, axis=1)[:, :4]
    Wt = np.take_along_axis(Wv, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
    return top.astype(np.uint16), Wt.astype(np.float32)


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
