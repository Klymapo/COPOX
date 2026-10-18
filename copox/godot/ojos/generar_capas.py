"""Capas de ojo para el shader de mirada (Godot): base, iris y encima, por ojo (L, R).

Mismo diseño y mismo mapeo UV que la textura horneada en el GLB (receta_theo_v05.textura_ojo):
- base: esclerótica con sombra del párpado; alfa = forma de la abertura (fuera de ella, el shader descarta).
- iris: iris, pupila y brillo en su posición de reposo, sobre fondo transparente; el shader lo desplaza.
- encima: línea gruesa del párpado (no se mueve con la mirada).
Uso: python generar_capas.py [carpeta_salida]
"""
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "..", "docs", "medicion"))
import receta_theo_v05 as v5  # noqa: E402

A, B, Y0 = 0.325, 0.285, 0.005
IRIS_W, IRIS_H, XI, YI, PARPADO = 0.215, 0.34, -0.04, 0.025, 0.085


def capas(lado):
    m = v5.OJO[lado]
    Xo, Y, Xw = v5._rejilla(m)
    forma = (np.abs(Xo / A) ** 3 + np.abs((Y - Y0) / B) ** 3) <= 1
    tope = -0.255 + 0.05 * (Xo / A) ** 2
    forma &= Y >= tope
    t = np.clip((Y - tope) / 0.25, 0, 1)[..., None]
    escl = np.array([214, 204, 194]) * (1 - t) + np.array([246, 241, 233]) * t
    base = np.concatenate([escl, forma[..., None] * 255.0], -1)
    base[~forma, :3] = (240, 190, 150)

    # iris: se dibuja más grande que la abertura en vertical (el párpado lo recorta)
    iris_m = ((Xo - XI) / IRIS_W) ** 2 + ((Y - YI) / IRIS_H) ** 2 <= 1
    g = np.clip((Y - YI + 0.30) / 0.62, 0, 1)[..., None]
    col = np.array([34, 19, 12]) * (1 - g) + np.array([104, 60, 32]) * g
    pup = ((Xo - XI) / 0.11) ** 2 + ((Y - YI + 0.01) / 0.16) ** 2 <= 1
    col[pup] = (14, 8, 6)
    iris = np.concatenate([col, iris_m[..., None] * 255.0], -1)
    iris[~iris_m, :3] = col[~iris_m]                       # color sin halo al filtrar
    # brillo único: viaja con el iris (estilo ALTH), arriba hacia la izquierda de la imagen
    hx, hy = (XI * m["sale"] - 0.075), YI - 0.10
    brillo = np.maximum(np.abs(Xw - hx), np.abs(Y - hy)) <= 0.045
    iris[brillo] = (255, 255, 255, 255)

    enc = np.zeros(Xo.shape + (4,))
    linea = (Y - tope) <= PARPADO - 0.03 * (Xo / A) ** 2
    enc[linea] = (34, 21, 15, 255)
    return {k: np.clip(v5._reducir(x), 0, 255).round().astype(np.uint8) for k, x in (("base", base), ("iris", iris), ("encima", enc))}


def rango_uv(lado):
    """Desplazamiento máximo del iris en UV (mirada = ±1): x hasta el borde de la abertura, y la mitad."""
    m = v5.OJO[lado]
    du = (A - IRIS_W) * v5.ED / abs(m["ex"])
    dv = 0.08 * v5.ED / abs(m["ey"])
    return round(du, 4), round(dv, 4)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else AQUI
    for lado in ("L", "R"):
        for k, im in capas(lado).items():
            Image.fromarray(im).save(os.path.join(out, f"ojo_{lado}_{k}.png"), optimize=True)
        print(lado, "rango_uv", rango_uv(lado))
