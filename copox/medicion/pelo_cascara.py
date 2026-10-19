"""SENKU · cáscara del pelo limpia (Adán V48.3).

Admin no aprobó V48.2: la "terraza" horizontal de la parte baja del pelo seguía, y se veía más grumosa. Esa banda está
construida en la malla vieja; empujarla o alisarla localmente la reacomoda pero no la quita. Por eso aquí la cáscara se
rehace como una sola superficie:
- Envolvente radial: desde el centro de la cabeza, para cada dirección (azimut, elevación), el radio máximo de la
  cáscara vieja. Se suaviza fuerte (gaussiana en la esfera): desaparecen la terraza, las ondas y las motas, y se
  conserva la silueta grande (la de V47, que Admin no objeta).
- Piso: en cada dirección el radio nunca baja de la piel + `holgura`, para que la piel no atraviese el pelo.
- La malla vieja (su topología y su orilla) se conserva: cada vértice solo cambia de radio. Las dos capas (RELLENO y
  CONTORNO) usan el mismo radio; CONTORNO, el del nacimiento del pelo, queda `sobre` mm por encima.
Pelo liso, como pidió Admin ("me sirve así"): el pelo final va al último.
"""
from __future__ import annotations

import numpy as np


def _esf(P, c):
    Q = P - c
    r = np.linalg.norm(Q, axis=1)
    az = np.arctan2(Q[:, 0], Q[:, 2])
    el = np.arcsin(np.clip(Q[:, 1] / np.maximum(r, 1e-12), -1, 1))
    return az, el, r


class Envolvente:
    def __init__(self, centro, puntos, nb=(144, 72), sigma=2.5, modo="max"):
        from scipy.ndimage import gaussian_filter, maximum_filter
        self.c = np.asarray(centro, float)
        na, ne = nb
        az, el, r = _esf(puntos, self.c)
        ia = np.clip(((az + np.pi) / (2 * np.pi) * na).astype(int), 0, na - 1)
        ie = np.clip(((el + np.pi / 2) / np.pi * ne).astype(int), 0, ne - 1)
        G = np.zeros((na, ne))
        np.maximum.at(G, (ia, ie), r)
        for _ in range(40):                                   # huecos: el máximo de los vecinos
            vacio = G == 0
            if not vacio.any():
                break
            M = maximum_filter(np.pad(G, ((2, 2), (1, 1)), mode="wrap"), size=3)[2:-2, 1:-1]
            G[vacio] = M[vacio]
        Gp = np.pad(G, ((3 * int(sigma) + 3,) * 2, (0, 0)), mode="wrap")
        G = gaussian_filter(Gp, sigma=(sigma, sigma), mode=("wrap", "nearest"))[3 * int(sigma) + 3:-(3 * int(sigma) + 3)]
        self.G = G
        self.az_c = (np.arange(na) + 0.5) / na * 2 * np.pi - np.pi
        self.el_c = (np.arange(ne) + 0.5) / ne * np.pi - np.pi / 2

    def R(self, P):
        from scipy.interpolate import RegularGridInterpolator
        az, el, _ = _esf(P, self.c)
        azp = np.r_[self.az_c[-1] - 2 * np.pi, self.az_c, self.az_c[0] + 2 * np.pi]
        Gp = np.vstack([self.G[-1:], self.G, self.G[:1]])
        f = RegularGridInterpolator((azp, self.el_c), Gp, bounds_error=False, fill_value=None)
        return f(np.c_[az, np.clip(el, self.el_c[0], self.el_c[-1])])


def rehacer(relleno, contorno, piel, centro, iter_=150, holgura=0.004, T=None, **_):
    """V48.3 (2.º intento). La envolvente por dirección inflaba la nuca: desde el centro, la orilla enrollada queda
    "lejos" y el máximo la arrastraba. Aquí se suaviza SOLO el radio de cada vértice sobre la propia malla del pelo
    (promedio con sus vecinos, `iter_` pasadas), con la orilla fija: la terraza, una arruga radial, desaparece y la
    forma grande no cambia. CONTORNO toma la misma razón de radio que su vértice más cercano de RELLENO. Piso: piel +
    `holgura`. T: triángulos de RELLENO."""
    from scipy.spatial import cKDTree
    c = np.asarray(centro, float)
    _, inv = np.unique(np.round(relleno, 6), axis=0, return_inverse=True); inv = inv.ravel()
    n = inv.max() + 1
    W = np.zeros((n, 3)); W[inv] = relleno
    Tw = inv[T]
    e = np.sort(np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    borde = np.zeros(n, bool); borde[np.unique(u[cnt == 1])] = True
    E = np.unique(e, axis=0)
    deg = np.bincount(E.ravel(), minlength=n).astype(float)
    Q = W - c
    r0 = np.linalg.norm(Q, axis=1); d = Q / np.maximum(r0, 1e-12)[:, None]
    r = r0.copy()
    for _ in range(iter_):
        s_ = np.zeros(n); np.add.at(s_, E[:, 0], r[E[:, 1]]); np.add.at(s_, E[:, 1], r[E[:, 0]])
        rn = 0.5 * r + 0.5 * s_ / np.maximum(deg, 1)
        r = np.where(borde, r0, rn)
    # sin piso: la piel de abajo, que no se ve, se mete donde haga falta (meter_piel)
    W1 = c + d * r[:, None]
    k = r / np.maximum(r0, 1e-12)
    R1 = W1[inv]
    # CONTORNO: misma razón que el vértice de RELLENO más cercano
    _, j = cKDTree(W).query(contorno)
    Qc = contorno - c
    C1 = c + Qc * k[j][:, None]
    return R1, C1


def meter_piel(piel, relleno_nuevo, centro, holgura=0.003, cono=0.012):
    """La piel escondida bajo el pelo se mete hasta quedar `holgura` por debajo de él, en cada dirección donde hay pelo
    (cono de ~0.7°). Afuera del pelo no se toca. Devuelve la piel nueva y cuántos vértices se movieron."""
    from scipy.spatial import cKDTree
    c = np.asarray(centro, float)
    Qh = relleno_nuevo - c; rh = np.linalg.norm(Qh, axis=1); dh = Qh / np.maximum(rh, 1e-12)[:, None]
    Qs = piel - c; rs = np.linalg.norm(Qs, axis=1); ds = Qs / np.maximum(rs, 1e-12)[:, None]
    vec = cKDTree(dh).query_ball_point(ds, r=cono)
    tope = np.array([rh[v].min() - holgura if len(v) else np.inf for v in vec])
    r2 = np.minimum(rs, tope)
    return c + ds * r2[:, None], int((r2 < rs - 1e-7).sum())
