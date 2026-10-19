"""SENKU · cabeza hacia una caja redondeada (Adán V48).

Pedido de Admin (19 oct 2026): "Queremos que la cara se vea plana de frente. Y de atrás y los lados también. Es una
sola pieza lisa en sus lados." "Los pómulos se ven muy marcados." "Una sola pieza lisa sin bultos en la nuca, veo una
masa sobresalir." Las cejas no se tocan.

Método: escalado radial desde el centro de la cabeza. Para cada dirección (azimut, elevación) se mide el radio de la
envolvente actual: la piel expuesta de la cara sin orejas ni nariz, más la cáscara del pelo. Se calcula el radio de una
caja redondeada (la hoja de la cabeza: caras planas, aristas redondeadas) en esa misma dirección. Cada vértice de la
cabeza (piel, pelo, ojos, cejas, párpados, boca, orejas, nariz) se multiplica por k = R_caja / R_envolvente de su
dirección: la superficie cae sobre la caja y los rasgos viajan con ella. Los deltas de los gestos se escalan por el mismo
k (jacobiano isotrópico). Cerca del cuello el efecto se apaga.
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class CajaCabeza:
    def __init__(self, centro, semiejes, radio=0.035, angosta_abajo=0.06, fuerza=0.9, k_min=0.85, k_max=1.12,
                 y_cuello=(0.500, 0.530), nb=(96, 48)):
        self.c = np.asarray(centro, float)
        self.h = np.asarray(semiejes, float)           # (x, y_arriba, z_frente) y abajo/atrás en `semiejes_neg`
        self.radio, self.angosta, self.fuerza = radio, angosta_abajo, fuerza
        self.k_min, self.k_max, self.y_cuello, self.nb = k_min, k_max, y_cuello, nb
        self.h_neg = self.h.copy()

    # --- caja redondeada (centrada en c; abajo se angosta un poco: quijada chibi) -----------------------------
    def sdf_caja(self, P):
        Q = P - self.c
        hy = np.where(Q[:, 1] >= 0, self.h[1], self.h_neg[1])
        hz = np.where(Q[:, 2] >= 0, self.h[2], self.h_neg[2])
        t = np.clip(-Q[:, 1] / self.h_neg[1], 0, 1)
        hx = self.h[0] * (1 - self.angosta * t * t)
        H = np.stack([hx, hy, hz], 1)
        q = np.abs(Q) - (H - self.radio)
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - self.radio

    def radio_caja(self, D):
        """Distancia del centro a la caja a lo largo de cada dirección unitaria D (bisección)."""
        lo = np.zeros(len(D)); hi = np.full(len(D), 0.5)
        for _ in range(40):
            m = (lo + hi) / 2
            dentro = self.sdf_caja(self.c + D * m[:, None]) < 0
            lo = np.where(dentro, m, lo); hi = np.where(dentro, hi, m)
        return (lo + hi) / 2

    # --- envolvente actual ---------------------------------------------------------------------------------
    def _esf(self, P):
        Q = P - self.c
        r = np.linalg.norm(Q, axis=1)
        az = np.arctan2(Q[:, 0], Q[:, 2])                       # 0 al frente
        el = np.arcsin(np.clip(Q[:, 1] / np.maximum(r, 1e-12), -1, 1))
        return az, el, r

    def ajustar(self, envolvente):
        """envolvente: puntos de la superficie exterior (piel de la cara sin orejas/nariz + pelo)."""
        from scipy.ndimage import gaussian_filter, maximum_filter
        na, ne = self.nb
        az, el, r = self._esf(envolvente)
        ia = np.clip(((az + np.pi) / (2 * np.pi) * na).astype(int), 0, na - 1)
        ie = np.clip(((el + np.pi / 2) / np.pi * ne).astype(int), 0, ne - 1)
        G = np.zeros((na, ne))
        np.maximum.at(G, (ia, ie), r)
        # huecos: el máximo de los vecinos (varias pasadas)
        for _ in range(12):
            vacio = G == 0
            if not vacio.any():
                break
            M = maximum_filter(np.pad(G, ((2, 2), (0, 0)), mode="wrap"), size=3)[2:-2]
            G[vacio] = M[vacio]
        G = gaussian_filter(np.pad(G, ((4, 4), (0, 0)), mode="wrap"), sigma=1.2)[4:-4]
        self.az_c = (np.arange(na) + 0.5) / na * 2 * np.pi - np.pi
        self.el_c = (np.arange(ne) + 0.5) / ne * np.pi - np.pi / 2
        A, Ee = np.meshgrid(self.az_c, self.el_c, indexing="ij")
        D = np.stack([np.cos(Ee) * np.sin(A), np.sin(Ee), np.cos(Ee) * np.cos(A)], -1).reshape(-1, 3)
        Rc = self.radio_caja(D).reshape(na, ne)
        K = np.clip(Rc / np.maximum(G, 1e-6), self.k_min, self.k_max)
        self.K = gaussian_filter(np.pad(K, ((4, 4), (0, 0)), mode="wrap"), sigma=1.0)[4:-4]
        self.G, self.Rc = G, Rc
        return self

    def k(self, P):
        from scipy.interpolate import RegularGridInterpolator
        az, el, _ = self._esf(P)
        azp = np.r_[self.az_c[-1] - 2 * np.pi, self.az_c, self.az_c[0] + 2 * np.pi]
        Kp = np.vstack([self.K[-1:], self.K, self.K[:1]])
        f = RegularGridInterpolator((azp, self.el_c), Kp, bounds_error=False, fill_value=None)
        k = f(np.c_[az, np.clip(el, self.el_c[0], self.el_c[-1])])
        w = self.fuerza * _ss((P[:, 1] - self.y_cuello[0]) / (self.y_cuello[1] - self.y_cuello[0]))
        return 1 + (k - 1) * w

    def campo(self, P):
        """P' y jacobiano (isotrópico, para los deltas de los gestos)."""
        k = self.k(P)
        P1 = self.c + (P - self.c) * k[:, None]
        J = np.tile(np.eye(3), (len(P), 1, 1)) * k[:, None, None]
        return P1, J


def mascara_local(P, cachete=True, lados=True, nuca=True, suave=2.0):
    """V48.1 (camino A): peso por zona, con orillas anchas (`suave` multiplica los anchos de transición).
    Solo cachetes, lados bajo el pelo y nuca. Se apaga cerca de ojos, boca y nariz, orejas y cuello."""
    x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
    s = suave
    sin_orejas = _ss((0.134 - x) / 0.004)
    cuello = _ss((y - 0.492) / (0.018 * s))
    w = np.zeros(len(P))
    if cachete:
        w = np.maximum(w, _ss((z - 0.04) / (0.03 * s)) * _ss((x - 0.045) / (0.02 * s)) * _ss((0.61 - y) / (0.025 * s)))
    if lados:
        w = np.maximum(w, _ss((x - 0.09) / (0.02 * s)) * _ss((z + 0.07) / (0.02 * s)) * _ss((0.11 - z) / (0.02 * s))
                       * _ss((0.62 - y) / (0.03 * s)))
    if nuca:
        w = np.maximum(w, _ss((-0.02 - z) / (0.03 * s)) * _ss((0.60 - y) / (0.03 * s)))
    return w * sin_orejas * cuello
