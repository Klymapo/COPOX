"""Theo V06 (sobre V05) y Adán V13 (sobre V12, con --solo-estilo): segunda pasada de cabeza y rostro.

Medido con CHXP + SENKU contra R_15, R_1 y el acercamiento de la Hoja (R_closeup):
- cejas: se probaron más gruesas/largas y bajaron el IoU de rasgos (0.453 → 0.441); se quedan las de V05;
- boca 0.05 ED más arriba y ×1.12 de ancho (Theo);
- costados de la cabeza: se probó angostarlos (×0.92 y ×0.82 más allá de |u| 0.85 ED) y el IoU de piel de la
  cara baja bajó (0.738 → 0.730 → 0.718); se dejan como en V05 (campo_costados queda para pruebas);
- boca más arriba y ancha con sonrisa de lado; cara baja aplanada (sin papada); fondo negro de la boca;
- rubor en mejillas y nariz un poco más rosada (COLOR_0);
- normales recalculadas: las ediciones V09–V12 dejaban normales viejas en la cara (Godot las usa).
Uso: python receta_theo_v06.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, y, S = v5.ED, v5.YC, v5.y, re._suave
PIEL, BOCA = v5.PIEL, v5.BOCA
es_cabeza = v5.es_cabeza
es_oreja = lambda V: len(V) == 84 and V[:, 1].min() > 0.5  # noqa: E731
cabeza_u_oreja = lambda V: es_cabeza(V) or es_oreja(V)  # noqa: E731
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")


def campo_costados(a=0.85, s=0.82):
    a_u = a * ED

    def f(V):
        ax = np.abs(V[:, 0])
        w = S((V[:, 1] - 0.50) / 0.02)                  # solo cabeza (sobre el cuello)
        fuera = np.maximum(ax - a_u, 0)
        k = 1 - (1 - s) * w
        V1 = V.copy(); V1[:, 0] = np.sign(V[:, 0]) * (np.minimum(ax, a_u) + fuera * k)
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = np.where(ax > a_u, k, 1.0)
        return V1, J
    return f


def color_rubor(V):
    C = np.ones((len(V), 3))
    frente = S((V[:, 2] - 0.06) / 0.04)
    for lado in (-1, 1):
        d = ((V[:, 0] - lado * 0.85 * ED) / (0.38 * ED)) ** 2 + ((V[:, 1] - y(0.40)) / (0.22 * ED)) ** 2
        w = np.exp(-d * 1.6) * frente
        C *= 1 - w[:, None] * np.array([0.0, 0.15, 0.11])
    nariz = (S((0.03 - np.abs(V[:, 0])) / 0.008) * S((V[:, 1] - y(0.45)) / 0.006) * S((y(0.08) - V[:, 1]) / 0.006)
             * S((V[:, 2] - 0.148) / 0.004))
    C *= 1 - nariz[:, None] * np.array([0.0, 0.07, 0.07])
    return C


def campo_sonrisa(V):
    """Sonrisa de lado: sube ambas comisuras, más la izquierda de la imagen (lado derecho de Theo)."""
    yb = y(0.58)

    def bump(cx, r):
        # caída vertical amplia: ambos labios suben juntos (no se abre la boca)
        d = np.sqrt(((V[:, 0] - cx) / r) ** 2 + ((V[:, 1] - yb) / 0.035) ** 2)
        return S(1 - d)
    # la abertura visible de la boca termina en |x| ≈ 0.036 (el interior negro es más ancho)
    dy = 0.08 * ED * bump(-0.034, 0.022) + 0.04 * ED * bump(0.034, 0.02)
    V1 = V.copy(); V1[:, 1] = V[:, 1] + dy
    return V1, np.tile(np.eye(3), (len(V), 1, 1))


def campo_mover_boca(V):
    """Sube 0.05 ED y ensancha x1.12 la zona de la boca con caída amplia en vertical:
    labios e interior se mueven igual, la abertura no cambia."""
    yb = y(0.63)
    w = S(1 - np.abs(V[:, 0]) / 0.075) * S(1 - np.abs(V[:, 1] - yb) / 0.035)
    V1 = V.copy()
    V1[:, 0] = V[:, 0] * (1 + 0.12 * w)
    V1[:, 1] = V[:, 1] + 0.05 * ED * w
    J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = 1 + 0.12 * w
    return V1, J


def campo_caja_boca(V, lo=(-0.095, 0.52, 0.098), hi=(0.095, 0.57, 0.1245)):
    """Reubica el interior de la boca en una caja fija detrás de los labios (afín por eje)."""
    a, b = V.min(0), V.max(0)
    lo, hi = np.array(lo), np.array(hi)
    k = (hi - lo) / np.maximum(b - a, 1e-9)
    return lo + (V - a) * k, np.tile(np.diag(k), (len(V), 1, 1))


def peso_cara_baja(V):
    yb = y(0.58)
    w = (S((y(0.38) - V[:, 1]) / (0.12 * ED)) * S((V[:, 1] - y(1.02)) / (0.08 * ED))
         * S((1.0 * ED - np.abs(V[:, 0])) / (0.25 * ED)) * S((V[:, 2] - 0.06) / 0.03))
    boca = S(1 - np.sqrt((V[:, 0] / (0.42 * ED)) ** 2 + ((V[:, 1] - yb) / (0.09 * ED)) ** 2)) 
    nariz = S((0.045 - np.abs(V[:, 0])) / 0.01) * S((V[:, 1] - y(0.48)) / 0.006)
    return w * (1 - boca) * (1 - nariz)


def campo_aplanar_cara_baja(V):
    """Quita papada y pliegues: acerca el frente de la cara baja a una superficie cuadrática ajustada."""
    w = peso_cara_baja(V)
    m = w > 0.3
    X, Yv = V[m, 0], V[m, 1]
    A = np.c_[np.ones(m.sum()), X, Yv, X * X, X * Yv, Yv * Yv]
    c, *_ = np.linalg.lstsq(A, V[m, 2], rcond=None)
    Af = np.c_[np.ones(len(V)), V[:, 0], V[:, 1], V[:, 0] ** 2, V[:, 0] * V[:, 1], V[:, 1] ** 2]
    z = Af @ c
    V1 = V.copy(); V1[:, 2] = V[:, 2] + (z - V[:, 2]) * 0.8 * w
    return V1, np.tile(np.eye(3), (len(V), 1, 1))


def main(src, dst, identidad=True):
    E = re.Editor(src)
    if identidad:
        E.deformar(PIEL, campo_mover_boca, "boca: +0.05 ED arriba, x1.12 ancho (labios juntos)", primitiva=es_cabeza)
        E.deformar(BOCA, campo_mover_boca, "boca interior: mismo campo")
        E.deformar(PIEL, campo_sonrisa, "sonrisa de lado: comisuras +0.08 (izq. imagen) y +0.04 ED", primitiva=es_cabeza)
        E.deformar(BOCA, campo_sonrisa, "sonrisa de lado (boca interior)")
        re.agregar_caja(E, "ADAN_CUERPO", BOCA, (0, 0.549, 0.105), (0.07, 0.017, 0.008), "Head")
        E.log.append({"operacion": "fondo negro de la boca (caja detrás de los labios)", "material": BOCA})
        E.deformar(PIEL, campo_aplanar_cara_baja, "cara baja: aplanada hacia superficie suave (sin papada)", primitiva=es_cabeza)
        re.suavizar_region(E, PIEL, peso_cara_baja, iteraciones=10, primitiva=es_cabeza, nombre="suavizado cara baja")
    E.color_vertices(PIEL, color_rubor, "rubor en mejillas y nariz rosada (COLOR_0)", primitiva=es_cabeza)
    # el interior de la boca se ve por la abertura desde cualquier ángulo: material de dos caras
    # el gorro de pelo es una cáscara abierta: de lado se ve su cara interior (también en Godot)
    for nombre in (BOCA,) + PELO:
        next(m for m in E.j["materials"] if m["name"] == nombre)["doubleSided"] = True
        E.log.append({"operacion": f"{nombre}: doubleSided (sin huecos al verlo de lado)", "material": nombre})
    for mat, prim in ((PIEL, cabeza_u_oreja), (BOCA, None)):
        E.recalcular_normales(mat, prim, f"normales recalculadas: {mat}")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V06" if identidad else "Adán V13") + ": segunda pasada de cabeza y rostro (CHXP + SENKU). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
