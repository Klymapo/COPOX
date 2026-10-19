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
TRIS = dict(pantalon_cadera=9000, pantalon_pierna_l=6000, pantalon_pierna_r=6000, camisa_torso=16000,
            camisa_manga_l=5000, camisa_manga_r=5000)


def _prims(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def prendas(E):
    """Partes separadas como el cuerpo (torso de la camisa, mangas, cadera del pantalón, perneras), encimadas igual que
    las piezas del cuerpo: cada parte sigue SOLO los pesos de su pieza y al posar no se pellizca en hombro ni ingle."""
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion.gltf import accesor
    P = _prims(E)

    def pz(n):
        q = P[n]
        return ra.Pieza(v39._leer(E, q, "POSITION"), v39._leer(E, q, "NORMAL"),
                        accesor(E.j, E.b, q["indices"]).reshape(-1, 3), J=v39._leer(E, q, "JOINTS_0"),
                        W=v39._leer(E, q, "WEIGHTS_0"))
    pl, pr_, torso, cuello = pz("PiernaL_PIEL"), pz("PiernaR_PIEL"), pz("Torso_PIEL"), pz("Cuello")
    bl, br = pz("BrazoL"), pz("BrazoR")
    short_, pretina = pz("Short_AZUL"), pz("Short_PRETINA")
    partes = {}
    cad = ra.Prenda([short_, pretina, torso],
                    region=lambda Q: np.maximum(Q[:, 1] - PANT["cintura"], 0.168 - Q[:, 1]),
                    holgura=0.0040, k=0.012)
    cad.visible = lambda Q: Q[:, 1] - PANT["cintura"]
    partes["pantalon_cadera"] = (cad, "pantalon", [torso], [short_, pretina])
    for nombre, pierna in (("pantalon_pierna_l", pl), ("pantalon_pierna_r", pr_)):
        pn = ra.Prenda([pierna], region=lambda Q: np.maximum(Q[:, 1] - 0.214, PANT["dobladillo"] - Q[:, 1]),
                       orilla=lambda Q: _ss((PANT["dobladillo"] + PANT["vuelta"] - Q[:, 1]) / 0.003),
                       holgura=0.0045, puno=0.0030)
        pn.visible = lambda Q: PANT["dobladillo"] - Q[:, 1]
        partes[nombre] = (pn, "pantalon", [pierna], [])
    afuera_cad = lambda Q: np.where(Q[:, 1] > 0.19, cad.cuerpo(Q) - 0.0065, 1.0)              # noqa: E731
    cam = ra.Prenda([torso, cuello],
                    region=lambda Q: np.maximum(CAMISA["borde"] - Q[:, 1], Q[:, 1] - CAMISA["cuello"]),
                    holgura=0.0040, k=0.010, extra=afuera_cad)
    cam.visible = cam.region
    partes["camisa_torso"] = (cam, "camisa", [torso, cuello], [short_, pretina])
    for nombre, brazo, sg in (("camisa_manga_l", bl, 1), ("camisa_manga_r", br, -1)):
        mg = ra.Prenda([brazo], region=lambda Q, sg=sg: np.maximum(0.090 - sg * Q[:, 0], sg * Q[:, 0] - CAMISA["manga"]),
                       orilla=lambda Q, sg=sg: _ss((sg * Q[:, 0] - (CAMISA["manga"] - CAMISA["puno"])) / 0.003),
                       holgura=0.0045, puno=0.0030)
        mg.visible = lambda Q, sg=sg: sg * Q[:, 0] - CAMISA["manga"]
        partes[nombre] = (mg, "camisa", [brazo], [])
    return partes


def ropa(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    nombres, _ = v40.v38_skin(E)
    partes = prendas(E)
    mats = {"pantalon": v41._material(E, "ROPA_PANTALON_AZUL", COLOR_PANTALON),
            "camisa": v41._material(E, "ROPA_CAMISA_BLANCA", COLOR_CAMISA)}
    log = {"operacion": "ropa de prueba"}
    prims = []
    for nombre, (prenda, mat, piel, respaldo) in partes.items():
        Vp = np.vstack([p.V0 for p in prenda.piezas])
        V, T = prenda.malla(Vp.min(0) - 0.015, Vp.max(0) + 0.015)
        n0 = len(T)
        V, T = v36.simplificar(V, T, TRIS[nombre], carpeta)
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        N = prenda.normales(V)
        # el simplificador deja triángulos volteados: cada uno se orienta con la normal del campo (hacia afuera)
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        al_reves = np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0
        T[al_reves] = T[al_reves][:, ::-1]
        log.setdefault("volteados", {})[nombre] = int(al_reves.sum())
        J4, W4 = ra.pesos_por_piel_visible(V, piel, len(nombres), respaldo)
        prims.append(v41._prim_nueva(E, V, T, N, J4, W4, mats[mat], f"ROPA_{nombre.upper()}"))
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


CULL_PIEZAS = ("Torso_PIEL", "BrazoL", "BrazoR", "PiernaL_PIEL", "PiernaR_PIEL")


def ocultar_bajo_ropa(E):
    """Skill vestuario: "prever culling bajo ropa solo en derivado reversible". En ESTE archivo de prueba se quitan los
    triángulos de piel que la ropa tapa por completo (a más de 1 cm de cualquier orilla): al posar, la piel escondida
    (el torso metido en el hombro, la cadera) ya no atraviesa la tela. El GLB de Adán no se toca."""
    from copox.medicion.gltf import accesor
    partes = prendas(E)
    P = _prims(E)
    log = {"operacion": "piel oculta bajo la ropa (solo en la prueba)"}
    for n in CULL_PIEZAS:
        q = P[n]
        V = v39._leer(E, q, "POSITION").astype(float)
        T = accesor(E.j, E.b, q["indices"]).reshape(-1, 3)
        dentro = np.zeros(len(V), bool)
        for pr_, *_ in partes.values():
            # margen de 1 cm solo junto a las orillas que se ven (puño, dobladillo, cuello, cintura); las orillas
            # internas (arranque de la manga dentro del torso) no dejan piel que asome al girar
            f = np.maximum(pr_.sdf(V), pr_.visible(V) + 0.010)
            dentro |= f < -0.0015
        quedan = ~dentro[T].all(1)
        import receta_adan_v24 as v24
        q["indices"] = v24._add_raw(E, np.ascontiguousarray(T[quedan].ravel(), np.uint32), 5125, "SCALAR", 34963)
        E.b = bytes(E.out)
        log[n] = int((~quedan).sum())
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [ropa(E, os.path.dirname(os.path.abspath(dst))), ocultar_bajo_ropa(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="PRUEBA de vestuario sobre Adán V48.3: camisa y pantalón ajustados. No es versión del personaje.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
