"""Pelo de cualquier personaje (19 oct 2026): la técnica del pelo de Theo (aprobada de momento) como receta general.
Brief: docs/investigacion/pelo_alastor.md. Uso desde otra receta: `pelo_personaje.pelo(E, ADAN_V47, carpeta, ref, ...)`.
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
from pelo_theo import (AFILAR, ESCALA, ESPESOR_ARCO, MECHONES_CUBRE, TRIS_BASE, VOLUMEN, JITTER, RAIZ,  # noqa: E402,F401
                       ARCO, _hacia_afuera)


def pelo(E, src_v47, carpeta, ref, mechones, color, nodo="CAPA_PELO_X", pieza="PELO_X", prefijo="PeloX",
         escala=ESCALA, afilar=AFILAR, punta=0.30, cubre=None, volumen=None, espesor_arco=ESPESOR_ARCO, tris_base=TRIS_BASE):
    """El pelo de Theo como receta general: base del cráneo con el ARCO medido por SENKU en la hoja `ref` + mechones
    explícitos `mechones` (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm, despega[, giro]) + mechones de
    cobertura fijos + resortes por mechón (huesos `prefijo`_NN_k). Nodo intercambiable `nodo`."""
    cubre = MECHONES_CUBRE if cubre is None else cubre
    import receta_adan_v36 as v36
    from copox.medicion import pelo_bloques as pb
    from copox.medicion import pelo_cobertura as pcob
    from copox.medicion import pelo_huesos as ph
    pc, R, S, N = v49._base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    v = volumen or VOLUMEN
    a = np.clip((el - v["el0"]) / (v["el1"] - v["el0"]), 0, 1); a = a * a * (3 - 2 * a)
    if ARCO and ref:                                          # SENKU: el arco sale de la hoja (casco visual)
        from copox.medicion import pelo_arco as pa
        ref_h = pa.vistas_ref(os.path.join(RAIZ, ref))
        al = pa.alinear(ref_h, pa.esqueleto(E))
        from types import SimpleNamespace
        Rd0 = H.Rd.copy()
        H.Rd, Rcasco = pa.arco(H, np.asarray(v483.CENTRO), ref_h, al, espesor_arco)
        guia = SimpleNamespace(arbol=H.arbol, Rd=np.where(H.Md > 0.5, np.maximum(Rcasco, Rd0), Rd0),
                               n=len(mechones))
    else:
        guia = None
        H.Rd = H.Rd + v["lados"] + (v["corona"] - v["lados"]) * a
    Vb, Tb = H.malla(paso=0.0012)
    previo = os.environ.get("ALTH_CALIDAD")
    os.environ["ALTH_CALIDAD"] = "final"                      # la base siempre se simplifica: las facetas son el estilo
    Vb, Tb = v36.simplificar(Vb, Tb, tris_base, carpeta)
    if previo is None:
        os.environ.pop("ALTH_CALIDAD")
    else:
        os.environ["ALTH_CALIDAD"] = previo
    Tb = _hacia_afuera(Vb, Tb, np.asarray(v483.CENTRO))
    pb.JITTER = JITTER
    Vm, Tm, ids, sv, curvas = pb.peinado(H, list(mechones) + list(cubre), escala=escala, afilar=afilar, punta=punta, romo=True,
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
    cadenas, jh = ph.agregar_cadenas(E, curvas[:len(mechones)], prefijo=prefijo)
    J, W = ph.pesos(ids, sv, cadenas, jh, n_base=len(Vb))
    J, W = J[T].reshape(-1, 4), W[T].reshape(-1, 4)            # mismo orden que el facetado (un vértice por esquina)
    V, T, Nv = v49._facetado(V, T)
    c = np.asarray(v483.CENTRO)
    r_col = min(float(np.linalg.norm(C[1:] - c, axis=1).min()) for C in curvas[:len(mechones)]) - 0.012
    import copox.medicion.gltf as gl
    sk = E.j["skins"][0]
    IBM = gl.accesor(E.j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    c_local = (IBM[jh] @ np.append(c, 1.0))[:3]
    nombres = [[E.j["nodes"][sk["joints"][k]]["name"] for k in cad] for cad in cadenas]
    extras = ph.config(nombres, c_local, r_col)
    mat = v41._material(E, pieza + "_COLOR", color)
    E.j["materials"][mat]["doubleSided"] = False
    v49._nodo(E, nodo, [v41._prim_nueva(E, V, T, Nv, J, W, mat, pieza)], junto_a="CAPA_GUIA_CAPILAR")
    E.j["nodes"][-1]["extras"] = extras
    v49._limpiar(carpeta)
    return {"operacion": f"pelo {nodo} (arco SENKU + bloques + resortes)", "tris_base": int(len(Tb)), "tris_mechones": int(len(Tm)),
            "tris": int(len(T)), "cobertura": cob["cobertura"], "huesos_pelo": 4 * len(cadenas),
            "radio_colision": round(r_col, 4)}


