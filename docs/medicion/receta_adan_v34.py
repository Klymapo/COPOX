"""Adán V34 (sobre V22 HABLA → V33): manos, segunda ronda — proporciones contra la mano con regla.

SENKU (copox/medicion/mano.py) contra refs/infografias/mano-con-regla.jpg (razones, sin unidades):
  ancho/largo de la palma 1.85 (ref 1.06): palma corta y ancha · meñique/medio 0.49 (ref 0.62)
  dedos, anchos de dedo, índice y anular: ya en rango.
Decisión chibi: no se copia la mano realista; se acerca a medio camino (la hoja trae puños gruesos).
Arreglo (copox/medicion/proporciones.py: huesos, vértices, inverseBindMatrices; rotaciones de clips intactas):
  1) Palma +30 % de largo (de la muñeca a los nudillos): los vértices de la mano se estiran en x con pivote en la
     muñeca; los cuatro dedos se trasladan rígidos al nuevo borde; el pulgar se traslada lo que se estiró su base.
  2) Dedos más largos a lo largo de su eje (desde el nudillo): medio ×1.17 e índice/anular/meñique según sus
     razones con el medio en la referencia. El grosor no cambia.
  3) Pesos por cadena rehechos (receta V27) sobre la mano nueva.
Uso: python receta_adan_v34.py ADAN_V22_HABLA.glb ADAN_V34.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import proporciones  # noqa: E402
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import leer_glb  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v33 as v33  # noqa: E402
import receta_adan_v27 as v27  # noqa: E402

PALMA = 1.30
DEDOS = {"Index": 1.23, "Middle": 1.17, "Ring": 1.26, "Little": 1.30}


def ediciones(glb):
    j, _ = leer_glb(glb)
    idx = {n.get("name"): i for i, n in enumerate(j["nodes"])}
    padre = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}

    def mundo(i):
        p = np.zeros(3)
        while i is not None:
            p += np.array(j["nodes"][i].get("translation", [0, 0, 0]), float); i = padre.get(i)
        return p
    ed = []
    for lado in ("Left", "Right"):
        W = mundo(idx[lado + "Hand"])
        s = np.sign(W[0])
        nudillos = np.mean([mundo(idx[lado + d + "Proximal"])[0] for d in DEDOS])
        L = abs(nudillos - W[0])
        for d, f in DEDOS.items():
            px = mundo(idx[lado + d + "Proximal"])
            ed.append({"tipo": "mover", "huesos": lado + d + "Proximal", "delta": [float((PALMA - 1) * (px[0] - W[0])), 0.0, 0.0]})
        tb = mundo(idx[lado + "ThumbMetacarpal"])
        ed.append({"tipo": "mover", "huesos": lado + "ThumbMetacarpal", "delta": [float((PALMA - 1) * (tb[0] - W[0])), 0.0, 0.0]})
        ed.append({"tipo": "escala_vertices", "huesos": lado + "Hand", "factores": [PALMA, 1.0, 1.0], "pivote": W.tolist()})
        for d, f in DEDOS.items():
            ed.append({"tipo": "escala_eje", "raiz": lado + d + "Proximal", "hacia": lado + d + "Distal", "factor": f})
        del s, L
    return ed


def main(src, dst):
    t33 = dst + ".v33.glb"
    v33.main(src, t33)
    tmp, tmp2 = dst + ".tmp.glb", dst + ".tmp2.glb"
    r = proporciones.editar(t33, tmp, ediciones(t33), nota="Adán V34: palma ×1.30 de largo, dedos más largos. SIN APROBAR.")
    E = re.Editor(tmp)
    r["repesado"] = v27.repesar(E)
    E.guardar(tmp2, nota="Adán V34: V33 + manos (palma más larga, dedos más largos, pesos por cadena). SIN APROBAR.")
    compactar(tmp2, dst)
    os.remove(tmp); os.remove(tmp2); os.remove(t33)
    return r


if __name__ == "__main__":
    r = main(sys.argv[1], sys.argv[2]); r.pop("huesos_movidos", None); print(r)
