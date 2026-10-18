"""Theo V07 (sobre V06): pómulos y orejas (pedido de Admin: «pómulos muy marcados, orejas sumidas»).

Medido con CHXP + SENKU (contorno de piel por altura contra R_15, R_1 y R_0):
- Costados del cráneo y pómulos: la cabeza era más ancha a media altura (|u| 1.28 ED en
  v −0.2…0.6) que arriba y abajo; las referencias tienen costados casi rectos. Lo que pasa de
  |u| 0.95 se comprime hasta un ancho máximo de ≈1.12 ED en esa franja.
- Pómulos de frente: el bulto bajo los ojos se acerca a una superficie suave ajustada.
- Orejas: quedan donde estaban por fuera (|u| ≈ 1.45) y se alargan hacia adentro para no
  despegarse: sobresalen ≈0.33 ED en vez de ≈0.17. Panel interior más oscuro (como la Hoja).
- Mandíbula un poco más cuadrada (v 0.85–1.0, ×1.08 de ancho).
Uso: python receta_theo_v07.py ENTRADA SALIDA [--solo-estilo]
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
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")


def banda(V, v0=-0.2, v1=0.6, r0=0.3, r1=0.25):
    """1 dentro de v0…v1 (ED), rampa suave de r0/r1 ED afuera."""
    v = (YC - V[:, 1]) / ED
    return S((v - (v0 - r0)) / r0) * S(((v1 + r1) - v) / r1)


def campo_costados(a=0.95, ancho=1.12, max_actual=1.28):
    k = (ancho - a) / (max_actual - a)
    a_u = a * ED

    def f(V):
        w = banda(V)
        ax = np.abs(V[:, 0])
        kk = 1 - (1 - k) * w
        V1 = V.copy()
        V1[:, 0] = np.where(ax > a_u, np.sign(V[:, 0]) * (a_u + (ax - a_u) * kk), V[:, 0])
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = np.where(ax > a_u, kk, 1.0)
        return V1, J
    return f


def peso_pomulos(V):
    """Mejillas y esquinas de la mandíbula (v 0.05–0.95, |u| 0.35–1.2), sin boca ni nariz."""
    v = (YC - V[:, 1]) / ED
    u = np.abs(V[:, 0]) / ED
    w = S((v - 0.05) / 0.12) * S((0.95 - v) / 0.1) * S((u - 0.35) / 0.12) * S((1.2 - u) / 0.12) * S((V[:, 2] - 0.06) / 0.03)
    boca = S(1 - np.sqrt((V[:, 0] / (0.45 * ED)) ** 2 + ((v - 0.58) / 0.1) ** 2))
    return w * (1 - boca)


def campo_pomulos(V):
    """Acerca el frente de las mejillas a una cuadrática ajustada en una zona más amplia (quita el bulto)."""
    v = (YC - V[:, 1]) / ED
    u = np.abs(V[:, 0]) / ED
    ajuste = (v > 0.0) & (v < 1.0) & (u > 0.3) & (u < 1.25) & (V[:, 2] > 0.06)
    A = lambda X, Y: np.c_[np.ones(len(X)), X ** 2, Y, Y ** 2, X ** 2 * Y, X ** 4, Y ** 3]  # noqa: E731
    c, *_ = np.linalg.lstsq(A(V[ajuste, 0], V[ajuste, 1]), V[ajuste, 2], rcond=None)
    z = A(V[:, 0], V[:, 1]) @ c
    w = peso_pomulos(V)
    V1 = V.copy(); V1[:, 2] = V[:, 2] + (z - V[:, 2]) * 0.9 * w  # bultos y surcos hacia la superficie suave
    return V1, np.tile(np.eye(3), (len(V), 1, 1))


def campo_mandibula(V):
    v = (YC - V[:, 1]) / ED
    w = S((v - 0.80) / 0.1) * S((1.08 - v) / 0.05) * S((V[:, 2] + 0.04) / 0.04)
    f = 1 + 0.08 * w
    V1 = V.copy(); V1[:, 0] = V[:, 0] * f
    J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = f
    return V1, J


def campo_oreja(adentro=1.02 * ED):
    """Mantiene la cara externa de la oreja y estira la interna hasta |x| = adentro (queda pegada al cráneo)."""
    def f(V):
        ax = np.abs(V[:, 0])
        ext, inn = ax.max(), ax.min()
        k = (ext - adentro) / (ext - inn)
        V1 = V.copy(); V1[:, 0] = np.sign(V[:, 0]) * (ext - (ext - ax) * k)
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = k
        return V1, J
    return f


def panel_oreja(E):
    """Panel interior de la oreja: caja delgada más oscura sobre la cara externa (como la Hoja)."""
    for lado in (-1, 1):
        x_ext = lado * 0.1952
        re.agregar_caja(E, "ADAN_CUERPO", PIEL, (x_ext + lado * 0.0006, 0.607, -0.028), (0.0012, 0.020, 0.0125), "Head", bisel=0.05)
        p = E.j["meshes"][next(n for n in E.j["nodes"] if n.get("name") == "ADAN_CUERPO")["mesh"]]["primitives"][-1]
        n = E.j["accessors"][p["attributes"]["POSITION"]]["count"]
        p["attributes"]["COLOR_0"] = E._add(np.tile([0.93, 0.70, 0.66, 1.0], (n, 1)), "VEC4", 34962)
        E.b = bytes(E.out)
    E.log.append({"operacion": "orejas: panel interior más oscuro (COLOR_0)", "material": PIEL})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    E.deformar(PIEL, campo_costados(), "costados del cráneo/pómulos: ancho máx. 1.28 → 1.12 ED (v −0.2…0.6)", primitiva=es_cabeza)
    for mat in PELO:
        E.deformar(mat, campo_costados(), "gorro de pelo: sigue a los costados")
    E.deformar(PIEL, campo_pomulos, "pómulos de frente: bulto aplanado", primitiva=es_cabeza)
    re.suavizar_region(E, PIEL, peso_pomulos, iteraciones=40, lam=0.5, mu=0.0, primitiva=es_cabeza,
                       nombre="pómulos y esquinas de mandíbula: suavizado laplaciano (quita bultos)")
    if identidad:
        E.deformar(PIEL, campo_mandibula, "mandíbula: x1.08 en v 0.85–1.0", primitiva=es_cabeza)
    E.deformar(PIEL, campo_oreja(), "orejas: cara interna hasta |u| 1.02 (pegadas al cráneo, sobresalen ≈0.33 ED)", primitiva=es_oreja)
    panel_oreja(E)
    E.recalcular_normales(PIEL, lambda V: es_cabeza(V) or es_oreja(V), "normales recalculadas: cabeza y orejas")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V07" if identidad else "Adán V14") + ": pómulos y orejas (CHXP + SENKU). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
