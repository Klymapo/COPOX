"""Rasterizador vectorizado (NumPy) con z-buffer.

Agrupa los triángulos por tamaño de su caja en píxeles y evalúa todos los
píxeles candidatos de un grupo a la vez; luego resuelve la profundidad con un
ordenamiento (gana el más cercano). Devuelve capas por píxel: triángulo,
baricéntricas en pantalla y profundidad.

Convención: X, Y en píxeles (Y hacia abajo), centros de píxel en i + 0.5;
Z mayor = más cerca de la cámara.
"""
from __future__ import annotations

import numpy as np

_LIMITE = 3_000_000  # candidatos por lote (memoria)


def rasterizar(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, tam: tuple, descartar=None):
    """X, Y, Z: (N, 3). tam: (alto, ancho).
    descartar(ids, b0, b1, b2) -> máscara booleana de candidatos a quitar (p. ej. alfa MASK).
    Devuelve (tri (H,W) int32 con -1 en fondo, bary (H,W,3) float32, prof (H,W) float32)."""
    H, W = tam
    N = len(X)
    x0 = np.ceil(X.min(1) - 0.5).astype(np.int64)
    x1 = np.floor(X.max(1) - 0.5).astype(np.int64)
    y0 = np.ceil(Y.min(1) - 0.5).astype(np.int64)
    y1 = np.floor(Y.max(1) - 0.5).astype(np.int64)
    x0c, x1c = np.maximum(x0, 0), np.minimum(x1, W - 1)
    y0c, y1c = np.maximum(y0, 0), np.minimum(y1, H - 1)
    d = (Y[:, 1] - Y[:, 2]) * (X[:, 0] - X[:, 2]) + (X[:, 2] - X[:, 1]) * (Y[:, 0] - Y[:, 2])
    ok = (x1c >= x0c) & (y1c >= y0c) & (np.abs(d) > 1e-12)
    w = np.where(ok, x1c - x0c + 1, 0)
    h = np.where(ok, y1c - y0c + 1, 0)
    k = np.maximum(w, h)
    # coeficientes de las funciones de arista
    inv = np.where(ok, 1.0 / np.where(ok, d, 1.0), 0.0)
    a0, b0_ = (Y[:, 1] - Y[:, 2]) * inv, (X[:, 2] - X[:, 1]) * inv
    a1, b1_ = (Y[:, 2] - Y[:, 0]) * inv, (X[:, 0] - X[:, 2]) * inv

    pix_l, z_l, t_l, u_l, v_l = [], [], [], [], []
    pot = 2 ** np.arange(13)
    bw = pot[np.minimum(np.searchsorted(pot, np.maximum(w, 1)), 12)]
    bh = pot[np.minimum(np.searchsorted(pot, np.maximum(h, 1)), 12)]
    clave = np.where(ok, bw * 8192 + bh, -1)
    for cl in np.unique(clave[ok]):
        sw, sh = int(cl // 8192), int(cl % 8192)
        sel = np.nonzero(clave == cl)[0]
        por_lote = max(1, _LIMITE // (sw * sh))
        dy, dx = np.divmod(np.arange(sw * sh), sw)
        for i in range(0, len(sel), por_lote):
            ids = sel[i:i + por_lote]
            px = x0c[ids, None] + dx[None]
            py = y0c[ids, None] + dy[None]
            m = (px <= x1c[ids, None]) & (py <= y1c[ids, None])
            gx, gy = px + 0.5, py + 0.5
            ex, ey = gx - X[ids, 2:3], gy - Y[ids, 2:3]
            l0 = a0[ids, None] * ex + b0_[ids, None] * ey
            l1 = a1[ids, None] * ex + b1_[ids, None] * ey
            l2 = 1.0 - l0 - l1
            m &= (l0 >= -1e-7) & (l1 >= -1e-7) & (l2 >= -1e-7)
            r, c = np.nonzero(m)
            if len(r) == 0:
                continue
            tid = ids[r]
            l0s, l1s = l0[r, c], l1[r, c]
            l2s = 1.0 - l0s - l1s
            if descartar is not None:
                q = ~descartar(tid, l0s, l1s, l2s)
                tid, l0s, l1s, l2s, r, c = tid[q], l0s[q], l1s[q], l2s[q], r[q], c[q]
            z = l0s * Z[tid, 0] + l1s * Z[tid, 1] + l2s * Z[tid, 2]
            pix_l.append(py[r, c] * W + px[r, c]); z_l.append(z); t_l.append(tid)
            u_l.append(l0s); v_l.append(l1s)
    tri = np.full(H * W, -1, np.int32)
    bary = np.zeros((H * W, 3), np.float32)
    prof = np.full(H * W, -np.inf, np.float32)
    if pix_l:
        pix, z = np.concatenate(pix_l), np.concatenate(z_l)
        o = np.lexsort((z, pix))
        pix_s = pix[o]
        ult = np.r_[pix_s[1:] != pix_s[:-1], True]
        g = o[ult]
        P = pix[g]
        tri[P] = np.concatenate(t_l)[g]
        u, v = np.concatenate(u_l)[g], np.concatenate(v_l)[g]
        bary[P, 0], bary[P, 1], bary[P, 2] = u, v, 1 - u - v
        prof[P] = z[g]
    return tri.reshape(H, W), bary.reshape(H, W, 3), prof.reshape(H, W)
