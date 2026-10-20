"""Revisor visual automático · COMPARATIVA por región (19 oct 2026).

Admin: que nada le llegue sin que alguien lo compare antes contra la referencia (los «hombros blancos» se escaparon
porque se juzgó a ojo la hoja completa). CHXP V3 arma una lámina <nombre>_COMPARATIVA.png: filas = regiones (cabeza,
hombros y torso, cadera y piernas, pies), columnas = referencia | render en frente y espalda, a la misma escala relativa.
Esa lámina (más HOJA y AUDITORIA.json) es la entrada del agente `revisor-visual-alth` (solo lectura), que corre ANTES
de mandar nada a Admin (skills crear-avatar y publicar-version).
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw

FONDO_MASCARA = np.array([227, 226, 233])
REGIONES = (("cabeza", "Neck", None), ("hombros y torso", "Hips", "Neck"), ("cadera y piernas", "LeftFoot", "Hips"),
            ("pies", None, "LeftFoot"))


def _mascara_render(ruta):
    a = np.asarray(Image.open(ruta).convert("RGB")).astype(int)
    return np.abs(a - FONDO_MASCARA).max(2) > 10


def _bandas(m, fr):
    """Filas (y0, y1) de cada región en una máscara, con las alturas relativas fr[nombre] = (ab, ar) en 0..1 (0 piso)."""
    filas = np.nonzero(m.any(1))[0]
    techo, piso = filas.min(), filas.max()
    alto = piso - techo
    return {k: (int(piso - ar * alto), int(piso - ab * alto)) for k, (ab, ar) in fr.items()}, techo, piso


def _recorte(img, m, y0, y1, ancho_rel, alto_total):
    cols = np.nonzero(m[max(y0, 0):max(y1, 1)].any(0))[0]
    cx = (cols.min() + cols.max()) / 2 if len(cols) else img.shape[1] / 2
    w = int(ancho_rel * alto_total / 2)
    x0, x1 = int(max(cx - w, 0)), int(min(cx + w, img.shape[1]))
    return Image.fromarray(img[max(y0 - 6, 0):y1 + 6, x0:x1].astype(np.uint8))


def lamina(glb, ref, salida, nombre, hoja2x2=True):
    from copox.medicion import senku_ref as sr
    J = sr.esqueleto(glb)
    V0, _ = sr.malla_visible(glb)
    alto = float(V0[:, 1].max())

    def rel(n):
        return 0.0 if n is None else (1.0 if n == "top" else float(J[n][1]) / alto) if n in J or n in (None, "top") else 0.5
    fr = {k: (rel(ab), rel(ar if ar else "top")) for k, ab, ar in REGIONES}
    hoja = sr.cargar_hoja(ref)
    filas_img = []
    for v in ("frente", "espalda"):
        rp = os.path.join(salida, f"{nombre}_{v}.png"); mp = os.path.join(salida, f"{nombre}_{v}_mascara.png")
        if v not in hoja or not os.path.exists(rp) or not os.path.exists(mp):
            continue
        img_r = np.asarray(Image.open(rp).convert("RGB")); m_r = _mascara_render(mp)
        img_h, m_h = hoja[v]["img"], hoja[v]["objeto"]
        b_r, t_r, p_r = _bandas(m_r, fr)
        b_h, t_h, p_h = _bandas(m_h, fr)
        for k, _, _ in REGIONES:
            ancho = 0.62 if k != "cabeza" else 0.75
            a = _recorte(img_h, m_h, *b_h[k], ancho, p_h - t_h)
            b = _recorte(img_r, m_r, *b_r[k], ancho, p_r - t_r)
            filas_img.append((f"{v} · {k}", a, b))
    if not filas_img:
        return None
    H = 230
    celdas = []
    for t, a, b in filas_img:
        a = a.resize((max(1, int(a.width * H / max(a.height, 1))), H)); b = b.resize((max(1, int(b.width * H / max(b.height, 1))), H))
        celdas.append((t, a, b))
    W = max(a.width + b.width for _, a, b in celdas) + 60
    out = Image.new("RGB", (W, (H + 34) * len(celdas) + 40), (250, 250, 250))
    d = ImageDraw.Draw(out)
    d.text((14, 10), f"CHXP V3 · COMPARATIVA por región · {nombre}   (izquierda: referencia · derecha: render)", fill=(30, 30, 30))
    y = 40
    for t, a, b in celdas:
        d.text((14, y), t, fill=(90, 90, 90))
        out.paste(a, (14, y + 18)); out.paste(b, (14 + a.width + 30, y + 18))
        y += H + 34
    ruta = os.path.join(salida, f"{nombre}_COMPARATIVA.png")
    out.save(ruta)
    return ruta
