"""Theo V12 (sobre V11) / Adán V19 (--solo-estilo): sin partes sumidas.

Ahora nariz, cejas, ojos y orejas son piezas aparte; la piel de la cabeza ya no necesita relieve
propio salvo la abertura de la boca. Dos pasadas sobre toda la piel de la cabeza (malla soldada):
1. Rellenar hundidos: el laplaciano solo se aplica cuando apunta hacia afuera (el vértice está por
   debajo de sus vecinos), así se llenan las cuencas sin rebajar los bultos.
2. Taubin suave en toda la piel para unir.
Protegidos: bordes abiertos y la zona de la boca (abertura, labios y comisuras).
Se mide el % de vértices cóncavos (curvatura < −umbral) antes y después.
Uso: python receta_theo_v12.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, S = v5.ED, v5.YC, re._suave
PIEL = v5.PIEL
es_cabeza = v5.es_cabeza


def _malla(E, p, V):
    F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True); w = w.ravel()
    nw = w.max() + 1; Fw = w[F]
    P = np.zeros((nw, 3)); np.add.at(P, w, V); P /= np.bincount(w, minlength=nw)[:, None]
    E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]])
    E2 = np.unique(np.concatenate([E2, E2[:, ::-1]]), axis=0)
    cnt = np.bincount(E2[:, 0], minlength=nw)
    k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
    u, c = np.unique(k, axis=0, return_counts=True)
    borde = np.zeros(nw, bool); borde[u[c == 1].ravel()] = True
    return w, Fw, P, E2, cnt, borde


def _normales(P, Fw):
    T = P[Fw]; Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    N = np.zeros_like(P)
    for i in range(3):
        np.add.at(N, Fw[:, i], Nf)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def _lap(P, E2, cnt):
    s = np.zeros_like(P); np.add.at(s, E2[:, 0], P[E2[:, 1]])
    return s / np.maximum(cnt, 1)[:, None] - P


def concavos(P, Fw, E2, cnt, umbral=0.04):
    N = _normales(P, Fw)
    L = _lap(P, E2, cnt)
    le = np.linalg.norm(P[E2[:, 0]] - P[E2[:, 1]], axis=1)
    lm = np.bincount(E2[:, 0], weights=le, minlength=len(P)) / np.maximum(cnt, 1)
    h = (L * N).sum(1) / np.maximum(lm, 1e-9)        # > 0: el vértice está hundido respecto a sus vecinos
    return h > umbral


def sin_hundidos(E, it_relleno=40, it_taubin=10):
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        w, Fw, P0, E2, cnt, borde = _malla(E, p, V)
        v = (YC - P0[:, 1]) / ED
        u = P0[:, 0] / ED
        boca = S(1 - np.sqrt((u / 0.62) ** 2 + ((v - 0.59) / 0.14) ** 2)) * (P0[:, 2] > 0.08)
        libre = np.where(borde, 0.0, 1 - boca)[:, None]
        antes = concavos(P0, Fw, E2, cnt)
        P = P0.copy()
        for _ in range(it_relleno):
            N = _normales(P, Fw)
            L = _lap(P, E2, cnt)
            hacia_afuera = np.maximum((L * N).sum(1), 0)[:, None] * N      # solo la parte que llena el hundido
            P += 0.5 * libre * hacia_afuera
        for _ in range(it_taubin):
            for f in (0.5, -0.53):
                P += f * libre * _lap(P, E2, cnt)
        despues = concavos(P, Fw, E2, cnt)
        fuera = (boca < 0.5)
        E.escribir(p, V + (P - P0)[w], T)
        E.log.append({"operacion": "piel sin hundidos (relleno de cuencas + Taubin), boca y bordes protegidos",
                      "material": PIEL,
                      "concavos_%_fuera_de_boca": [round(100 * float(antes[fuera].mean()), 1), round(100 * float(despues[fuera].mean()), 1)],
                      "desplazamiento_max_mm": round(float(np.abs(P - P0).max() * 1000), 2)})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    sin_hundidos(E)
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V12" if identidad else "Adán V19") + ": sin partes sumidas. SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print({k: v for k, v in x.items() if k != "material"})
