"""Theo V14 (sobre V13) / Adán V21 (--solo-estilo): gestos revisados.

Revisión de los 18 gestos con CHXP (y en Godot 4.7.2): el único roto es el parpadeo
(parpado_L/R): el párpado cerrado quedaba detrás de la placa del ojo, que ahora está apoyada más
adelante, y se veía un aro blanco. Al morph de parpadeo se le suma lo necesario para que el párpado
cerrado quede 1 mm delante de la placa (ponderado por cuánto se mueve cada vértice: el párpado
abierto no cambia), y la placa del ojo se encoge al 80 % y se mete 3 mm al cerrar (sus
bordes ya no asoman; a medio parpadeo el ojo se ve normal).
Uso: python receta_theo_v14.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

PIEL = v5.PIEL
OJOS = ("C7V2_eye_BAKE_L", "C7V2_eye_BAKE_R")


ESCALA_PLACA = 0.8   # la placa se encoge al 80 % (hacia su centro) y se mete 3 mm al cerrar


def z_placa(E, mat, x, y):
    P = np.concatenate([E.leer(p)[0] for p in E.prims(mat)])
    out = np.empty(len(x))
    for i in range(0, len(x), 2000):
        d2 = (x[i:i + 2000, None] - P[None, :, 0]) ** 2 + (y[i:i + 2000, None] - P[None, :, 1]) ** 2
        idx = np.argsort(d2, 1)[:, :6]
        w = 1 / (np.take_along_axis(d2, idx, 1) + 1e-12)
        out[i:i + 2000] = (P[idx, 2] * w).sum(1) / w.sum(1)
    return out


def parpadeo_delante(E, delante=0.001):
    nombres = E.j["meshes"][0]["extras"]["targetNames"]
    n = 0
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not (len(V) == 1377 and V[:, 1].min() > 0.55):
            continue
        mat = OJOS[0] if V[:, 0].mean() > 0 else OJOS[1]
        lado = "L" if mat.endswith("L") else "R"
        k = nombres.index(f"parpado_{lado}")
        D = T[k].copy()
        cerrado = V + D
        zp = z_placa(E, mat, cerrado[:, 0], cerrado[:, 1])
        mueve = np.clip(np.linalg.norm(D, axis=1) / 0.004, 0, 1)
        falta = np.maximum(zp + delante - cerrado[:, 2], 0) * mueve
        D[:, 2] += falta
        T[k] = D
        E.escribir(p, V, T)
        n += int((falta > 0).sum())
        # la placa del ojo se pliega detrás del párpado al cerrar (si no, sus bordes asoman como aro blanco)
        for q in E.prims(mat):
            Q, TQ = E.leer(q)
            c = (Q.min(0) + Q.max(0)) / 2
            Dq = np.zeros_like(Q)
            Dq[:, :2] = (c[:2] - Q[:, :2]) * (1 - ESCALA_PLACA)
            Dq[:, 2] = -0.003
            TQ[k] = Dq
            E.escribir(q, Q, TQ)
    E.log.append({"operacion": "parpadeo: párpado 1 mm delante de la placa; la placa se pliega detrás al cerrar", "material": PIEL, "vertices": n})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    parpadeo_delante(E)
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V14" if identidad else "Adán V21") + ": gestos revisados (parpadeo). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print({k: v for k, v in x.items() if k != "material"})
