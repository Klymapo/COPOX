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
VOLUMEN = dict(corona=0.030, lados=0.006, el0=10.0, el1=70.0)
TRIS = 2400                       # pocas caras grandes: facetas como la hoja
# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm, despega_m); az 0 = frente, +90 = su izquierda (+x)
MECHONES_THEO = [
    # pico en "M" sobre la frente (raya al centro), despegados de la frente
    (-10, 76, -18, 36, 56, 20, 0.008), (10, 76, 18, 36, 56, 20, 0.008),
    # mechones largos que enmarcan la cara: bajan por las sienes hasta la mejilla
    (-26, 70, -58, -14, 52, 18, 0.016), (26, 70, 58, -14, 52, 18, 0.016),
    (-44, 66, -74, 0, 56, 20, 0.012), (44, 66, 74, 0, 56, 20, 0.012),
    # copete: nacen arriba de la frente y suben hacia atrás (picos con altura)
    (-22, 66, -60, 92, 70, 26, 0.026), (22, 66, 60, 92, 70, 26, 0.026), (0, 70, 0, 96, 66, 26, 0.030),
    # arriba-atrás: barren hacia la coronilla y se levantan
    (-70, 66, -140, 80, 72, 24, 0.020), (70, 66, 140, 80, 72, 24, 0.020),
    # lados sobre la oreja
    (-84, 58, -102, 8, 66, 20, 0.006), (84, 58, 102, 8, 66, 20, 0.006),
    # atrás: bloques verticales hacia la nuca
    (-158, 64, -162, -22, 76, 22, 0.006), (-120, 60, -136, -14, 70, 20, 0.006), (158, 64, 162, -22, 76, 22, 0.006),
    (120, 60, 136, -14, 70, 20, 0.006), (180, 66, 180, -26, 76, 22, 0.006),
    # coronilla: dos bloques que suben
    (-160, 76, -175, 92, 60, 22, 0.022), (160, 76, 175, 92, 60, 22, 0.022),
]


def pelo_theo(E, src_v47, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import pelo_mechones as pm
    pc, R, S, N = v49._base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    v = VOLUMEN
    a = np.clip((el - v["el0"]) / (v["el1"] - v["el0"]), 0, 1); a = a * a * (3 - 2 * a)
    H.Rd = H.Rd + v["lados"] + (v["corona"] - v["lados"]) * a
    M = pm.PeloCunas(H, mechones=MECHONES_THEO, hundir=0.0, levanta=1.0, k_mechon=0.0015, k_union=0.002, escala=1.35, afilar=0.45)
    V, T = M.malla(paso=0.0012)
    n0 = len(T)
    previo = os.environ.get("ALTH_CALIDAD")
    os.environ["ALTH_CALIDAD"] = "final"                      # el pelo siempre se simplifica: las facetas son el estilo
    V, T = v36.simplificar(V, T, TRIS, carpeta)
    if previo is None:
        os.environ.pop("ALTH_CALIDAD")
    else:
        os.environ["ALTH_CALIDAD"] = previo
    Nv = M.normales(V)
    T = v49._orientar(V, T, Nv)
    V, T, Nv = v49._facetado(V, T)
    J, W = v49._pesos_cabeza(E, V)
    mat = v41._material(E, "PELO_THEO_RUBIO", COLOR)
    E.j["materials"][mat]["doubleSided"] = False
    v49._nodo(E, "CAPA_PELO_THEO", [v41._prim_nueva(E, V, T, Nv, J, W, mat, "PELO_THEO")], junto_a="CAPA_GUIA_CAPILAR")
    for n in E.j["nodes"]:                                     # en este archivo de prueba solo se ve el pelo de Theo
        if n.get("name") in ("CAPA_GUIA_CAPILAR", "CAPA_PELO_CORTO", "CAPA_PELO_MECHONES"):
            n["extensions"] = {"KHR_node_visibility": {"visible": False}}
    v49._limpiar(carpeta)
    return {"operacion": "pelo de Theo", "tris_marching": int(n0), "tris": int(len(T))}


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
