"""Adán V31 (sobre V22 HABLA → V30 aprobada): brazos más cortos — rediseño del cuerpo, paso 1 (esqueleto).

Decisiones de Admin (18 oct 2026): con los brazos abajo la mano llega a la entrepierna; brazo y antebrazo casi
iguales (chibi). Medido con SENKU (copox/medicion/cuerpo.py, en alturas de barbilla Hc) contra la Hoja de vistas:
  hombro → muñeca 0.452 Hc (hoja 0.324); antebrazo 0.136 u contra brazo 0.086 u (1.6 veces más largo).
Arreglo: solo el antebrazo se acorta a lo largo de su eje (0.136 → 0.078 u). La mano y los dedos se trasladan
rígidos (no cambian de tamaño ni de forma); los vértices del antebrazo se escalan en x con pivote en el codo. En la
muñeca las dos cosas coinciden, así que la unión no se abre. Rotaciones de los clips, morphs y pesos intactos;
inverseBindMatrices y traslaciones de los nodos se recalculan (copox/medicion/proporciones.py).
Uso: python receta_adan_v31.py ADAN_V22_HABLA.glb ADAN_V31.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import proporciones  # noqa: E402
from copox.medicion.gltf import leer_glb  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v30 as v30  # noqa: E402
import receta_adan_v27 as v27  # noqa: E402
from copox.medicion import rostro_edicion as re  # noqa: E402

ANTEBRAZO = 0.078          # u (antes 0.1356); brazo de arriba 0.0857 → razón 1.10


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
        codo, mun = mundo(idx[lado + "LowerArm"]), mundo(idx[lado + "Hand"])
        d = mun - codo; L = np.linalg.norm(d); u = d / L
        assert abs(abs(u[0]) - 1) < 1e-6, "el antebrazo en reposo debe ir sobre x (pose T)"
        f = ANTEBRAZO / L
        ed.append({"tipo": "mover", "huesos": lado + "Hand", "delta": (u * (ANTEBRAZO - L)).tolist()})
        ed.append({"tipo": "escala_vertices", "huesos": lado + "LowerArm", "factores": [f, 1.0, 1.0], "pivote": codo.tolist()})
    return ed


def main(src, dst):
    t30 = dst + ".v30.glb"
    v30.main(src, t30)
    tmp = dst + ".tmp.glb"
    tmp2 = dst + ".tmp2.glb"
    r = proporciones.editar(t30, tmp, ediciones(t30), nota="Adán V31: antebrazo 0.136 → 0.078 u (mano rígida). SIN APROBAR.")
    # pesos por cadena otra vez sobre el brazo nuevo: con el antebrazo comprimido la rampa del codo quedaba
    # más corta y el codo estiraba más (SENKU uniones: 6 clips > ×3)
    E = re.Editor(tmp)
    r["repesado"] = v27.repesar(E)
    E.guardar(tmp2, nota="Adán V31: brazos más cortos (antebrazo 0.078 u), pesos por cadena rehechos. SIN APROBAR.")
    compactar(tmp2, dst)
    os.remove(tmp); os.remove(tmp2); os.remove(t30)
    return r


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2]))
