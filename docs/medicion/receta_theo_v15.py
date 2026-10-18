"""Theo V15 (sobre Theo Alpha) / Adán V22 (--solo-estilo): boca para hablar.

Hallazgo: Talk-loop y Blink estaban vacíos y los 8 gestos de boca son expresiones, no sonidos.
Se agregan 8 morphs nuevos (visemas + mandíbula) hechos con los gestos existentes más campos de
deformación medidos en la boca de Alpha (abertura en v 0.44–0.55, |u| < 0.28; centro v 0.53):
  vis_A, vis_E, vis_I, vis_O, vis_U, vis_MBP, vis_FV y mandibula.
La mandíbula baja toda la cara inferior (barbilla incluida) con caída suave hacia mejillas y orejas, y
acompaña a A, E, O e I: hablar mueve la quijada, no solo los labios.
Clips: Talk-loop (6 s: frase de prueba con pausas, mandíbula y un parpadeo) y Blink (0.26 s).
Uso: python receta_theo_v15.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion import gestos  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, S = v5.ED, v5.YC, re._suave
PIEL, BOCA = v5.PIEL, v5.BOCA
V_BOCA = 0.53


def _uv(V):
    return V[:, 0] / ED, (YC - V[:, 1]) / ED


def zona_boca(V, ru=0.75, rv=0.25):
    u, v = _uv(V)
    return S(1 - np.sqrt((u / ru) ** 2 + ((v - V_BOCA) / rv) ** 2)) * S((V[:, 2] - 0.06) / 0.03)


def abajo(V):
    _, v = _uv(V)
    return S((v - V_BOCA) / 0.03)


def campo_mandibula(baja=0.10):
    def f(V):
        u, v = _uv(V)
        w = abajo(V) * S((1.15 - np.abs(u)) / 0.4) * S((V[:, 2] + 0.03) / 0.05)
        D = np.zeros_like(V)
        D[:, 1] = -baja * ED * w
        D[:, 2] = -0.25 * baja * ED * w
        return D
    return f


def campo_ancho(k):
    def f(V):
        D = np.zeros_like(V)
        D[:, 0] = (k - 1) * V[:, 0] * zona_boca(V)
        return D
    return f


def campo_adelante(a):
    def f(V):
        D = np.zeros_like(V)
        D[:, 2] = a * ED * zona_boca(V, 0.45, 0.18)
        return D
    return f


def campo_labio_inferior(a):
    def f(V):
        u, v = _uv(V)
        w = abajo(V) * S(1 - np.sqrt((u / 0.4) ** 2 + ((v - 0.6) / 0.1) ** 2)) * S((V[:, 2] - 0.08) / 0.02)
        D = np.zeros_like(V)
        D[:, 1] = a * ED * w
        D[:, 2] = -0.3 * a * ED * w
        return D
    return f


def suma(*campos):
    return lambda V: sum(c(V) for c in campos)


def elegible(p, V):
    """Piel de la cabeza y piezas de la boca (interior y fondos)."""
    return (len(V) > 10000 and V[:, 1].max() > 0.75) or (V[:, 1].max() < 0.62 and V[:, 1].min() > 0.5 and np.abs(V[:, 0]).max() < 0.11 and V[:, 2].min() > 0.08)


VISEMAS = {
    "mandibula": ({}, campo_mandibula(0.12)),
    "vis_A": ({"boca_abrir": 0.85}, campo_mandibula(0.09)),
    "vis_E": ({"boca_abrir": 0.35}, suma(campo_ancho(1.12), campo_mandibula(0.04))),
    "vis_I": ({"boca_abrir": 0.15, "boca_sonrisa": 0.25}, suma(campo_ancho(1.15), campo_mandibula(0.02))),
    # O y U con campos propios: boca_o (expresión) arruga el centro; aquí se estrecha y se abre redondo
    "vis_O": ({"boca_abrir": 0.85, "boca_triste": 0.35}, suma(campo_ancho(0.6), campo_adelante(0.05), campo_mandibula(0.05))),
    "vis_U": ({"boca_abrir": 0.3}, suma(campo_ancho(0.52), campo_adelante(0.09))),
    "vis_MBP": ({"boca_tensa": 0.7}, None),
    "vis_FV": ({"boca_tensa": 0.3}, campo_labio_inferior(0.04)),
}

# frase de prueba: sílabas encadenadas (0.24 s cada una) — "hola, me ves, no puedo"
SECUENCIA = ["vis_O", "vis_A", "vis_MBP", "vis_E", "vis_FV", "vis_E", "vis_I", "vis_O", "vis_U", "vis_E", "vis_MBP", "vis_A"]


def clips(E, duracion=6.0):
    paso = 0.2
    n = int(round(duracion / paso / len(SECUENCIA)))       # la frase se repite hasta cubrir el clip (6 s)
    sec = (SECUENCIA + ["vis_MBP", "vis_MBP", "vis_MBP"]) * max(n, 1)
    sec = sec[:int(duracion / paso)]
    t = np.arange(len(sec) + 1) * paso
    pesos = {k: np.zeros(len(t)) for k in VISEMAS}
    for i, s in enumerate(sec):
        pesos[s][i] = 0.85
    # pequeño rebote de mandíbula entre sílabas abiertas
    for i, s in enumerate(sec):
        if s in ("vis_A", "vis_O", "vis_E"):
            pesos["mandibula"][i] = 0.15
    # parpadeo a la mitad de la frase
    tt = np.sort(np.concatenate([t, [1.10, 1.16, 1.24]]))
    out = {k: np.interp(tt, t, v) for k, v in pesos.items()}
    out["parpado_L"] = np.interp(tt, [0, 1.08, 1.14, 1.20, 1.28, tt[-1]], [0, 0, 1, 1, 0, 0])
    out["parpado_R"] = out["parpado_L"]
    gestos.pista_pesos(E, "Talk-loop", tt, out)
    tb = np.array([0.0, 0.06, 0.12, 0.18, 0.26])
    gestos.pista_pesos(E, "Blink", tb, {"parpado_L": [0, 1, 1, 0.3, 0], "parpado_R": [0, 1, 1, 0.3, 0]})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    for nombre, (comb, campo) in VISEMAS.items():
        gestos.agregar_morph(E, nombre, comb, campo, elegible, suavizar=12, mascara=lambda V: zona_boca(V, 1.0, 0.45))
    gestos.rellenar_pesos(E)
    clips(E)
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V15" if identidad else "Adán V22") + ": boca para hablar (visemas, mandíbula, Talk-loop, Blink). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print({k: v for k, v in x.items() if k not in ("material", "combinacion")})
