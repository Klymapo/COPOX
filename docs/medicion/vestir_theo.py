"""Theo vestido (derivado de entrega; no reemplaza theo_alpha.glb): Adán V49 con el pelo de Theo aprobado + la ropa de la
hoja (refs/personajes/joven-rubio-4-vistas.jpg). Admin (19 oct 2026): "Después intentaremos vestir a Theo con su ropa
que le corresponde" → "Adán ajustado a Theo" (SENKU midió el cuerpo de Adán contra la hoja: las proporciones ya
coinciden; lo que falta es el volumen de la ropa).

Prendas (técnica ropa_ajustada, skill alth-meta-vestuario-cabello "ajustada → skinning"):
- camisa blanca (medidos/camisa_blanca) arremangada al antebrazo, cuello visible;
- chaleco negro (medidos/chaleco_negro) sin mangas, escote en V hasta media pecho, cae sobre el pantalón;
- corbata azul (medidos/corbata_azul) entre camisa y chaleco: se ve en la V;
- pantalón azul (medidos/pantalon_azul) recto con vuelta;
- zapatos negros: la pieza PIES_TENIS recoloreada (medidos/zapato_negro; suela negro_calido/5).
Capas (sobre el torso ya inflado 6.5 mm por la cadera): camisa +4 mm, corbata +7.5 mm, chaleco +10.5 mm. La piel tapada se quita solo en este derivado.
Uso: GODOT_BIN=… python vestir_theo.py ADAN_V49_PELO_THEO.glb THEO_VESTIDO.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import prueba_ropa_adan as pr  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v41 as v41  # noqa: E402

COLORES = {"camisa": "#FBEFE1", "pantalon": "#4A5770", "chaleco": "#302E2D", "corbata": "#41598D"}
ZAPATO, SUELA = "#292929", "#1F1916"
CHALECO = dict(borde=0.250, hombro_x=0.116, v_fondo=0.372, v_ancho=0.040, cuello=0.478, holgura=0.0105)
CORBATA = dict(nudo=0.470, punta=0.318, ancho_nudo=0.011, ancho=0.020, holgura=0.0075)
FRENTE_Z = 0.030                                   # z > esto = pecho (el torso de Adán va de −0.06 a 0.11)
TRIS = dict(pr.TRIS, chaleco=9000, corbata=1200)
VISIBLE = {"CAPA_SHORT": False, "PIES_DESCALZOS": False, "PIES_TENIS": True, "CAPA_GUIA_CAPILAR": False,
           "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": False, "CAPA_PELO_THEO": True}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# de la hoja: manga larga arremangada cerca de la muñeca; pantalón recto y holgado que cae sobre el zapato
pr.CAMISA.update(manga=0.272, puno=0.016)
pr.PANT.update(dobladillo=0.046, vuelta=0.016)
HOLGURA_PIERNA = 0.0095


def prendas_theo(E):
    from copox.medicion import ropa_ajustada as ra
    partes = pr.prendas(E)
    for n in ("pantalon_pierna_l", "pantalon_pierna_r"):
        partes[n][0].holgura = HOLGURA_PIERNA
    cam, _, piel_cam, resp = partes["camisa_torso"]
    torso, cuello = cam.piezas[0], cam.piezas[1]
    c = CHALECO

    def v_abierta(Q):                              # > 0 dentro del escote (fuera del chaleco)
        t = np.clip((Q[:, 1] - c["v_fondo"]) / (c["cuello"] - c["v_fondo"]), 0, 1)
        w = c["v_ancho"] * t
        return np.where((Q[:, 2] > FRENTE_Z) & (Q[:, 1] > c["v_fondo"]), w - np.abs(Q[:, 0]), -1.0)

    def region_chaleco(Q):
        return np.maximum.reduce([c["borde"] - Q[:, 1], Q[:, 1] - c["cuello"], np.abs(Q[:, 0]) - c["hombro_x"],
                                  v_abierta(Q)])
    ch = ra.Prenda([torso, cuello], region=region_chaleco, holgura=c["holgura"], k=0.010, extra=cam.extra)
    ch.visible = region_chaleco
    partes["chaleco"] = (ch, "chaleco", piel_cam, resp)
    k = CORBATA

    def region_corbata(Q):
        t = np.clip((k["nudo"] - Q[:, 1]) / (k["nudo"] - k["punta"]), 0, 1)
        w = k["ancho_nudo"] + (k["ancho"] - k["ancho_nudo"]) * _ss(t / 0.35)
        w = w * np.where(t > 0.9, 1 - (t - 0.9) / 0.1 * 0.95, 1.0)       # punta en pico
        return np.maximum.reduce([np.abs(Q[:, 0]) - w, Q[:, 1] - k["nudo"], k["punta"] - Q[:, 1], FRENTE_Z - Q[:, 2]])
    co = ra.Prenda([torso, cuello], region=region_corbata, holgura=k["holgura"], k=0.010, extra=cam.extra)
    co.visible = region_corbata
    partes["corbata"] = (co, "corbata", piel_cam, resp)
    return partes


def ropa(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    nombres, _ = v40.v38_skin(E)
    partes = prendas_theo(E)
    mats = {k: v41._material(E, f"THEO_{k.upper()}", col) for k, col in COLORES.items()}
    log = {"operacion": "ropa de Theo"}
    prims = []
    for nombre, (prenda, mat, piel, respaldo) in partes.items():
        Vp = np.vstack([p.V0 for p in prenda.piezas])
        V, T = prenda.malla(Vp.min(0) - 0.02, Vp.max(0) + 0.02)
        n0 = len(T)
        V, T = v36.simplificar(V, T, TRIS[nombre], carpeta)
        N = prenda.normales(V)
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        al_reves = np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0
        T[al_reves] = T[al_reves][:, ::-1]
        J4, W4 = ra.pesos_por_piel_visible(V, piel, len(nombres), respaldo)
        prims.append(v41._prim_nueva(E, V, T, N, J4, W4, mats[mat], f"THEO_{nombre.upper()}"))
        log[nombre] = {"tris_marching": int(n0), "tris": int(len(T))}
    E.j["meshes"].append({"name": "ROPA_THEO", "primitives": prims})
    E.j["nodes"].append({"name": "CAPA_ROPA_THEO", "mesh": len(E.j["meshes"]) - 1, "skin": 0})
    padre = next(n for n in E.j["nodes"] if any(E.j["nodes"][ch].get("name") == "CAPA_SHORT" for ch in n.get("children", [])))
    padre["children"].append(len(E.j["nodes"]) - 1)
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return log


def zapatos(E):
    """Los tenis de V49 pasan a zapatos negros (solo color; misma pieza intercambiable)."""
    hechos = {}
    for m in E.j["meshes"]:
        for p in m["primitives"]:
            pz = p.get("extras", {}).get("pieza", "")
            if pz.startswith("Tenis"):
                col = SUELA if pz.endswith("SUELA") else ZAPATO
                if col not in hechos:
                    hechos[col] = v41._material(E, "THEO_ZAPATO" + ("_SUELA" if col == SUELA else ""), col)
                p["material"] = hechos[col]
    return {"operacion": "zapatos negros", "materiales": len(hechos)}


def elegir(E):
    usados = E.j.setdefault("extensionsUsed", [])
    if "KHR_node_visibility" not in usados:
        usados.append("KHR_node_visibility")
    for n in E.j["nodes"]:
        if n.get("name") in VISIBLE:
            ext = n.setdefault("extensions", {})
            if VISIBLE[n["name"]]:
                ext.pop("KHR_node_visibility", None)
                if not ext:
                    n.pop("extensions")
            else:
                ext["KHR_node_visibility"] = {"visible": False}
    return {"operacion": "piezas elegidas", **VISIBLE}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [ropa(E, os.path.dirname(os.path.abspath(dst))), pr.ocultar_bajo_ropa(E), zapatos(E), elegir(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Theo vestido: Adán V49 + pelo de Theo + camisa, chaleco, corbata, pantalón y zapatos. "
                        "Derivado de entrega; theo_alpha.glb no se toca.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
