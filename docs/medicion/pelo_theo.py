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
VOLUMEN = dict(corona=0.026, lados=0.004, el0=10.0, el1=70.0)
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ARCO = True                       # SENKU pelo_arco: la base sigue el casco de la hoja; los mechones van encima
ESPESOR_ARCO = 0.032              # la base queda bajo el arco este tanto: la cubren los mechones
TRIS_BASE = 500                   # base del cráneo: pocas caras grandes
ESCALA = 1.55
AFILAR = 0.55
# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm, despega_m); az 0 = frente, +90 = su izquierda (+x)
MECHONES_THEO = [
    # (con ARCO la altura y el ancho los pone el casco de la hoja; aquí solo va el trazo de cada mechón)
    # barridos de arriba: nacen sobre la frente y corren por el arco hacia la coronilla (los planos grandes del perfil)
    (-34, 58, -150, 52, 92, 30, 0.0, 8), (0, 60, 180, 54, 96, 32, 0.0), (34, 58, 150, 52, 92, 30, 0.0, -8),
    # picos del copete: suben desde la raya (la "M" vista de frente)
    (-12, 56, -40, 86, 70, 28, 0.010, 14), (12, 56, 40, 86, 70, 28, 0.010, -14),
    # fleco en "M": caen sobre la frente, despegados
    (-8, 74, -26, 42, 50, 20, 0.010, -15), (8, 74, 26, 42, 50, 20, 0.010, 15),
    # mechones largos que enmarcan la cara: bajan por las sienes hasta la mejilla
    (-26, 70, -58, -14, 52, 18, 0.016), (26, 70, 58, -14, 52, 18, 0.016),
    (-44, 66, -74, 0, 56, 20, 0.012), (44, 66, 74, 0, 56, 20, 0.012),
    # lados sobre la oreja
    (-80, 62, -102, 8, 72, 22, 0.006), (80, 62, 102, 8, 72, 22, 0.006),
    # atrás: bloques verticales grandes hacia la nuca
    (-150, 66, -156, -34, 90, 24, 0.008), (-112, 60, -126, -24, 80, 22, 0.008), (150, 66, 156, -34, 90, 24, 0.008),
    (112, 60, 126, -24, 80, 22, 0.008), (180, 68, 180, -36, 90, 24, 0.008),
    # coronilla: un bloque que se levanta
    (165, 74, 150, 88, 64, 24, 0.008),
]
# cobertura (compuerta pelo_cobertura): patillas, sobre y detrás de la oreja, nuca baja. Fijos a Head (sin resorte):
# son cortos y van pegados al cuero.
MECHONES_CUBRE = [
    (-70, 24, -68, -20, 46, 14, 0.002), (70, 24, 68, -20, 46, 14, 0.002),
    (-118, 30, -120, -24, 56, 16, 0.003), (118, 30, 120, -24, 56, 16, 0.003),
    (-136, 40, -140, -48, 64, 18, 0.004), (136, 40, 140, -48, 64, 18, 0.004),
    (-168, 40, -172, -58, 70, 18, 0.004), (168, 40, 172, -58, 70, 18, 0.004), (180, 40, 180, -58, 60, 18, 0.004),
    (-152, 40, -154, -56, 60, 18, 0.004), (152, 40, 154, -56, 60, 18, 0.004),
    (-94, 26, -95, -4, 50, 14, 0.002), (94, 26, 95, -4, 50, 14, 0.002),
    (-58, 24, -60, -12, 44, 14, 0.002), (58, 24, 60, -12, 44, 14, 0.002),
    (-112, 20, -114, -26, 50, 14, 0.003), (112, 20, 114, -26, 50, 14, 0.003),
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
    from copox.medicion import pelo_cobertura as pcob
    from copox.medicion import pelo_huesos as ph
    pc, R, S, N = v49._base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    v = VOLUMEN
    a = np.clip((el - v["el0"]) / (v["el1"] - v["el0"]), 0, 1); a = a * a * (3 - 2 * a)
    if ARCO:                                                  # SENKU: el arco sale de la hoja (casco visual)
        from copox.medicion import pelo_arco as pa
        ref = pa.vistas_ref(os.path.join(RAIZ, pa.REF))
        al = pa.alinear(ref, pa.esqueleto(E))
        from types import SimpleNamespace
        Rd0 = H.Rd.copy()
        H.Rd, Rcasco = pa.arco(H, np.asarray(v483.CENTRO), ref, al, ESPESOR_ARCO)
        guia = SimpleNamespace(arbol=H.arbol, Rd=np.where(H.Md > 0.5, np.maximum(Rcasco, Rd0), Rd0),
                               n=len(MECHONES_THEO))
    else:
        guia = None
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
    Vm, Tm, ids, sv, curvas = pb.peinado(H, MECHONES_THEO + MECHONES_CUBRE, escala=ESCALA, afilar=AFILAR, punta=0.30, romo=True,
                                         detalle=True, arco=guia)
    V = np.vstack([Vb, Vm]); T = np.vstack([Tb, Tm + len(Vb)])
    # compuerta: el pelo cubre toda el área de pelo de la guía (si no, no se entrega)
    piel = v49._prims(E)[v482.PIEL]
    import receta_adan_v39 as v39
    from copox.medicion.gltf import accesor
    Vs = v39._leer(E, piel, "POSITION").astype(float); Ts = accesor(E.j, E.b, piel["indices"]).reshape(-1, 3)
    Ts = Ts[(Vs[Ts][:, :, 1] > 0.47).all(1)]
    cob = pcob.cobertura(V, T, v483.CENTRO, H.D, H.Md, piel=(Vs, Ts), Rd=H.Rd)
    print("cobertura del pelo:", cob)
    if cob["veredicto"] != "PASS" and not os.environ.get("ALTH_DIAGNOSTICO"):   # diagnóstico: construir para mirar
        raise SystemExit("FAIL cobertura del pelo: " + str(cob))
    # huesos por mechón (resortes en el motor) y pesos: base en Head, mechones de la raíz (Head) a su cadena
    cadenas, jh = ph.agregar_cadenas(E, curvas[:len(MECHONES_THEO)])
    J, W = ph.pesos(ids, sv, cadenas, jh, n_base=len(Vb))
    J, W = J[T].reshape(-1, 4), W[T].reshape(-1, 4)            # mismo orden que el facetado (un vértice por esquina)
    V, T, Nv = v49._facetado(V, T)
    c = np.asarray(v483.CENTRO)
    r_col = min(float(np.linalg.norm(C[1:] - c, axis=1).min()) for C in curvas[:len(MECHONES_THEO)]) - 0.012
    import copox.medicion.gltf as gl
    sk = E.j["skins"][0]
    IBM = gl.accesor(E.j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    c_local = (IBM[jh] @ np.append(c, 1.0))[:3]
    nombres = [[E.j["nodes"][sk["joints"][k]]["name"] for k in cad] for cad in cadenas]
    extras = ph.config(nombres, c_local, r_col)
    mat = v41._material(E, "PELO_THEO_RUBIO", COLOR)
    E.j["materials"][mat]["doubleSided"] = False
    v49._nodo(E, "CAPA_PELO_THEO", [v41._prim_nueva(E, V, T, Nv, J, W, mat, "PELO_THEO")], junto_a="CAPA_GUIA_CAPILAR")
    E.j["nodes"][-1]["extras"] = extras
    for n in E.j["nodes"]:                                     # en este archivo de prueba solo se ve el pelo de Theo
        if n.get("name") in ("CAPA_GUIA_CAPILAR", "CAPA_PELO_CORTO", "CAPA_PELO_MECHONES"):
            n["extensions"] = {"KHR_node_visibility": {"visible": False}}
    v49._limpiar(carpeta)
    return {"operacion": "pelo de Theo (bloques + resortes)", "tris_base": int(len(Tb)), "tris_mechones": int(len(Tm)),
            "tris": int(len(T)), "cobertura": cob["cobertura"], "huesos_pelo": 4 * len(cadenas),
            "radio_colision": round(r_col, 4)}


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
