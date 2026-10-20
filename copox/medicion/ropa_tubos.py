"""SENKU · ropa como volúmenes limpios (19 oct 2026), con la técnica del short que le gustó a Admin ("El short queda
muy bien"): cada prenda es una superficie implícita de secciones superelípticas que se interpolan suave a lo largo de
un eje (torso y piernas en y, mangas en x). Las secciones se AJUSTAN al cuerpo medido (extremos + holgura) y luego se
suavizan a lo largo del eje: la tela no copia cada bulto del cuerpo, es un volumen simple como el short. Las capas son
el mismo tubo con más holgura (chaleco = camisa + capa), así nunca se cruzan en reposo.
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Tubo:
    """Tubo de secciones superelípticas a lo largo de `eje` (0 = x, 1 = y) entre t0 y t1.
    V: vértices del cuerpo que el tubo debe envolver. lado: +1/−1 para mangas (x positivo o negativo)."""

    def __init__(self, V, eje, t0, t1, holgura, n=28, p=3.0, suavizar=3, lado=1, recto_desde=None, extra=None,
                 holgura_fn=None):
        self.eje, self.t0, self.t1, self.p, self.lado = eje, min(t0, t1), max(t0, t1), p, lado
        otros = [i for i in range(3) if i != eje]
        self.otros = otros
        V = np.asarray(V, float)
        t = V[:, eje] * (lado if eje == 0 else 1)
        ts = np.linspace(self.t0, self.t1, n)
        dt = (self.t1 - self.t0) / (n - 1) * 0.75 + 1e-4
        C, A = np.zeros((n, 2)), np.zeros((n, 2))
        validos = np.zeros(n, bool)
        for i, s in enumerate(ts):
            q = V[np.abs(t - s) < dt][:, otros]
            if len(q) < 4:
                continue
            lo, hi = q.min(0), q.max(0)
            C[i] = (lo + hi) / 2; A[i] = (hi - lo) / 2
            validos[i] = True
        if not validos.any():
            raise ValueError("tubo sin vértices")
        for k in range(2):
            C[:, k] = np.interp(ts, ts[validos], C[validos, k]); A[:, k] = np.interp(ts, ts[validos], A[validos, k])
        # superelipse p=3 envuelve la caja de extremos con margen: el semieje se infla un poco (esquinas)
        A = A * 1.04
        if suavizar:
            ker = np.ones(2 * suavizar + 1) / (2 * suavizar + 1)
            for k in range(2):
                C[:, k] = np.convolve(np.r_[[C[0, k]] * suavizar, C[:, k], [C[-1, k]] * suavizar], ker, "valid")
                Ap = np.r_[[A[0, k]] * suavizar, A[:, k], [A[-1, k]] * suavizar]
                # el suavizado no puede achicar (la tela no entra en el cuerpo): máximo entre suavizado y original
                A[:, k] = np.maximum(np.convolve(Ap, ker, "valid"), A[:, k] * 0.985)
        if recto_desde is not None:                        # caída recta: abajo de `recto_desde` la sección no se cierra
            j = ts <= recto_desde
            if j.any():
                ref = np.argmin(np.abs(ts - recto_desde))
                A[j] = np.maximum(A[j], A[ref]); C[j] = C[ref]
        h = holgura_fn(ts) if holgura_fn is not None else np.full(n, holgura)
        self.ts, self.C, self.A = ts, C, A + h[:, None]
        self.extra = extra

    def sdf(self, P):
        t = P[:, self.eje] * (self.lado if self.eje == 0 else 1)
        cu = np.interp(t, self.ts, self.C[:, 0]); cw = np.interp(t, self.ts, self.C[:, 1])
        au = np.interp(t, self.ts, self.A[:, 0]); aw = np.interp(t, self.ts, self.A[:, 1])
        u = np.abs(P[:, self.otros[0]] - cu) / au; w = np.abs(P[:, self.otros[1]] - cw) / aw
        k = (u ** self.p + w ** self.p) ** (1 / self.p)
        d = (k - 1) * np.minimum(au, aw)
        return np.maximum(d, np.maximum(self.t0 - t, t - self.t1))

    def inflado(self, h):
        """El mismo tubo con `h` más de holgura (la capa de encima)."""
        import copy
        o = copy.copy(self)
        o.A = self.A + h
        return o


def union(campos, k):
    def f(P):
        d = campos[0](P)
        for c in campos[1:]:
            d = smin(d, c(P), k)
        return d
    return f


def superficie_z(f, x, y, z0=0.20, z1=-0.05, n=500):
    """Primer cruce (desde el frente) de f < 0 en la recta (x, y, z): z de la cara delantera de una prenda."""
    zs = np.linspace(z0, z1, n)
    q = np.c_[np.full(n, x), np.full(n, y), zs]
    dentro = f(q) < 0
    return float(zs[np.argmax(dentro)]) if dentro.any() else None
