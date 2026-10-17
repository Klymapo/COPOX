"""Clasificación por color de la paleta plana ALTH-META.

La MISMA regla se aplica a las referencias (píxeles) y al modelo (color base
de cada triángulo, sin luz), así las dos máscaras son comparables.
Clases: 0 fondo · 1 pelo · 2 piel · 3 claro (camisa/esclerótica) ·
4 oscuro (chaleco, ojos, cejas, zapatos) · 5 azul (pantalón, corbata, short).
"""
from __future__ import annotations

from collections import deque

import numpy as np

FONDO, PELO, PIEL, CLARO, OSCURO, AZUL = range(6)
NOMBRES = {0: "fondo", 1: "pelo", 2: "piel", 3: "claro", 4: "oscuro", 5: "azul"}
COLORES = {0: (236, 236, 236), 1: (215, 180, 110), 2: (245, 185, 145), 3: (250, 250, 250), 4: (40, 40, 40), 5: (60, 80, 150)}

# umbral de tono (g-b)/(r-b) que separa piel (<) de pelo rubio (>=); medido en refs: piel 0.37-0.45, pelo 0.54-0.62
CORTE_TONO = 0.52


def clasificar(rgb: np.ndarray) -> np.ndarray:
    """rgb en 0-255 (…,3). Devuelve clases sin decidir fondo (0 solo si nada aplica)."""
    rgb = rgb.astype(float)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / (mx + 1e-6)
    tono = (g - b) / (r - b + 1e-6)
    oscuro = mx < 95
    azul = ((b > r + 18) & ~oscuro) | ((b > r + 15) & oscuro)
    calido = (r > b + 40) & ~oscuro
    claro = (sat < 0.2) & (mx >= 150)
    C = np.zeros(rgb.shape[:-1], np.uint8)
    C[claro] = CLARO
    C[calido & (tono >= CORTE_TONO)] = PELO
    C[calido & (tono < CORTE_TONO)] = PIEL
    C[oscuro & ~azul] = OSCURO
    C[azul] = AZUL
    C[(C == 0) & (mx < 140)] = OSCURO
    C[(C == 0)] = CLARO
    return C


def fondo_por_inundacion(rgb: np.ndarray, sat_max=0.06, val_min=200) -> np.ndarray:
    """Fondo = gris claro neutro conectado al borde (no se confunde con la camisa interior)."""
    rgb = rgb.astype(float)
    mx, mn = rgb.max(-1), rgb.min(-1)
    cand = ((mx - mn) / (mx + 1e-6) < sat_max) & (mx > val_min)
    H, W = cand.shape
    vis = np.zeros_like(cand)
    q = deque()
    for y in range(H):
        for x in (0, W - 1):
            if cand[y, x] and not vis[y, x]:
                vis[y, x] = True; q.append((y, x))
    for x in range(W):
        for y in (0, H - 1):
            if cand[y, x] and not vis[y, x]:
                vis[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and cand[yy, xx] and not vis[yy, xx]:
                vis[yy, xx] = True; q.append((yy, xx))
    return vis


def segmentar_referencia(rgb: np.ndarray, quitar_sombra_piso=True, hueco_min=0.002) -> np.ndarray:
    C = clasificar(rgb)
    C[fondo_por_inundacion(rgb)] = FONDO
    # huecos encerrados de fondo (p. ej. entre las piernas): gris neutro claro en manchas grandes
    from .piezas import componentes
    rgbf = rgb.astype(float)
    mx, mn = rgbf.max(-1), rgbf.min(-1)
    neutro = ((mx - mn) / (mx + 1e-6) < 0.06) & (mx > 185) & (C != FONDO)
    for c in componentes(neutro, int(hueco_min * C.size)):
        sub = neutro[c["y0"]:c["y1"] + 1, c["x0"]:c["x1"] + 1]
        C[c["y0"]:c["y1"] + 1, c["x0"]:c["x1"] + 1][sub] = FONDO
    if quitar_sombra_piso:
        # sombra de contacto: gris medio sin croma bajo los pies, más ancha que el personaje
        rgbf = rgb.astype(float)
        mx, mn = rgbf.max(-1), rgbf.min(-1)
        sombra = ((mx - mn) < 14) & (mx > 120) & (C == CLARO)
        filas = np.nonzero((C != FONDO).any(1))[0]
        if len(filas):
            corte = int(filas.max() - 0.12 * (filas.max() - filas.min()))
            sombra[:corte] = False  # solo en la franja de los pies
            C[sombra] = FONDO
    return C


def colorear(C: np.ndarray) -> np.ndarray:
    out = np.zeros(C.shape + (3,), np.uint8)
    for k, v in COLORES.items():
        out[C == k] = v
    return out
