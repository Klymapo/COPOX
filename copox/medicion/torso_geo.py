"""COPOX · torso de una pieza con anatomía marcada (pectorales, clavículas, abdomen, omóplatos, columna, deltoides).

Igual que la mano (mano_geo): superficie implícita → marching cubes → Taubin → simplificación (meshoptimizer vía
Godot, en la receta) → pesos transferidos de la piel vieja y suavizados sobre la malla nueva.

Base: superelipses horizontales apiladas (medio ancho a(y), medio fondo b(y), centro z c(y), exponente p) — el perfil
se mide en la referencia (frente y lado). Anatomía: elipsoides que se suman con unión suave (smin) y surcos que se
restan (smax). Hombros: el torso se funde con un deltoides y un trapecio que terminan DENTRO del tubo del brazo y del
cuello (sus orillas abiertas no se ven), como la muñeca de V38. Ejes del modelo: y arriba, +z al frente, x a la izquierda
del personaje. Todo es simétrico en x (se evalúa con |x|).
"""
from __future__ import annotations

import numpy as np

from .mano_geo import _smin, _capsula, _elipsoide, taubin


def _smax(a, b, k):
    return -_smin(-a, -b, k)


class Torso:
    def __init__(self, perfil, exponente=2.6, rasgos=None, recortes=None, k_union=0.006):
        """perfil: lista de (y, a, b, c). rasgos: lista de dicts {"tipo": "suma"|"surco", "forma": "elipsoide"|
        "capsula", ...}. recortes: dict con x_max (el torso termina dentro del brazo), y_min, y_max."""
        self.P = np.array(perfil, float)
        self.p = exponente
        self.rasgos = rasgos or []
        self.rec = recortes or {}
        self.k = k_union

    def seccion(self, y):
        # interpolación monótona suave (PCHIP): con interpolación lineal se ven bandas en cada nodo del perfil
        from scipy.interpolate import PchipInterpolator
        if not hasattr(self, "_f"):
            self._f = [PchipInterpolator(self.P[:, 0], self.P[:, i], extrapolate=True) for i in (1, 2, 3)]
        y = np.clip(y, self.P[0, 0], self.P[-1, 0])
        return [f(y) for f in self._f]

    def sdf(self, Q):
        P = Q.copy(); P[:, 0] = np.abs(P[:, 0])          # simetría
        a, b, c = self.seccion(P[:, 1])
        u = np.abs(P[:, 0]) / a; v = np.abs(P[:, 2] - c) / b
        e = (u ** self.p + v ** self.p) ** (1 / self.p)
        d = (e - 1) * np.minimum(a, b) * 0.9
        # tapas suaves arriba/abajo (la orilla queda dentro del cuello y del short)
        if "y_min" in self.rec:
            d = np.maximum(d, self.rec["y_min"] - P[:, 1])
        if "y_max" in self.rec:
            d = np.maximum(d, P[:, 1] - self.rec["y_max"])
        for r in self.rasgos:
            if r["tipo"] == "hendidura":
                # surco por desplazamiento (no depende de qué tan alta quedó la superficie ahí): línea vertical en
                # x = x0, entre y0 e y1, sólo del lado indicado (+1 frente, −1 espalda); prof en metros
                y0, y1 = r["y"]
                ty = np.clip(np.minimum(P[:, 1] - y0, y1 - P[:, 1]) / r.get("rampa", 0.01), 0, 1)
                lado = np.clip((P[:, 2] - c) * r["lado"] / 0.01, 0, 1)
                d = d + r["prof"] * np.exp(-((P[:, 0] - r.get("x0", 0.0)) / r["ancho"]) ** 2) * ty * ty * (3 - 2 * ty) * lado
                continue
            if r["forma"] == "elipsoide":
                f = _elipsoide(P, np.array(r["c"], float), np.array(r["r"], float))
            else:
                f = _capsula(P, np.array(r["a"], float), np.array(r["b"], float), r["r1"], r.get("r2", r["r1"]))
            if r["tipo"] == "suma":
                d = _smin(d, f, r.get("k", self.k))
            else:                                          # surco: resta suave
                d = _smax(d, -f, r.get("k", self.k * 0.5))
        if "x_max" in self.rec:                            # el hombro termina dentro del brazo
            d = np.maximum(d, P[:, 0] - self.rec["x_max"])
        return d

    def malla(self, lo, hi, paso=0.0012, pulido=6):
        from skimage.measure import marching_cubes
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.empty(n, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            F[ix] = self.sdf(g).reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        # caras hacia afuera: volumen con signo positivo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        V = taubin(V, T, pulido)
        return V, T


def transferir_pesos(V, T, fuentes, n_huesos, k=6, suavizado=8):
    """fuentes: lista de (Vf, Jf, Wf) de las piezas viejas (reposo). Pesos por los k vecinos más cercanos (inverso de
    la distancia) y suavizado laplaciano sobre la malla nueva; se dejan 4 por vértice."""
    from scipy.spatial import cKDTree
    from .mano_geo import aristas
    Vf = np.concatenate([f[0] for f in fuentes])
    Wd = np.zeros((len(Vf), n_huesos))
    o = 0
    for Vs, Js, Ws in fuentes:
        Ws = Ws / np.maximum(Ws.sum(1, keepdims=True), 1e-9)
        np.add.at(Wd, (np.repeat(np.arange(o, o + len(Vs)), 4), Js.ravel().astype(int)), Ws.ravel())
        o += len(Vs)
    d, i = cKDTree(Vf).query(V, k=k)
    w = 1 / np.maximum(d, 1e-5); w /= w.sum(1, keepdims=True)
    W = np.einsum("nk,nkh->nh", w, Wd[i])
    A = aristas(T, len(V)); deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(suavizado):
        W = 0.5 * W + 0.5 * (np.asarray(A @ W) / deg[:, None])
    top = np.argsort(-W, axis=1)[:, :4]
    Wt = np.take_along_axis(W, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
    return top.astype(np.uint16), Wt.astype(np.float32)
