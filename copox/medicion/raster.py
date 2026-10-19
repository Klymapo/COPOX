"""Rasterizador NumPy con z-buffer que produce, en una pasada, la imagen por
clases de pieza (misma paleta que las referencias), un RGB sombreado y la
profundidad. ``silueta_rapida`` es una aproximación por salpicado de puntos
para búsquedas de cámara/pose (rápida, baja resolución)."""
from __future__ import annotations

import numpy as np

from .camara import Camara
from .gltf import Modelo
from . import paleta


class Escena:
    """Triángulos de un modelo en una pose, con su clase y color."""

    def __init__(self, modelo: Modelo, clip: str | None = None, frac: float = 0.0, excluir_nodos: tuple = ()):
        pos = modelo.posar(clip, frac)
        T, C, K = [], [], []
        for p, P in zip(modelo.prims, pos):
            nombre = modelo.j["nodes"][p.nodo].get("name", "")
            if nombre in excluir_nodos:
                continue
            rgb, vis = modelo.color_triangulos(p)
            tri = P[p.indices][vis]
            col = rgb[vis]
            T.append(tri); C.append(col); K.append(paleta.clasificar((col * 255)[None])[0])
        self.T = np.concatenate(T)
        self.rgb = np.concatenate(C)
        self.clase = np.concatenate(K)
        self.clip, self.frac = clip, frac


def _a_pixeles(xy, escala, centro, tam):
    x, y = xy
    return centro[0] + x * escala, centro[1] - y * escala


def render(esc: Escena, cam: Camara, escala: float, centro: tuple, tam: tuple, fondo=paleta.COLORES[0]):
    """escala: px por unidad del modelo en el plano del objetivo; centro: px del objetivo; tam: (alto, ancho)."""
    H, W = tam
    P = esc.T.reshape(-1, 3)
    x, y, z = cam.proyectar(P)
    X, Y = _a_pixeles((x, y), escala, centro, tam)
    X, Y, Z = X.reshape(-1, 3), Y.reshape(-1, 3), z.reshape(-1, 3)
    der, arriba, hc = cam.base()
    N = np.cross(esc.T[:, 1] - esc.T[:, 0], esc.T[:, 2] - esc.T[:, 0])
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    luz = 0.6 * hc + 0.5 * arriba + 0.3 * der
    luz /= np.linalg.norm(luz)
    som = 0.45 + 0.55 * np.abs(N @ luz)
    cls = np.zeros((H, W), np.uint8)
    img = np.ones((H, W, 3)) * np.array(fondo) / 255
    zb = np.full((H, W), -np.inf)
    vis = (X.max(1) >= 0) & (X.min(1) < W) & (Y.max(1) >= 0) & (Y.min(1) < H)
    for k in np.nonzero(vis)[0]:
        xs, ys, zs = X[k], Y[k], Z[k]
        x0, x1 = max(0, int(np.floor(xs.min()))), min(W - 1, int(np.ceil(xs.max())))
        y0, y1 = max(0, int(np.floor(ys.min()))), min(H - 1, int(np.ceil(ys.max())))
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        zz = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= zz > sub
        sub[m] = zz[m]
        cls[y0:y1 + 1, x0:x1 + 1][m] = esc.clase[k]
        img[y0:y1 + 1, x0:x1 + 1][m] = esc.rgb[k] * som[k]
    return cls, (np.clip(img, 0, 1) * 255).astype(np.uint8)


def silueta_rapida(esc: Escena, cam: Camara, escala: float, centro: tuple, tam: tuple, excluir_clases=()) -> np.ndarray:
    """Silueta binaria aproximada por salpicado de vértices + centroides + puntos medios de aristas."""
    H, W = tam
    keep = ~np.isin(esc.clase, excluir_clases) if excluir_clases else np.ones(len(esc.T), bool)
    T = esc.T[keep]
    pts = np.concatenate([T.reshape(-1, 3), T.mean(1), (T[:, 0] + T[:, 1]) / 2, (T[:, 1] + T[:, 2]) / 2, (T[:, 0] + T[:, 2]) / 2])
    x, y, _ = cam.proyectar(pts)
    X, Y = _a_pixeles((x, y), escala, centro, tam)
    X, Y = np.round(X).astype(int), np.round(Y).astype(int)
    ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
    M = np.zeros((H, W), bool)
    M[Y[ok], X[ok]] = True
    # cierre 3x3 para tapar huecos del salpicado
    D = M.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            D |= np.roll(np.roll(M, dy, 0), dx, 1)
    E = D.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            E &= np.roll(np.roll(D, dy, 0), dx, 1)
    return E | M
