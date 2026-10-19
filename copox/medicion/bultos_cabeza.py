"""SENKU · quita los dos bultos que señaló Admin en la cabeza de V47 (19 oct 2026).

1. "Rollo" de la nuca: atrás, el pelo cae recto (z ≈ −0.167) hasta y ≈ 0.60 y ahí se enrolla hacia adentro unos 3.5 cm
   hasta su orilla (y ≈ 0.52); de perfil y de espalda se lee como un rollo. `nuca_recta` lleva el plano de atrás más abajo:
   en cada ángulo θ (atrás, desvanecido hacia los lados) la superficie se desplaza hacia afuera, hasta el radio del pelo
   a la altura de referencia. El desplazamiento se aplica igual al pelo y a la piel de abajo (conservan su separación);
   abajo se apaga hacia el cuello y deja una esquina redondeada corta.
2. "Visera" de las cejas: la piel sobre los ojos sobresale ~2.5 mm (y 0.66–0.73) y luego regresa hacia la frente.
   `frente_recta` cambia, en cada columna x, la piel de esa franja por la recta entre sus dos extremos, solo hacia
   adentro. Las cejas pintadas se mueven con la piel.
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _cil(P, zc):
    th = np.degrees(np.arctan2(P[:, 0], -(P[:, 2] - zc)))       # 0 = atrás al centro
    r = np.hypot(P[:, 0], P[:, 2] - zc)
    return th, r


def nuca_recta(pelo, y_ref=0.625, y_fin=0.505, y_pleno=0.575, ancho_th=80.0, zc=0.005, n_th=73, n_y=40):
    """Desplazamiento radial d(θ, y) calculado UNA vez en una rejilla con la superficie del pelo (RELLENO) y aplicado
    igual a todas las capas (pelo, contorno y piel): conservan su separación y la piel nunca atraviesa el pelo.
    Devuelve f(P) -> (P', d)."""
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, RegularGridInterpolator
    th, r = _cil(pelo, zc)
    atras = pelo[:, 2] < zc + 0.02
    lin = LinearNDInterpolator(np.c_[th[atras], pelo[atras, 1]], r[atras])
    near = NearestNDInterpolator(np.c_[th[atras], pelo[atras, 1]], r[atras])
    ths = np.linspace(-ancho_th - 20, ancho_th + 20, n_th)
    ys = np.linspace(y_fin - 0.03, y_ref + 0.02, n_y)
    A, Y = np.meshgrid(ths, ys, indexing="ij")
    Rh = lin(A.ravel(), Y.ravel()); bad = ~np.isfinite(Rh)
    Rh[bad] = near(A.ravel()[bad], Y.ravel()[bad]); Rh = Rh.reshape(A.shape)
    # el borde del pelo por ángulo: debajo de él, el radio del pelo es el de su orilla (no se extrapola)
    Rref = np.array([np.interp(y_ref, ys, Rh[k]) for k in range(n_th)])
    Rref = np.convolve(np.r_[Rref[:2], Rref, Rref[-2:]], np.ones(5) / 5, mode="valid")
    w = _ss((Y - y_fin) / (y_pleno - y_fin)) * np.where(Y > y_ref, 0.0, 1.0)
    w *= _ss((ancho_th - np.abs(A)) / 25.0)
    D = np.maximum(Rref[:, None] - Rh, 0) * w
    from scipy.ndimage import gaussian_filter
    D = gaussian_filter(D, sigma=1.0)
    g = RegularGridInterpolator((ths, ys), D, bounds_error=False, fill_value=0.0)

    def f(P):
        t, r = _cil(P, zc)
        m = P[:, 2] < zc + 0.03
        d = np.zeros(len(P))
        d[m] = g(np.c_[t[m], P[m, 1]])
        a = np.radians(t); r2 = r + d
        out = P.copy()
        out[m, 0] = (r2 * np.sin(a))[m]; out[m, 2] = (zc - r2 * np.cos(a))[m]
        return out, d
    return f


def frente_recta(piel, y0=0.674, y1=0.740, x_max=0.115, z_min=0.06, n_x=47):
    """Devuelve f(P) -> P' que cambia la franja sobre los ojos por la recta entre y0 y y1 (solo hacia adentro)."""
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
    fr = piel[(piel[:, 2] > z_min) & (np.abs(piel[:, 0]) < x_max + 0.02)]
    lin = LinearNDInterpolator(fr[:, :2], fr[:, 2]); near = NearestNDInterpolator(fr[:, :2], fr[:, 2])

    def Z(x, y):
        v = lin(x, y); bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = near(x[bad], y[bad])
        return v
    xs = np.linspace(-x_max, x_max, n_x)
    z0 = Z(xs, np.full(n_x, y0)); z1 = Z(xs, np.full(n_x, y1))

    def f(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        m = (z > z_min) & (np.abs(x) < x_max) & (y > y0) & (y < y1)
        out = P.copy()
        if not m.any():
            return out
        t = (y[m] - y0) / (y1 - y0)
        recta = np.interp(x[m], xs, z0) * (1 - t) + np.interp(x[m], xs, z1) * t
        w = _ss((x_max - np.abs(x[m])) / 0.035) * _ss(np.minimum(t, 1 - t) / 0.30)   # orillas anchas: sin marco
        out[m, 2] = z[m] + np.minimum(recta - z[m], 0) * w
        return out
    return f
