"""Medición por piezas sobre mapas de clases (referencia o render del modelo).

Todo se reporta en ED (distancia entre centros de ojos de la vista frontal) y,
verticalmente, respecto a la línea de ojos. Las mismas funciones miden la
referencia y el modelo: no hay regiones fijas que presupongan proporciones.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from .paleta import FONDO, PELO, PIEL, CLARO, OSCURO, AZUL


def componentes(M: np.ndarray, minimo: int = 10) -> list[dict]:
    H, W = M.shape
    lab = np.zeros((H, W), np.int32)
    out = []
    n = 0
    for y0, x0 in zip(*np.nonzero(M)):
        if lab[y0, x0]:
            continue
        n += 1
        q = deque([(y0, x0)]); lab[y0, x0] = n; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and M[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; q.append((yy, xx))
        if len(pts) >= minimo:
            p = np.array(pts)
            out.append(dict(n=len(p), y0=int(p[:, 0].min()), y1=int(p[:, 0].max()), x0=int(p[:, 1].min()), x1=int(p[:, 1].max()),
                            cy=float(p[:, 0].mean()), cx=float(p[:, 1].mean())))
    return out


def extremos(C):
    fg = C != FONDO
    ys = np.nonzero(fg.any(1))[0]
    return int(ys.min()), int(ys.max())


def ojos(C: np.ndarray):
    """Par de ojos: componentes oscuros/con iris en la mitad superior, emparejados por tamaño y altura.
    Devuelve lista de 0, 1 o 2 componentes ordenados de izquierda a derecha."""
    top, bot = extremos(C)
    zona = C == OSCURO
    zona[int(top + 0.42 * (bot - top)):] = False

    def rodeado_de_piel(c, m=4):
        y0, y1 = max(c['y0'] - m, 0), min(c['y1'] + m, C.shape[0] - 1)
        x0, x1 = max(c['x0'] - m, 0), min(c['x1'] + m, C.shape[1] - 1)
        caja = C[y0:y1 + 1, x0:x1 + 1]
        anillo = np.ones(caja.shape, bool)
        anillo[m:-m or None, m:-m or None] = False
        vec = caja[anillo]
        vec = vec[vec != OSCURO]
        return len(vec) > 0 and np.mean(np.isin(vec, (PIEL, CLARO))) >= 0.5

    # ojo: tamaño acotado y rodeado de piel/esclerótica (descarta chaleco, cejas pegadas al pelo y ropa)
    cs = [c for c in componentes(zona, 20) if 8 <= (c['y1'] - c['y0']) <= 0.12 * (bot - top) and 6 <= (c['x1'] - c['x0']) <= 0.12 * (bot - top)
          and rodeado_de_piel(c)]
    if len(cs) < 2:
        return sorted(cs, key=lambda c: -c['n'])[:1]
    mejor, puntaje = None, -1
    for i in range(len(cs)):
        for k in range(i + 1, len(cs)):
            a, b = cs[i], cs[k]
            sim = min(a['n'], b['n']) / max(a['n'], b['n'])
            dy = abs(a['cy'] - b['cy']) / max(a['y1'] - a['y0'], 1)
            dx = abs(a['cx'] - b['cx'])
            if dy > 0.6 or dx < 1.2 * max(a['x1'] - a['x0'], b['x1'] - b['x0']):
                continue
            # preferir el par más bajo (las cejas quedan arriba) y más grande
            p = sim * (a['n'] + b['n']) * (1 + (a['cy'] + b['cy']) / (2 * (bot - top)))
            if p > puntaje:
                mejor, puntaje = (a, b), p
    return sorted(mejor, key=lambda c: c['cx']) if mejor else sorted(cs, key=lambda c: -c['n'])[:1]


def centro_cabeza(C, top, alto):
    """Columna central de la cabeza (piel+pelo en la franja superior del 30 %)."""
    band = ((C == PELO) | (C == PIEL))[top:top + int(0.3 * alto)]
    xs = np.nonzero(band.any(0))[0]
    return float((xs.min() + xs.max()) / 2) if len(xs) else float(C.shape[1] / 2)


def perfil_anchos(C: np.ndarray, y_ojos: float, ed: float, x_centro: float, alturas: np.ndarray, clases=None):
    """Para cada altura (ED bajo la línea de ojos; negativo = arriba) devuelve
    (izquierda, derecha, ancho) en ED respecto a x_centro. ``clases`` limita qué cuenta como cuerpo."""
    fg = (C != FONDO) if clases is None else np.isin(C, clases)
    out = []
    for h in alturas:
        y = int(round(y_ojos + h * ed))
        if y < 0 or y >= C.shape[0]:
            out.append((None, None, None)); continue
        xs = np.nonzero(fg[y])[0]
        if not len(xs):
            out.append((0.0, 0.0, 0.0)); continue
        izq, der = (x_centro - xs.min()) / ed, (xs.max() - x_centro) / ed
        out.append((float(izq), float(der), float(izq + der)))
    return out


def medidas(C: np.ndarray, ed_px: float, y_ojos: float, x_centro: float) -> dict:
    """Puntos de referencia genéricos en ED. y_ojos/x_centro definen el origen."""
    top, bot = extremos(C)
    fg = C != FONDO
    m = {"coronilla": (top - y_ojos) / ed_px, "suela": (bot - y_ojos) / ed_px}
    # pelo y piel de cabeza
    for nombre, cl in (("pelo", PELO), ("piel", PIEL), ("oscuro", OSCURO), ("azul", AZUL), ("claro", CLARO)):
        ys, xs = np.nonzero(C == cl)
        m[f"area_{nombre}"] = float(len(ys) / ed_px ** 2)
    ys = np.nonzero((C == PELO).any(1))[0]
    if len(ys):
        m["pelo_arriba"] = (ys.min() - y_ojos) / ed_px
    # cabeza: ancho máximo de pelo+piel desde la coronilla hasta 0.75 ED bajo los ojos (antes de hombros/manos)
    cab = ((C == PELO) | (C == PIEL))[max(top, 0):int(y_ojos + 0.75 * ed_px)]
    xs = np.nonzero(cab.any(0))[0]
    if len(xs):
        m["cabeza_ancho"] = (xs.max() - xs.min()) / ed_px
    # entrepierna: primera fila bajo el 62 % donde la columna central deja de ser pierna
    piernas = np.isin(C, (AZUL, PIEL, OSCURO))
    xc = int(round(x_centro))
    col = piernas[:, max(0, xc - 2):xc + 3].all(1)
    inicio = int(top + 0.62 * (bot - top))
    lleno = [y for y in range(inicio, bot) if col[y]]
    if lleno:
        y0 = lleno[0]
        hueco = next((y for y in range(y0, bot) if not col[y]), None)
        if hueco is not None:
            m["entrepierna"] = (hueco - y_ojos) / ed_px
    # ancho máximo del cuerpo (incluye brazos) y su altura
    anchos = fg.sum(1)
    y_max = int(np.argmax(anchos[int(y_ojos + 0.8 * ed_px):bot])) + int(y_ojos + 0.8 * ed_px)
    xs = np.nonzero(fg[y_max])[0]
    m["ancho_max"] = (xs.max() - xs.min()) / ed_px
    m["ancho_max_altura"] = (y_max - y_ojos) / ed_px
    # pies: ancho en la fila 2 % sobre la suela
    yp = int(bot - 0.02 * (bot - top))
    xs = np.nonzero(fg[yp])[0]
    m["pies_ancho"] = (xs.max() - xs.min()) / ed_px if len(xs) else None
    return m


def iou_por_clase(Ca: np.ndarray, Cb: np.ndarray, grupos: dict) -> dict:
    out = {}
    for nombre, cls in grupos.items():
        a, b = np.isin(Ca, cls), np.isin(Cb, cls)
        u = (a | b).sum()
        out[nombre] = float((a & b).sum() / u) if u else None
    return out
