"""PRUEBA de vestuario (no es versión de Adán): camisa y pantalón ajustados sobre Adán V48.3.

Admin (19 oct 2026): "Hagamos unas pruebas" → ropa ajustada en movimiento. Skill alth-meta-vestuario-cabello, caso
"ajustada → skinning". Módulo aparte: el cuerpo no se toca; se agrega un nodo CAPA_ROPA_PRUEBA con su malla y la misma
piel (skin). Colores de la paleta: medidos/camisa_blanca #FBEFE1, medidos/pantalon_azul #4A5770.
Silueta de referencia: hoja de Theo (refs/personajes/joven-rubio-4-vistas.jpg): manga arremangada al antebrazo,
pantalón recto con vuelta sobre el zapato.
Uso: GODOT_BIN=… python prueba_ropa_adan.py ADAN_V48_3.glb ADAN_V48_3_ROPA_PRUEBA.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v41 as v41  # noqa: E402

COLOR_CAMISA, COLOR_PANTALON = "#FBEFE1", "#4A5770"
PANT = dict(cintura=0.276, dobladillo=0.060, vuelta=0.014)
CAMISA = dict(borde=0.215, cuello=0.492, manga=0.212, puno=0.015)
TRIS = dict(pantalon=9000, camisa=12000)


def _prims(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def prendas(E):
    from copox.medicion import ropa_ajustada as ra
    P = _prims(E)
    from copox.medicion.gltf import accesor

    def pz(n):
        q = P[n]
        return ra.Pieza(v39._leer(E, q, "POSITION"), v39._leer(E, q, "NORMAL"),
                        accesor(E.j, E.b, q["indices"]).reshape(-1, 3), J=v39._leer(E, q, "JOINTS_0"),
                        W=v39._leer(E, q, "WEIGHTS_0"))
    pierna_l, pierna_r, torso = pz("PiernaL_PIEL"), pz("PiernaR_PIEL"), pz("Torso_PIEL")
    short_, pretina = pz("Short_AZUL"), pz("Short_PRETINA")
    pant = ra.Prenda([short_, pretina, pierna_l, pierna_r, torso],
                     region=lambda Q: np.maximum(Q[:, 1] - PANT["cintura"], PANT["dobladillo"] - Q[:, 1]),
                     orilla=lambda Q: _ss((PANT["dobladillo"] + PANT["vuelta"] - Q[:, 1]) / 0.003),
                     holgura=0.0040, adentro=0.0025, puno=0.0030, k=0.012)
    afuera_pant = lambda Q: np.where(Q[:, 1] > 0.19, pant.cuerpo(Q) - 0.0065, 1.0)              # noqa: E731
    camisa = ra.Prenda([torso, pz("BrazoL"), pz("BrazoR"), pz("Cuello")],
                       region=lambda Q: np.maximum.reduce([CAMISA["borde"] - Q[:, 1], Q[:, 1] - CAMISA["cuello"],
                                                           np.abs(Q[:, 0]) - CAMISA["manga"]]),
                       orilla=lambda Q: _ss((np.abs(Q[:, 0]) - (CAMISA["manga"] - CAMISA["puno"])) / 0.003),
                       holgura=0.0040, adentro=0.0025, puno=0.0030, k=0.010, extra=afuera_pant)
    pant.todas = pant.piezas
    camisa.todas = camisa.piezas + [short_, pierna_l, pierna_r]
    return pant, camisa


def ropa(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    P = _prims(E)
    nombres, _ = v40.v38_skin(E)
    fuente = lambda n: (v39._leer(E, P[n], "POSITION").astype(float), v39._leer(E, P[n], "JOINTS_0").astype(int),  # noqa: E731
                        v39._leer(E, P[n], "WEIGHTS_0").astype(float))
    pant, camisa = prendas(E)
    cajas = {"pantalon": ((-0.16, 0.045, -0.05), (0.16, 0.29, 0.13)),
             "camisa": ((-0.235, 0.20, -0.095), (0.235, 0.515, 0.14))}
    fuentes = {"pantalon": [fuente(n) for n in ("PiernaL_PIEL", "PiernaR_PIEL", "Short_AZUL", "Torso_PIEL")],
               "camisa": [fuente(n) for n in ("Torso_PIEL", "BrazoL", "BrazoR", "Cuello", "Short_AZUL")]}
    mats = {"pantalon": v41._material(E, "ROPA_PANTALON_AZUL", COLOR_PANTALON),
            "camisa": v41._material(E, "ROPA_CAMISA_BLANCA", COLOR_CAMISA)}
    log = {"operacion": "ropa de prueba"}
    prims = []
    for nombre, prenda in (("pantalon", pant), ("camisa", camisa)):
        V, T = prenda.malla(*cajas[nombre])
        n0 = len(T)
        V, T = v36.simplificar(V, T, TRIS[nombre], carpeta)
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        N = prenda.normales(V)
        J4, W4, cuenta = ra.pesos_por_dueno(V, prenda.todas, len(nombres))
        prims.append(v41._prim_nueva(E, V, T, N, J4, W4, mats[nombre], f"ROPA_{nombre.upper()}"))
        log[nombre] = {"tris_marching": int(n0), "tris": int(len(T))}
    E.j["meshes"].append({"name": "ROPA_PRUEBA", "primitives": prims})
    E.j["nodes"].append({"name": "CAPA_ROPA_PRUEBA", "mesh": len(E.j["meshes"]) - 1, "skin": 0})
    padre = next(n for n in E.j["nodes"] if any(E.j["nodes"][c].get("name") == "CAPA_SHORT" for c in n.get("children", [])))
    padre["children"].append(len(E.j["nodes"]) - 1)
    # el short queda debajo del pantalón: oculto en esta prueba (KHR_node_visibility, igual que las manos)
    short_ = next(n for n in E.j["nodes"] if n.get("name") == "CAPA_SHORT")
    short_.setdefault("extensions", {})["KHR_node_visibility"] = {"visible": False}
    usados = E.j.setdefault("extensionsUsed", [])
    if "KHR_node_visibility" not in usados:
        usados.append("KHR_node_visibility")
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [ropa(E, os.path.dirname(os.path.abspath(dst)))]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="PRUEBA de vestuario sobre Adán V48.3: camisa y pantalón ajustados. No es versión del personaje.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
