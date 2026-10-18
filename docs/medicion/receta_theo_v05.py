"""Theo V05: likeness de cabeza y rostro, medido con CHXP + SENKU contra R_1, R_15 y R_0.

Parte de Theo V04 (V03 con caras orientadas). Unidad ED = 0.1348 u; v hacia abajo
desde la línea de ojos visible (y = 0.6252).
Uso: python receta_theo_v05.py ENTRADA SALIDA [--solo-estilo]   (--solo-estilo: Adán, sin rasgos de Theo)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402

ED, YC = 0.1348, 0.6252
y = lambda v: YC - v * ED  # noqa: E731
PIEL, BOCA = "PIEL_REFERENCIAS_THEO_ALASTOR_v04", "BOCA_INTERIOR_NEGRO"
es_cabeza = lambda V: len(V) > 10000 and V[:, 1].max() > 0.75  # noqa: E731
S = re._suave

# --- placas: mapeo UV → mundo (medido en V04) -----------------------------------
OJO = {"L": dict(x0=0.0157, ex=0.0907, y0=0.6659, ey=-0.079, cx=0.0615, sale=+1),
       "R": dict(x0=-0.1190, ex=0.0903, y0=0.6659, ey=-0.079, cx=-0.0733, sale=-1)}
CEJA = {"L": dict(x0=0.0138, ex=0.1011, y0=0.7116, ey=-0.0392, cx=0.0615, sale=+1),
        "R": dict(x0=-0.0279, ex=-0.1007, y0=0.7111, ey=-0.0392, cx=-0.0733, sale=-1)}
BAJAR_CEJA = 0.08  # ED


def _rejilla(m, tam=512, ss=3):
    """Coordenadas (Xo hacia afuera, Y hacia abajo) en ED respecto al centro del ojo, supermuestreadas."""
    n = tam * ss
    v, u = (np.mgrid[0:n, 0:n] + 0.5) / n
    x = m["x0"] + m["ex"] * u
    yy = m["y0"] + m["ey"] * v
    return (x - m["cx"]) / ED * m["sale"], (YC - yy) / ED, (x - m["cx"]) / ED


def _reducir(img, ss=3):
    H = img.shape[0] // ss
    return img.reshape(H, ss, H, ss, -1).mean((1, 3))


def textura_ojo(lado):
    m = OJO[lado]

    def f(_rgba):
        Xo, Y, Xw = _rejilla(m)
        a, b, Y0 = 0.325, 0.285, 0.005
        forma = (np.abs(Xo / a) ** 3 + np.abs((Y - Y0) / b) ** 3) <= 1
        tope = -0.255 + 0.05 * (Xo / a) ** 2
        forma &= Y >= tope
        col = np.zeros(Xo.shape + (3,))
        # esclerótica con sombra del párpado
        t = np.clip((Y - tope) / 0.25, 0, 1)
        col[:] = np.array([214, 204, 194]) * (1 - t[..., None]) + np.array([246, 241, 233]) * t[..., None]
        # iris alto y oscuro, un poco hacia la nariz
        xi, yi = -0.04, 0.025
        iris = ((Xo - xi) / 0.215) ** 2 + ((Y - yi) / 0.34) ** 2 <= 1
        g = np.clip((Y - yi + 0.30) / 0.62, 0, 1)[..., None]
        col[iris] = (np.array([34, 19, 12]) * (1 - g) + np.array([104, 60, 32]) * g)[iris]
        pup = ((Xo - xi) / 0.11) ** 2 + ((Y - yi + 0.01) / 0.16) ** 2 <= 1
        col[pup] = (14, 8, 6)
        # brillo único arriba, hacia la izquierda de la imagen (luz principal)
        hx, hy = (xi * m["sale"] - 0.075), yi - 0.10   # en coordenadas de mundo-imagen
        brillo = (np.maximum(np.abs(Xw - hx), np.abs(Y - hy)) <= 0.045)
        col[brillo] = (255, 255, 255)
        # línea gruesa del párpado superior
        grosor = 0.085 - 0.03 * (Xo / a) ** 2
        parpado = (Y - tope) <= grosor
        col[parpado] = (34, 21, 15)
        rgba = np.concatenate([col, forma[..., None] * 255.0], -1)
        rgba[~forma, :3] = (240, 190, 150)
        return np.clip(_reducir(rgba), 0, 255).round().astype(np.uint8)
    return f


def textura_ceja(lado, color=(88, 56, 32), extremos=(-0.25, 0.35), arriba=(-0.47, -0.50), abajo=(-0.30, -0.35)):
    """extremos: interno/externo en ED desde el centro del ojo; arriba/abajo: borde (interno, externo) en v."""
    m = CEJA[lado]

    def f(_rgba):
        Xo, Y, _ = _rejilla(m)
        Y = Y + BAJAR_CEJA                      # posición final tras bajar la placa
        i0, i1 = extremos
        t = np.clip((Xo - i0) / (i1 - i0), 0, 1)
        top = arriba[0] + (arriba[1] - arriba[0]) * t   # sube levemente hacia afuera
        bot = abajo[0] + (abajo[1] - abajo[0]) * t
        dentro = (Xo >= i0) & (Xo <= i1) & (Y >= top) & (Y <= bot)
        # chaflán externo inferior (corte low-poly)
        dentro &= ~((Xo > i1 - 0.08) & (Y > bot - (Xo - (i1 - 0.08)) * 0.9))
        col = np.zeros(Xo.shape + (3,)); col[:] = color
        col[dentro & (Y > bot - 0.035)] = np.array(color) * 0.78
        rgba = np.concatenate([col, dentro[..., None] * 255.0], -1)
        return np.clip(_reducir(rgba), 0, 255).round().astype(np.uint8)
    return f


def campo_nariz(V):
    w = (S((0.034 - np.abs(V[:, 0])) / 0.008) * S((V[:, 1] - y(0.40)) / 0.006) * S((y(0.0) - V[:, 1]) / 0.006)
         * S((V[:, 2] - 0.1455) / 0.004))
    V1 = V.copy()
    V1[:, 0] = V[:, 0] * (1 - 0.28 * w)
    zb = 0.1445
    V1[:, 2] = np.where(V[:, 2] > zb, zb + (V[:, 2] - zb) * (1 - 0.35 * w), V[:, 2])
    V1[:, 1] = V[:, 1] - 0.08 * ED * w
    J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = 1 - 0.28 * w; J[:, 2, 2] = 1 - 0.35 * w
    return V1, J


def campo_mejillas(V):
    """Angosta la cara baja (v 0.5 → 0.8) un 9 %, sin tocar orejas ni nuca."""
    w = S((y(0.5) - V[:, 1]) / (0.3 * ED)) * S((V[:, 2] + 0.06) / 0.05)
    f = 1 - 0.09 * w
    V1 = V.copy(); V1[:, 0] = V[:, 0] * f
    J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = f
    return V1, J


def campo_sonrisa(V):
    """Media sonrisa: sube la comisura izquierda de la imagen (lado derecho de Theo)."""
    def bump(cx, cy, r):
        d = np.sqrt(((V[:, 0] - cx) / r) ** 2 + ((V[:, 1] - cy) / (0.6 * r)) ** 2)
        return S(1 - d)
    yb = y(0.63)
    dy = 0.06 * ED * bump(-0.075, yb, 0.035) - 0.015 * ED * bump(0.07, yb, 0.03)
    V1 = V.copy(); V1[:, 1] = V[:, 1] + dy
    return V1, np.tile(np.eye(3), (len(V), 1, 1))


def campo_ocultar_parpado_viejo(V):
    """La línea de párpado en geometría queda dentro de la cabeza (la textura nueva ya la dibuja)."""
    c = V.mean(0) + np.array([0, 0, -0.035])
    V1 = c + (V - V.mean(0)) * 0.02
    return V1, np.tile(np.eye(3) * 0.02, (len(V), 1, 1))


def peso_cara_baja(V):
    """Suavizado de pliegues y papada (v 0.35 → 1.0, frente de la cara); protege la línea de la boca."""
    yb = y(0.63)
    w = (S((y(0.35) - V[:, 1]) / (0.1 * ED)) * S((V[:, 1] - y(1.05)) / (0.1 * ED))
         * S((1.1 * ED - np.abs(V[:, 0])) / (0.2 * ED)) * S((V[:, 2] - 0.0) / 0.04))
    linea = (np.abs(V[:, 1] - yb) < 0.05 * ED) & (np.abs(V[:, 0]) < 0.6 * ED) & (V[:, 2] > 0.09)
    return np.where(linea, 0.0, w)


def main(src, dst, identidad=True):
    """identidad=False aplica solo el canon de estilo (ojos, cejas, nariz, párpado): sirve para Adán."""
    E = re.Editor(src)
    for lado in ("L", "R"):
        E.textura(f"C7V2_eye_BAKE_{lado}", textura_ojo(lado), f"ojo {lado}: forma ancha, iris alto oscuro, brillo único, párpado grueso")
        E.textura(f"C7V2_brow_BAKE_{lado}", textura_ceja(lado), f"ceja {lado}: barra inclinada (interna baja), extremos -0.25/+0.35 ED")
        E.deformar(f"C7V2_brow_BAKE_{lado}", re.campo_rigido(1, 1, (0, 0, 0), (0, -BAJAR_CEJA * ED, 0)), f"placa ceja {lado}: baja 0.08 ED")
    E.deformar(PIEL, campo_nariz, "nariz: ancho x0.72, saliente x0.65, baja 0.08 ED", primitiva=es_cabeza)
    if identidad:  # rasgos de Theo
        E.deformar(PIEL, campo_mejillas, "cara baja: -9 % de ancho (v 0.5→0.8)", primitiva=es_cabeza)
        E.deformar(BOCA, campo_mejillas, "boca interior: sigue a la cara baja")
        E.deformar(PIEL, campo_sonrisa, "media sonrisa (comisura izquierda de la imagen +0.06 ED)", primitiva=es_cabeza)
        E.deformar(BOCA, campo_sonrisa, "media sonrisa (boca interior)")
    E.deformar("LINEA_PARPADO_CAFE", campo_ocultar_parpado_viejo, "línea de párpado vieja: escondida dentro de la cabeza")
    if identidad:
        re.suavizar_region(E, PIEL, peso_cara_baja, iteraciones=12, primitiva=es_cabeza, nombre="suavizado cara baja (pliegues)")
    tmp = dst + ".tmp"
    nota = ("Theo V05: likeness de cabeza y rostro (CHXP + SENKU). SIN APROBAR." if identidad else
            "Adán V12: canon de estilo de rostro ALTH (ojos, cejas, nariz) desde la receta de Theo V05. SIN APROBAR.")
    E.guardar(tmp, nota=nota)
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
