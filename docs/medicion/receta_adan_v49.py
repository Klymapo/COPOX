"""Adán V49 (sobre V48.3): pelvis, cuero cabelludo, tenis intercambiables y un corte de pelo intercambiable.

Admin (19 oct 2026): "Haz la pelvis, colócale unos tenis de pieza intercambiable y haz un intercambiable de pelo
sencillo. Un corte fácil que sirva de intercambiable." Antes: "Los shorts deberían poder ser intercambiables. Poder
quitarse. Los pies igual serán piezas intercambiables."
1. Pelvis (cuerpo): entre el torso (cierra en y≈0.262) y las piernas (cierran en y≈0.218) no había piel; el short
   tapaba el hueco. Pieza lisa, unión suave de torso, piernas y un bloque de cadera; entrepierna lisa. Pesos: Hips arriba,
   rampa a cada muslo abajo (como el short). El short (CAPA_SHORT) ya se puede quitar.
2. Cuero cabelludo (cuerpo): la piel expuesta no cubría la parte de arriba de la cabeza (el pelo era la cabeza). Copia de la
   cara exterior del pelo 2.5 mm hacia adentro, color piel: cualquier pelo intercambiable cierra sobre él.
3. Tenis (CALZADO_TENIS, intercambiable): caja redondeada por pie que envuelve pie y tobillo, suela crema_suave/2 #F7F0E7
   y corte rojo_calido/3 #A8453B. Pesos de la piel del pie que tapan.
4. Pelo corto (CAPA_PELO_CORTO, intercambiable, oculto por defecto con KHR_node_visibility): misma técnica que V48.3,
   con lados y nuca más arriba y un poco más de volumen arriba. El pelo de V48.3 sigue como el visible.
Uso: GODOT_BIN=… python receta_adan_v49.py ADAN_V48_3.glb ADAN_V47.glb ADAN_V49.glb
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
import receta_adan_v48_2 as v482  # noqa: E402
import receta_adan_v48_3 as v483  # noqa: E402

COLOR_SUELA, COLOR_TENIS = "#F7F0E7", "#A8453B"
CADERA = dict(y_top=0.280, y_bot=0.192, ancho_top=0.112, ancho_bot=0.028, fondo_top=0.080, fondo_bot=0.046, zc=0.022,
              k=0.030, arriba=0.292, abajo=0.180, hundir=0.0015)
CUERO = 0.0045
TENIS = dict(holgura_x=0.008, holgura_z=0.010, suela=0.007, collar=0.058, punta=0.032, sobre_pie=0.007, n=4.0,
             corte_suela=0.007, redondeo=0.014)
CORTE = dict(lados_y=0.605, nuca_y=0.524, frente_az=45.0, volumen=0.0025, lados=0.0)
TRIS = dict(pelvis=3000, cuero=4000, tenis=2500, pelo_corto=9000, mechones=5000)


def _prims(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _pieza(E, n):
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion.gltf import accesor
    q = _prims(E)[n]
    return ra.Pieza(v39._leer(E, q, "POSITION"), v39._leer(E, q, "NORMAL"), accesor(E.j, E.b, q["indices"]).reshape(-1, 3),
                    J=v39._leer(E, q, "JOINTS_0"), W=v39._leer(E, q, "WEIGHTS_0"))


def _orientar(V, T, N):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    al_reves = np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0
    T = T.copy(); T[al_reves] = T[al_reves][:, ::-1]
    return T


def _al_cuerpo(E, prim):
    """Agrega una primitiva a la malla del cuerpo (con los morphs en cero, como las demás)."""
    malla = E.j["meshes"][0]
    ntar = len(malla["primitives"][0].get("targets", []))
    if ntar:
        nv = E.j["accessors"][prim["attributes"]["POSITION"]]["count"]
        ceros = E._add(np.zeros((nv, 3), np.float32), "VEC3", None, True)
        prim["targets"] = [{"POSITION": ceros} for _ in range(ntar)]
    malla["primitives"].append(prim)
    E.b = bytes(E.out)


def _nodo(E, nombre, prims, junto_a="CAPA_SHORT", visible=True):
    E.j["meshes"].append({"name": nombre, "primitives": prims})
    E.j["nodes"].append({"name": nombre, "mesh": len(E.j["meshes"]) - 1, "skin": 0})
    k = len(E.j["nodes"]) - 1
    padre = next(n for n in E.j["nodes"] if any(E.j["nodes"][c].get("name") == junto_a for c in n.get("children", [])))
    padre["children"].append(k)
    if not visible:
        E.j["nodes"][k]["extensions"] = {"KHR_node_visibility": {"visible": False}}
        usados = E.j.setdefault("extensionsUsed", [])
        if "KHR_node_visibility" not in usados:
            usados.append("KHR_node_visibility")
    E.b = bytes(E.out)


def _limpiar(carpeta):
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))


# 1 ── pelvis ───────────────────────────────────────────────────────────────────────────────────────────────────────
class _Pelvis:
    def __init__(self, torso, pl, pr_):
        from copox.medicion import ropa_ajustada as ra
        self.ra, self.piezas = ra, [torso, pl, pr_]

    def sdf(self, P):
        """Pelvis en triángulo (ancha arriba como el torso, angosta abajo en la entrepierna), unida en suave a torso y
        piernas con un radio grande: una sola pieza orgánica."""
        ra, c = self.ra, CADERA
        y = P[:, 1]
        t = np.clip((c["y_top"] - y) / (c["y_top"] - c["y_bot"]), 0, 1)
        w = c["ancho_top"] + (c["ancho_bot"] - c["ancho_top"]) * t ** 0.85
        dz = c["fondo_top"] + (c["fondo_bot"] - c["fondo_top"]) * t
        zc = c["zc"]
        k = np.sqrt((P[:, 0] / w) ** 2 + ((P[:, 2] - zc) / dz) ** 2)
        d = (k - 1) * np.minimum(w, dz)
        d = -ra.smin(-d, -(c["y_bot"] - y), 0.014)                 # fondo redondo en la entrepierna
        for p in self.piezas:
            d = ra.smin(d, p.sdf(P), c["k"])
        sobre = 0.0012 * np.exp(-((y - 0.214) / 0.010) ** 2)
        d = d + c["hundir"] - (c["hundir"] + sobre) * np.exp(-((y - 0.214) / 0.012) ** 2)
        return np.maximum(d, np.maximum(y - c["arriba"], c["abajo"] - y))


def pelvis(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import short_geo as sg
    nombres, _ = v40.v38_skin(E)
    S = _Pelvis(_pieza(E, "Torso_PIEL"), _pieza(E, "PiernaL_PIEL"), _pieza(E, "PiernaR_PIEL"))
    V, T = sg.malla_sdf(S.sdf, (-0.16, CADERA["abajo"] - 0.01, -0.09), (0.16, CADERA["arriba"] + 0.01, 0.14), paso=0.0012,
                        pulido=4)
    V, T = ra.solo_mayor(V, T)
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS["pelvis"], carpeta)
    N = _normales_sdf(S.sdf, V)
    T = _orientar(V, T, N)
    J4, W4 = v41.pesos_short(V, nombres, y_ent=0.214, y_cint=0.27, alto=0.035, centro=0.03, maximo=1.0)
    mat = _prims(E)["Torso_PIEL"]["material"]
    _al_cuerpo(E, v41._prim_nueva(E, V, T, N, J4, W4, mat, "Pelvis_PIEL"))
    _limpiar(carpeta)
    return {"operacion": "pelvis", "tris_marching": int(n0), "tris": int(len(T))}


def _normales_sdf(sdf, V, h=0.0004):
    g = np.zeros_like(V)
    for i in range(3):
        e = np.zeros(3); e[i] = h
        g[:, i] = sdf(V + e) - sdf(V - e)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


# 2 ── cuero cabelludo ─────────────────────────────────────────────────────────────────────────────────────────────
def _base_pelo(E, src_v47, piel_extra=None):
    """Datos para un PeloOrilla como el de V48.3 (pelo de V47 como guía, piel actual): cuero y cortes salen de ahí."""
    from copox.medicion import pelo_cascara as pc
    from copox.medicion import rostro_edicion as re
    E47 = re.Editor(src_v47)
    R = v39._leer(E47, _prims(E47)[v482.PELO[0]], "POSITION").astype(float)
    P = _prims(E)
    S0 = v39._leer(E, P[v482.PIEL], "POSITION").astype(float); N0 = v39._leer(E, P[v482.PIEL], "NORMAL").astype(float)
    sel = (np.abs(S0[:, 0]) <= 0.133) & (S0[:, 1] > 0.47)
    S, N = S0[sel], N0[sel]
    if piel_extra is not None:
        S, N = np.vstack([S, piel_extra[0]]), np.vstack([N, piel_extra[1]])
    return pc, R, S, N


def _pesos_cabeza(E, V):
    from scipy.spatial import cKDTree
    q = _prims(E)[v482.PELO[0]]
    Rv = v39._leer(E, q, "POSITION").astype(float)
    _, k = cKDTree(Rv).query(V)
    return v39._leer(E, q, "JOINTS_0")[k].astype(np.uint16), v39._leer(E, q, "WEIGHTS_0")[k].astype(np.float32)


def cuero_cabelludo(E, src_v47, carpeta):
    """Superficie implícita lisa (misma técnica que el pelo de V48.3) CUERO mm bajo la cara del pelo; en la orilla se
    hunde bajo la piel (ras negativo): sin labio ni rendija, y tapa la piel escondida que dejaba ver un pelo corto."""
    import receta_adan_v36 as v36
    pc, R, S, N = _base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N, ras=-0.0010, cubre=0.0)
    H.Rd = H.Rd - CUERO
    V, T = H.malla(paso=v483.PASO_PELO)
    V, T = v36.simplificar(V, T, TRIS["cuero"], carpeta)
    Nv = H.normales(V)
    T = _orientar(V, T, Nv)
    J, W = _pesos_cabeza(E, V)
    mat = _prims(E)["Torso_PIEL"]["material"]
    _al_cuerpo(E, v41._prim_nueva(E, V, T, Nv, J, W, mat, "CueroCabelludo_PIEL"))
    E._cuero = (V, Nv)
    _limpiar(carpeta)
    return {"operacion": "cuero cabelludo", "tris": int(len(T))}


# 3 ── tenis (pie con tenis) ───────────────────────────────────────────────────────────────────────────────────────
class _Tenis:
    def __init__(self, pie):
        """pie: vértices del pie/tobillo (y < collar) de una pierna."""
        t = TENIS
        lo, hi = pie.min(0), pie.max(0)
        self.cx, self.cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        self.a = (hi[0] - lo[0]) / 2 + t["holgura_x"]; self.b = (hi[2] - lo[2]) / 2 + t["holgura_z"]
        zs = np.linspace(lo[2] - t["holgura_z"], hi[2] + t["holgura_z"], 40)
        h = np.array([pie[np.abs(pie[:, 2] - z) < 0.012, 1].max() if (np.abs(pie[:, 2] - z) < 0.012).any() else 0
                      for z in zs]) + t["sobre_pie"]
        h = np.clip(h, t["punta"], t["collar"])
        h = np.convolve(np.r_[h[:5], h, h[-5:]], np.ones(11) / 11, mode="valid")
        self.zs, self.h = zs, h

    def sdf(self, P):
        t = TENIS
        dx = np.abs(P[:, 0] - self.cx) / self.a; dz = np.abs(P[:, 2] - self.cz) / self.b
        k = (dx ** t["n"] + dz ** t["n"]) ** (1 / t["n"])
        d2 = (k - 1) * min(self.a, self.b)
        top = np.interp(P[:, 2], self.zs, self.h)
        from copox.medicion.ropa_ajustada import smin
        d = -smin(-d2, -(P[:, 1] - top), t["redondeo"])              # empeine y orillas de arriba redondeadas
        return -smin(-d, P[:, 1], 0.003)                             # suela apoyada en y = 0 (el pie no se ve)


def tenis(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import short_geo as sg
    nombres, _ = v40.v38_skin(E)
    m_suela = v41._material(E, "TENIS_SUELA", COLOR_SUELA)
    m_corte = v41._material(E, "TENIS_CORTE", COLOR_TENIS)
    prims, log = [], {"operacion": "tenis"}
    for lado, pz in (("L", "PiernaL_PIEL"), ("R", "PiernaR_PIEL")):
        P = _pieza(E, pz)
        Vp = P.V0[P.V0[:, 1] < TENIS["collar"]]
        S = _Tenis(Vp)
        dentro = S.sdf(Vp)
        lo = np.array([S.cx - S.a - 0.01, -0.01, S.cz - S.b - 0.01])
        hi = np.array([S.cx + S.a + 0.01, TENIS["collar"] + 0.01, S.cz + S.b + 0.01])
        V, T = sg.malla_sdf(S.sdf, lo, hi, paso=0.0010, pulido=8)
        V, T = v36.simplificar(V, T, TRIS["tenis"], carpeta)
        N = _normales_sdf(S.sdf, V)
        T = _orientar(V, T, N)
        V, T, arriba = sg.partir_plano(V, T, TENIS["corte_suela"])
        N = mg.normales(V, T)
        J4, W4 = ra.pesos_por_piel_visible(V, [P], len(nombres))
        for sel, mat, nm in ((~arriba, m_suela, f"Tenis{lado}_SUELA"), (arriba, m_corte, f"Tenis{lado}_CORTE")):
            Ts = T[sel]; u = np.unique(Ts); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
            prims.append(v41._prim_nueva(E, V[u], mp[Ts], N[u], J4[u], W4[u], mat, nm))
        log[lado] = {"tris": int(len(T)), "pie_fuera_mm": round(float(max(dentro.max(), 0)) * 1000, 2)}
    _nodo(E, "PIES_TENIS", prims)
    _limpiar(carpeta)
    return log


# 3b ── pies separados (intercambiables con los tenis) ─────────────────────────────────────────────────────────────
Y_TOBILLO = 0.045


def pies_aparte(E):
    """Los triángulos del pie (centro bajo Y_TOBILLO) pasan de la pierna a un nodo PIES_DESCALZOS, oculto por defecto:
    con tenis puestos el pie no existe (pieza "pie con tenis"); descalzo se muestra el pie y se ocultan los tenis."""
    from copox.medicion.gltf import accesor
    import receta_adan_v24 as v24
    prims, log = [], {"operacion": "pies aparte"}
    for pz in ("PiernaL_PIEL", "PiernaR_PIEL"):
        q = _prims(E)[pz]
        T = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
        V = v39._leer(E, q, "POSITION").astype(float)
        pie = V[T].mean(1)[:, 1] < Y_TOBILLO
        u = np.unique(T[pie]); mp = -np.ones(len(V), np.int64); mp[u] = np.arange(len(u))
        N = v39._leer(E, q, "NORMAL"); J = v39._leer(E, q, "JOINTS_0"); W = v39._leer(E, q, "WEIGHTS_0")
        prims.append(v41._prim_nueva(E, V[u], mp[T[pie]], N[u], J[u].astype(np.uint16), W[u].astype(np.float32),
                                     q["material"], pz.replace("Pierna", "Pie")))
        q["indices"] = v24._add_raw(E, np.ascontiguousarray(T[~pie].ravel(), np.uint32), 5125, "SCALAR", 34963)
        E.b = bytes(E.out)
        log[pz] = int(pie.sum())
    _nodo(E, "PIES_DESCALZOS", prims, visible=False)
    return log


# 4 ── pelo corto intercambiable ───────────────────────────────────────────────────────────────────────────────────
def pelo_corto(E, src_v47, carpeta):
    import receta_adan_v36 as v36
    pc, R, S, N = _base_pelo(E, src_v47)            # sin el cuero en la piel: el corte termina en un canto limpio sobre él
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    c = CORTE
    D = H.D; el = np.degrees(np.arcsin(np.clip(D[:, 1], -1, 1))); az = np.degrees(np.arctan2(D[:, 0], D[:, 2]))
    H.Rd = H.Rd + c["lados"] + (c["volumen"] - c["lados"]) * _ss((el - 25) / 40)
    y_dir = H.c[1] + D[:, 1] * H.Rd
    atras = _ss((np.abs(az) - 100) / 40)
    y_corte = c["lados_y"] + (c["nuca_y"] - c["lados_y"]) * atras
    frente = _ss((c["frente_az"] + 20 - np.abs(az)) / 20)          # al frente el nacimiento queda como estaba
    H.Md = H.Md * np.maximum(frente, _ss((y_dir - y_corte) / 0.012))
    V, T = H.malla(paso=v483.PASO_PELO)
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS["pelo_corto"], carpeta)
    Nv = H.normales(V)
    T = _orientar(V, T, Nv)
    J, W = _pesos_cabeza(E, V)
    mat = _prims(E)[v482.PELO[0]]["material"]
    _nodo(E, "CAPA_PELO_CORTO", [v41._prim_nueva(E, V, T, Nv, J, W, mat, "PELO_CORTO")], junto_a="CAPA_GUIA_CAPILAR",
          visible=False)
    _limpiar(carpeta)
    return {"operacion": "pelo corto intercambiable", "tris_marching": int(n0), "tris": int(len(T))}


# 5 ── pelo por mechones estilo ALTH-META ─────────────────────────────────────────────────────────────────────────
# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm). Hoja de Theo: volumen arriba, copete que barre a su
# izquierda, mechones anchos que bajan a sienes y nuca; raíz ancha, punta suave (skill vestuario-cabello §5).
MECHONES_ALTH = [
    (-50, 72, -26, 17, 46, 12), (-25, 78, 2, 13, 50, 13), (2, 78, 30, 15, 48, 12), (28, 74, 52, 19, 44, 11),
    (50, 68, 72, 24, 40, 10),
    (75, 60, 100, 8, 44, 11), (105, 55, 116, 0, 40, 10), (-75, 60, -100, 8, 44, 11), (-105, 55, -116, 0, 40, 10),
    (-58, 64, -80, 16, 40, 10),
    (140, 65, 150, -20, 48, 12), (165, 66, 172, -27, 50, 12), (-165, 66, -172, -27, 50, 12), (-140, 65, -150, -20, 48, 12),
    (120, 55, 128, -10, 40, 10), (-120, 55, -128, -10, 40, 10),
    (0, 88, 140, 64, 46, 14), (60, 85, 175, 58, 44, 13), (-60, 85, -175, 58, 44, 13), (0, 86, -150, 62, 44, 13),
]
FACETAS = True


def _facetado(V, T):
    """Sombreado plano (como las facetas de la hoja de Theo): un vértice por esquina con la normal de su cara."""
    P = V[T].reshape(-1, 3)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return P, np.arange(len(P)).reshape(-1, 3), np.repeat(fn, 3, axis=0)


def pelo_mechones(E, src_v47, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import pelo_mechones as pm
    pc, R, S, N = _base_pelo(E, src_v47)
    H = pc.PeloOrilla(v483.CENTRO, R, S, N)
    M = pm.PeloMechones(H, mechones=MECHONES_ALTH, escala=1.0, levanta=0.8, k_mechon=0.007, k_union=0.005)
    V, T = M.malla(paso=0.0012)
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS["mechones"], carpeta)
    Nv = M.normales(V)
    T = _orientar(V, T, Nv)
    if FACETAS:
        V, T, Nv = _facetado(V, T)
    J, W = _pesos_cabeza(E, V)
    mat = _prims(E)[v482.PELO[0]]["material"]
    _nodo(E, "CAPA_PELO_MECHONES", [v41._prim_nueva(E, V, T, Nv, J, W, mat, "PELO_MECHONES")],
          junto_a="CAPA_GUIA_CAPILAR", visible=False)
    _limpiar(carpeta)
    return {"operacion": "pelo por mechones ALTH", "tris_marching": int(n0), "tris": int(len(T))}


def main(src, src_v47, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    carpeta = os.path.dirname(os.path.abspath(dst))
    log = [pelvis(E, carpeta), cuero_cabelludo(E, src_v47, carpeta), tenis(E, carpeta), pies_aparte(E), pelo_corto(E, src_v47, carpeta),
           pelo_mechones(E, src_v47, carpeta)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V49: pelvis, cuero cabelludo, tenis y pelo corto intercambiables. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], sys.argv[3]):
        print(x)
