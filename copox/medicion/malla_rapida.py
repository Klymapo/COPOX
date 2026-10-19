"""SENKU · fabricación rápida de mallas implícitas (19 oct 2026).

Medido en el pelo por mechones de V49: 569 s en `malla()`, casi todo evaluando el campo en puntos de la rejilla fina
que están lejos de la superficie (y no cambian nada). Aquí:
  1. `malla_banda`: rejilla gruesa primero (factor× más gruesa), se interpola a la fina y SOLO se evalúa el campo exacto
     donde la interpolación queda cerca de cero (banda de `banda`× el paso grueso). Lejos, el signo interpolado basta
     para marching cubes. Para piezas delgadas el margen es amplio (banda 2.5 pasos gruesos).
     ALTH_MALLA=exacta evalúa todo (como antes): sirve para reproducir bit a bit GLB publicados con recetas viejas.
  2. Calidad por variable de entorno: ALTH_CALIDAD=borrador → paso ×2 y sin simplificar con Godot (iteración rápida);
     final (por defecto) → como siempre. Las recetas no cambian: solo leen `paso()` y `simplificar_activo()`.
"""
from __future__ import annotations

import os
import time

import numpy as np

REGISTRO: list = []                      # (etiqueta, segundos, puntos_exactos, puntos_totales) para medir


def calidad() -> str:
    return os.environ.get("ALTH_CALIDAD", "final").strip().lower()


def paso(p: float) -> float:
    return p * 2.0 if calidad() == "borrador" else p


def simplificar_activo() -> bool:
    return calidad() != "borrador"


def malla_banda(sdf, lo, hi, paso_fino, factor=3, banda=2.5, lote=400_000, pulido=2, etiqueta="malla", rellenar=False):
    """Marching cubes con evaluación en dos niveles. `sdf(P)` -> distancia con signo aproximada (negativa adentro).
    Devuelve V, T (sin orientar ni simplificar; mismo contrato que las mallas de antes)."""
    from scipy.ndimage import map_coordinates
    from skimage.measure import marching_cubes
    from .mano_geo import taubin
    t0 = time.time()
    paso_fino = paso(paso_fino)                       # borrador: rejilla 2× más gruesa en todas las recetas
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    n = np.ceil((hi - lo) / paso_fino).astype(int) + 1
    pg = paso_fino * factor
    ng = np.ceil((hi - lo) / pg).astype(int) + 2
    ejes_g = [lo[i] + pg * np.arange(ng[i]) for i in range(3)]
    G = np.stack(np.meshgrid(*ejes_g, indexing="ij"), -1).reshape(-1, 3)
    Fg = np.empty(len(G), np.float32)
    for k in range(0, len(G), lote):
        Fg[k:k + lote] = sdf(G[k:k + lote])
    Fg = Fg.reshape(ng)
    if rellenar:
        # campos que lejos de la pieza dicen "afuera" aunque sea el interior profundo (p. ej. ropa_ajustada.Pieza):
        # lo positivo que no conecta con el borde de la caja es adentro
        from scipy.ndimage import label
        lab, _ = label(Fg > 0)
        borde = np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                          lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
        Fg[(Fg > 0) & ~np.isin(lab, borde)] = -pg * 3
    umbral = banda * pg
    if os.environ.get("ALTH_MALLA", "").lower() == "exacta":
        umbral = np.inf
    F = np.empty(n, np.float32)
    ejes = [lo[i] + paso_fino * np.arange(n[i]) for i in range(3)]
    gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
    exactos = 0
    for ix in range(n[0]):
        cx = np.full(gy.size, (ejes[0][ix] - lo[0]) / pg)
        coords = np.stack([cx, (gy.ravel() - lo[1]) / pg, (gz.ravel() - lo[2]) / pg])
        f = map_coordinates(Fg, coords, order=1, mode="nearest").astype(np.float32)
        cerca = np.abs(f) < umbral
        if cerca.any():
            g = np.stack([np.full(int(cerca.sum()), ejes[0][ix]), gy.ravel()[cerca], gz.ravel()[cerca]], 1)
            f[cerca] = sdf(g)
            exactos += int(cerca.sum())
        F[ix] = f.reshape(n[1], n[2])
    V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso_fino,) * 3)
    V = V + lo
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    if pulido:
        V = taubin(V, T, pulido)
    REGISTRO.append((etiqueta, round(time.time() - t0, 1), exactos, int(np.prod(n))))
    return V, T
