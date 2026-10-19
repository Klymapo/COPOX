"""Pelo de Theo como pieza intercambiable (CAPA_PELO_THEO) sobre Adán V49.

Admin (19 oct 2026): "Trabajemos más en el pelo. Intenta replicar el de Theo." Referencia:
refs/personajes/joven-rubio-4-vistas.jpg. Lo que se lee en la hoja:
- volumen grande arriba (sube ~1/4 de la cabeza sobre el cráneo) y más ancho que la cabeza;
- raya al centro con un pico en "M" sobre la frente; la frente queda libre al centro;
- dos mechones largos al frente que enmarcan la cara y bajan por las sienes hasta la mejilla;
- arriba, mechones gruesos que barren hacia atrás; atrás, mechones verticales que bajan a la nuca;
- facetas planas grandes (low-poly), rubio arena.
Técnica: cáscara de V48.3 inflada (volumen por elevación) + mechones (pelo_mechones) con sombreado facetado.
Uso: GODOT_BIN=… [ALTH_CALIDAD=borrador] python pelo_theo.py ADAN_V49.glb ADAN_V47.glb SALIDA.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v41 as v41  # noqa: E402
import receta_adan_v48_2 as v482  # noqa: E402
import receta_adan_v48_3 as v483  # noqa: E402
import receta_adan_v49 as v49  # noqa: E402

COLOR = "#D2AE72"                 # medidos/rubio_arena
VOLUMEN = dict(corona=0.020, lados=0.004, el0=10.0, el1=70.0)
TRIS_BASE = 500                   # base del cráneo: pocas caras grandes
ESCALA = 1.55
AFILAR = 0.55
# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm, despega_m); az 0 = frente, +90 = su izquierda (+x)
MECHONES_THEO = [
    # pico en "M" sobre la frente (raya al centro), despegados de la frente
    (-8, 78, -28, 46, 50, 20, 0.010, -15), (8, 78, 28, 46, 50, 20, 0.010, 15),
    # mechones largos que enmarcan la cara: bajan por las sienes hasta la mejilla
    (-26, 70, -58, -14, 52, 18, 0.016), (26, 70, 58, -14, 52, 18, 0.016),
    (-44, 66, -74, 0, 56, 20, 0.012), (44, 66, 74, 0, 56, 20, 0.012),
    # copete: nacen arriba de la frente y suben hacia atrás (picos con altura)
    (-22, 66, -60, 92, 70, 28, 0.036), (22, 66, 60, 92, 70, 28, 0.036), (0, 70, 0, 96, 66, 28, 0.042),
    # arriba-atrás: barren hacia la coronilla y se levantan
    (-70, 66, -130, 84, 80, 26, 0.028, 10), (70, 66, 130, 84, 80, 26, 0.028, -10),
    # lados sobre la oreja
    (-84, 58, -102, 8, 66, 20, 0.006), (84, 58, 102, 8, 66, 20, 0.006),
    # atrás: bloques verticales hacia la nuca
    (-156, 64, -160, -34, 84, 22, 0.008), (-118, 60, -132, -24, 78, 20, 0.008), (156, 64, 160, -34, 84, 22, 0.008),
    (118, 60, 132, -24, 78, 20, 0.008), (180, 66, 180, -36, 84, 22, 0.008),
    # coronilla: dos bloques que suben
    (-160, 76, -175, 92, 60, 22, 0.022), (160, 76, 175, 92, 60, 22, 0.022),
]


def _hacia_afuera(V, T, c):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, V[T].mean(1) - c) < 0
    T = T.copy(); T[malo] = T[malo][:, ::-1]
    return T


def pelo_theo(E, src_v47, carpeta):
    """Técnica 3: base del cráneo low-poly (cáscara V48.3 inflada, simplificada) + mechones explícitos (pelo_bloques)."""
    import receta_adan_v36 as v36
    from copox.medicion import pelo_bloques as pb
    pc, R, S, N = v49._base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    v = VOLUMEN
    a = np.clip((el - v["el0"]) / (v["el1"] - v["el0"]), 0, 1); a = a * a * (3 - 2 * a)
    H.Rd = H.Rd + v["lados"] + (v["corona"] - v["lados"]) * a
    Vb, Tb = H.malla(paso=0.0012)
    previo = os.environ.get("ALTH_CALIDAD")
    os.environ["ALTH_CALIDAD"] = "final"                      # la base siempre se simplifica: las facetas son el estilo
    Vb, Tb = v36.simplificar(Vb, Tb, TRIS_BASE, carpeta)
    if previo is None:
        os.environ.pop("ALTH_CALIDAD")
    else:
        os.environ["ALTH_CALIDAD"] = previo
    Tb = _hacia_afuera(Vb, Tb, np.asarray(v483.CENTRO))
    Vm, Tm = pb.peinado(H, MECHONES_THEO, escala=ESCALA, afilar=AFILAR, punta=0.30, romo=True)
    V = np.vstack([Vb, Vm]); T = np.vstack([Tb, Tm + len(Vb)])
    V, T, Nv = v49._facetado(V, T)
    J, W = v49._pesos_cabeza(E, V)
    mat = v41._material(E, "PELO_THEO_RUBIO", COLOR)
    E.j["materials"][mat]["doubleSided"] = False
    v49._nodo(E, "CAPA_PELO_THEO", [v41._prim_nueva(E, V, T, Nv, J, W, mat, "PELO_THEO")], junto_a="CAPA_GUIA_CAPILAR")
    for n in E.j["nodes"]:                                     # en este archivo de prueba solo se ve el pelo de Theo
        if n.get("name") in ("CAPA_GUIA_CAPILAR", "CAPA_PELO_CORTO", "CAPA_PELO_MECHONES"):
            n["extensions"] = {"KHR_node_visibility": {"visible": False}}
    v49._limpiar(carpeta)
    return {"operacion": "pelo de Theo (bloques)", "tris_base": int(len(Tb)), "tris_mechones": int(len(Tm)),
            "tris": int(len(T))}


def main(src, src_v47, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [pelo_theo(E, src_v47, os.path.dirname(os.path.abspath(dst)))]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Prueba: pelo de Theo intercambiable sobre Adán V49. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], sys.argv[3]):
        print(x)
