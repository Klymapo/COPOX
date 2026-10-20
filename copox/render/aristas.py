"""Nitidez de aristas · cuánto «dibujo» interno tiene la figura (20 oct 2026, ruta AAA §4.4).

Ninguna métrica veía lo «blando»: un abrigo inflado pasaba 15/0. Esta mide, dentro de la silueta (sin el contorno),
la fracción de píxeles con cambio de sombreado fuerte (Sobel sobre luminancia normalizada por el contraste de la propia
figura) y la compara con la referencia. Las referencias ALTH son bloques con bisel → muchos bordes internos nítidos;
una malla blanda da gradientes suaves → pocos.

  densidad(img, mascara) → fracción de píxeles internos con borde fuerte
  comparar(render_color, render_mascara, ref) → {"render": d, "ref": d, "razon": d_render / d_ref}
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def _lum(a):
    a = a.astype(float)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def _sobel(L):
    k = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], float)
    P = np.pad(L, 1, mode="edge")
    gx = sum(k[i, j] * P[i:i + L.shape[0], j:j + L.shape[1]] for i in range(3) for j in range(3))
    gy = sum(k.T[i, j] * P[i:i + L.shape[0], j:j + L.shape[1]] for i in range(3) for j in range(3))
    return np.hypot(gx, gy)


def _erosion(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * r + 1))
    return np.asarray(im) > 127


def mascara_fondo(a, tol=28):
    """Objeto = lo que difiere del color de las esquinas (referencias con fondo liso)."""
    esquinas = np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3), a[-8:, :8].reshape(-1, 3), a[-8:, -8:].reshape(-1, 3)])
    fondo = np.median(esquinas, 0)
    return np.linalg.norm(a.astype(float) - fondo, axis=2) > tol


def densidad(img, mascara, lado=512, umbral=0.18):
    """Fracción de píxeles internos (silueta erosionada) con gradiente > umbral × rango de luminancia de la figura."""
    a = np.asarray(img.convert("RGB"))
    m = np.asarray(mascara) if not isinstance(mascara, np.ndarray) else mascara
    ys, xs = np.nonzero(m)
    if len(ys) < 100:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    a, m = a[y0:y1, x0:x1], m[y0:y1, x0:x1]
    s = lado / max(a.shape[:2])
    tam = (max(1, int(a.shape[1] * s)), max(1, int(a.shape[0] * s)))
    a = np.asarray(Image.fromarray(a).resize(tam, Image.BILINEAR))
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(tam, Image.NEAREST)) > 127
    L = _lum(a)
    dentro = _erosion(m, 3)
    if dentro.sum() < 50:
        return None
    rango = np.percentile(L[dentro], 95) - np.percentile(L[dentro], 5)
    G = _sobel(L) / max(rango, 1e-6) / 8.0
    return float((G[dentro] > umbral).mean())


def comparar(render_color, render_mascara, ref):
    rc = Image.open(render_color)
    rm = np.asarray(Image.open(render_mascara).convert("L")) > 0
    ri = Image.open(ref).convert("RGB")
    dr = densidad(rc, rm)
    df = densidad(ri, mascara_fondo(np.asarray(ri)))
    return {"render": None if dr is None else round(dr, 4), "ref": None if df is None else round(df, 4),
            "razon": None if not (dr and df) else round(dr / df, 3)}
