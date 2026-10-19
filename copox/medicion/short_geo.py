"""SENKU · short de una pieza como superficie implícita (Adán V41).

Pelvis de sección superelipse que abraza al torso, dos perneras en caja redondeada y una entrepierna estrecha por unión
suave. La pretina es la franja de arriba (otro material) y el cordón va aparte, también implícito.
Marco del personaje: Y arriba, frente hacia +Z, X a la izquierda del personaje. Unidades del GLB.
"""
from __future__ import annotations

import numpy as np

from .mano_geo import _smin, _capsula, taubin


def _superelipse(P, cx, cz, a, b, p):
    u = np.abs(P[:, 0] - cx) / a; v = np.abs(P[:, 2] - cz) / b
    e = (u ** p + v ** p) ** (1 / p)
    return (e - 1) * np.minimum(a, b)


class Short:
    def __init__(self, y_cint, y_ent, y_dob, cint, cadera, dob, muesca=0.013, p=3.2, boca=None, alto_boca=0.010):
        """Caja de la cintura al dobladillo con una muesca en la entrepierna (como la hoja de piernas).
        cint/cadera/dob: (medio ancho, medio fondo, centro z) en la cintura, la entrepierna y el dobladillo.
        muesca: medio ancho de la muesca en el dobladillo; arriba (entrepierna) es 0."""
        self.y_cint, self.y_ent, self.y_dob = y_cint, y_ent, y_dob
        self.cint, self.cadera, self.dob = (np.asarray(v, float) for v in (cint, cadera, dob))
        self.muesca, self.p = muesca, p
        self.boca = None if boca is None else np.asarray(boca, float)
        self.alto_boca = alto_boca

    def seccion(self, y):
        t1 = np.clip((self.y_cint - y) / (self.y_cint - self.y_ent), 0, 1); s1 = t1 * t1 * (3 - 2 * t1)
        t2 = np.clip((self.y_ent - y) / (self.y_ent - self.y_dob), 0, 1); t2 = t2 * t2 * (3 - t2 * 2)   # sin quiebre en la entrepierna
        v = self.cint[None] + (self.cadera - self.cint)[None] * s1[:, None]
        v = v + (self.dob - self.cadera)[None] * t2[:, None]
        if self.boca is not None:                                   # la boca abraza al torso: no se ve por dentro
            tb = np.clip((self.y_cint - y) / self.alto_boca, 0, 1); tb = tb * tb * (3 - 2 * tb)
            v = self.boca[None] + (v - self.boca[None]) * tb[:, None]
        return v

    def sdf(self, Q):
        P = Q.copy(); P[:, 0] = np.abs(P[:, 0])
        y = P[:, 1]
        a, b, cz = self.seccion(y).T
        d = _superelipse(P, 0.0, cz, a, b, self.p)
        d = np.maximum(d, np.maximum(y - self.y_cint, self.y_dob - y))
        # muesca: cuña vertical entre las perneras, de la entrepierna (ancho 0) al dobladillo; redondeada arriba
        t = np.clip((self.y_ent - y) / (self.y_ent - self.y_dob), 0, 1)
        w = self.muesca * t                                 # V recta, como la hoja
        m = np.where(y < self.y_ent, P[:, 0] - w, self.y_ent - y + 0.0 * P[:, 0])
        m = np.maximum(m, y - self.y_ent)
        return np.maximum(d, -m)

    def malla(self, paso=0.0012, pulido=2):
        from skimage.measure import marching_cubes
        ext = np.vstack([self.cint, self.cadera, self.dob])
        lo = np.array([-ext[:, 0].max() - 0.02, self.y_dob - 0.006, (ext[:, 2] - ext[:, 1]).min() - 0.02])
        hi = np.array([ext[:, 0].max() + 0.02, self.y_cint + 0.006, (ext[:, 2] + ext[:, 1]).max() + 0.02])
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.empty(n, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            F[ix] = self.sdf(g).reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            V = taubin(V, T, pulido)
        return V, T


def partir_plano(V, T, y0):
    """Corta la malla por el plano y = y0 sin quitar nada: los triángulos que lo cruzan se parten con vértices nuevos
    sobre el plano (compartidos entre vecinos). Devuelve V, T y si cada triángulo queda arriba."""
    V = [tuple(v) for v in V]; Vn = list(V)
    cache = {}
    def punto(i, j):
        k = (min(i, j), max(i, j))
        if k not in cache:
            a, b = np.array(Vn[i]), np.array(Vn[j]); t = (y0 - a[1]) / (b[1] - a[1])
            Vn.append(tuple(a + (b - a) * t)); cache[k] = len(Vn) - 1
        return cache[k]
    Y = np.array([v[1] for v in V])
    out = []
    for tri in T:
        s = [Y[i] > y0 for i in tri]
        if all(s) or not any(s):
            out.append(list(tri)); continue
        # rota para que el vértice solitario vaya primero
        for r in range(3):
            a, b, c = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
            if (Y[a] > y0) != (Y[b] > y0) and (Y[a] > y0) != (Y[c] > y0):
                break
        pab, pac = punto(a, b), punto(a, c)
        out += [[a, pab, pac], [pab, b, c], [pab, c, pac]]
    V2 = np.array(Vn); T2 = np.array(out, int)
    arriba = V2[T2].mean(1)[:, 1] > y0
    return V2, T2, arriba


def recortar(V, T, y_dob, y_cint, margen=0.0025):
    """Bocas limpias: corta la malla por dos planos exactos (dobladillo y cintura) y quita lo de afuera."""
    V, T, arriba = partir_plano(V, T, y_dob + margen)
    T = T[arriba]
    V, T, arriba = partir_plano(V, T, y_cint - margen)
    T = T[~arriba]
    u = np.unique(T); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
    return V[u], mp[T]


def quitar_tapas(V, T, y_cint, y_dob, tol=0.0025):
    """Abre la boca de la cintura (queda dentro del torso) y las de las perneras (ahí entra la pierna)."""
    c = V[T].mean(1)
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    fuera = ((c[:, 1] > y_cint - tol) & (n[:, 1] > 0.6)) | ((c[:, 1] < y_dob + tol) & (n[:, 1] < -0.6))
    T = T[~fuera]
    usados = np.unique(T)
    mapa = -np.ones(len(V), int); mapa[usados] = np.arange(len(usados))
    V, T = V[usados].copy(), mapa[T]
    # bordes de las bocas al plano exacto (sin dientes de la malla)
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    b = np.unique(u[c == 1])
    V[b[V[b, 1] < y_dob + 0.006], 1] = y_dob
    V[b[V[b, 1] > y_cint - 0.006], 1] = y_cint
    return V, T


def cordon(y, z_frente, ancho=0.018, r=0.0026, caida=0.024):
    """Moño de cordón al frente: nudo, dos lazadas y dos puntas (cápsulas). Devuelve una función sdf."""
    nudo = np.array([0.0, y, z_frente])
    piezas = []
    for s in (1, -1):
        a = nudo; b = nudo + [s * ancho, 0.006, 0.002]; c = nudo + [s * ancho * 0.9, -0.004, 0.003]
        piezas += [(a, b), (b, c), (c, a)]                       # lazada
        p0 = nudo + [s * 0.002, -0.002, 0.001]
        p1 = nudo + [s * ancho * 0.45, -caida * 0.6, 0.004]; p2 = nudo + [s * ancho * 0.35, -caida, 0.004]
        piezas += [(p0, p1), (p1, p2)]                           # punta
    def sdf(P):
        d = None
        for a, b in piezas:
            e = _capsula(P, np.asarray(a, float), np.asarray(b, float), r, r)
            d = e if d is None else np.minimum(d, e)
        bola = np.linalg.norm(P - nudo, axis=1) - r * 1.7
        return _smin(d, bola, 0.002)
    lo = nudo - [ancho + 0.01, caida + 0.01, 0.01]; hi = nudo + [ancho + 0.01, 0.015, 0.015]
    return sdf, lo, hi


def malla_sdf(sdf, lo, hi, paso=0.0006, pulido=2):
    from skimage.measure import marching_cubes
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    n = np.ceil((hi - lo) / paso).astype(int) + 1
    ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
    g = np.stack(np.meshgrid(*ejes, indexing="ij"), -1).reshape(-1, 3)
    F = sdf(g).reshape(n).astype(np.float32)
    V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
    V = V + lo
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    if pulido:
        V = taubin(V, T, pulido)
    return V, T
