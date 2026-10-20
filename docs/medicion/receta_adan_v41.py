"""Adán V41 (sobre V40): manos corregidas por la revisión de V40 y short nuevo de una pieza (parte inferior, etapa 1).

Pedido de Admin (18 oct 2026): "Corrige lo del revisor y pasamos a parte inferior del cuerpo".
- Manos (en copox/medicion/mano_bloques.py y receta_adan_v40.py): dedos-bloque más cortos y gruesos, casi sin ranura;
  la mano toma el perfil del anillo del antebrazo cerca de la costura (sin escalón) y la losa de la palma entra al tubo
  de la muñeca (sin línea en el dorso).
- Short (copox/medicion/short_geo.py): una pieza implícita en lugar de torso+perneras encimadas (quitaba la "solapa"
  del frente), entrepierna estrecha como la hoja, pretina más oscura y cordón al frente. Colores de la paleta:
  azul_desaturado/2 #4F6D9A (short), azul_desaturado/3 #3B5475 (pretina), medidos/cabello_blanco #DDDDE7 (cordón).
Uso: GODOT_BIN=… python receta_adan_v41.py ADAN_V22_HABLA.glb ADAN_V41.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402

COLOR_SHORT, COLOR_PRETINA, COLOR_CORDON = "#4F6D9A", "#3B5475", "#DDDDE7"
PRETINA = 0.018               # u: alto de la pretina (hoja de piernas: ~1/8 del short)
RESALTE_PRETINA = 0.0012      # u: la pretina sobresale un poco del short (la hoja la marca con un escalón leve)
HOLGURA_CINT = 1.31           # medio ancho del short en la cintura ÷ el del torso (hoja de piernas)
CADERA = (0.140, 0.092, 0.022)          # medio ancho, medio fondo y centro z en la entrepierna
DOBLADILLO = (0.144, 0.088, 0.024)      # en el dobladillo (la pierna mide hasta x 0.1385)
MUESCA = 0.024                          # medio ancho de la muesca de la entrepierna en el dobladillo (la pierna empieza en x 0.0375)
TRIS_SHORT = 4200


from copox.medicion.glb_util import lineal as _lineal  # noqa: E402,F401  (movido a la librería)


from copox.medicion.glb_util import material as _material  # noqa: E402,F401  (movido a la librería)


from copox.medicion.glb_util import prim_nueva as _prim_nueva  # noqa: E402,F401  (movido a la librería)


from copox.medicion.glb_util import pesos_short  # noqa: E402,F401  (movido a la librería)


def short(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import short_geo as sg
    from copox.medicion import torso_geo as tg
    nombres, _ = v40.v38_skin(E)
    viejas = [p for m in E.j["meshes"] for p in m["primitives"] if "SHORT_AZUL" in str(p.get("extras", {}).get("pieza"))]
    malla_short = [m for m in E.j["meshes"] if any(p in viejas for p in m["primitives"])][0]
    Vt = v39._leer(E, v39._prims(E, "Torso_SHORT_AZUL")[0], "POSITION").astype(float)
    Vp = v39._leer(E, v39._prims(E, "PiernaL_SHORT_AZUL")[0], "POSITION").astype(float)
    y_cint, y_dob = float(Vt[:, 1].max()), float(Vp[:, 1].min())
    y_ent = float(Vt[np.abs(Vt[:, 0]) < 0.01, 1].min())
    T0 = tg.Torso(v39.PERFIL, v39.EXPONENTE)
    a, b, c = [float(np.ravel(v)[0]) for v in T0.seccion(np.array([y_cint]))]
    S = sg.Short(y_cint + 0.0025, y_ent, y_dob - 0.0025, (a * HOLGURA_CINT, b + 0.010, c), CADERA, DOBLADILLO, MUESCA,
                 boca=(a + 0.004, b + 0.004, c), alto_boca=0.005)
    V, T = S.malla()
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS_SHORT, carpeta)
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    V, T = sg.recortar(V, T, y_dob - 0.0025, y_cint + 0.0025)     # bocas por plano exacto: dobladillo sin picos
    fuentes = [(v39._leer(E, q, "POSITION").astype(float), v39._leer(E, q, "JOINTS_0").astype(int),
                v39._leer(E, q, "WEIGHTS_0").astype(float)) for q in viejas]
    # pretina: la malla se parte por un plano exacto y las caras de arriba van con su material
    V, T, arriba = sg.partir_plano(V, T, y_cint - PRETINA)
    N = mg.normales(V, T)
    J4, W4 = tg.transferir_pesos(V, T, fuentes, len(nombres), suavizado=6)
    J4, W4 = pesos_short(V, nombres, y_ent, y_cint)
    m_short = _material(E, "ADAN_SHORT_AZUL", COLOR_SHORT)
    m_pret = _material(E, "ADAN_SHORT_PRETINA", COLOR_PRETINA)
    m_cord = _material(E, "ADAN_CORDON", COLOR_CORDON)
    prims = []
    for sel, mat, pz in ((~arriba, m_short, "Short_AZUL"), (arriba, m_pret, "Short_PRETINA")):
        Ts = T[sel]; u = np.unique(Ts); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
        Vs = V[u].copy()
        if pz == "Short_PRETINA":                                # sobresale arriba del borde (el borde queda cosido)
            f = np.clip((Vs[:, 1] - (y_cint - PRETINA)) / 0.003, 0, 1)
            Vs += N[u] * (RESALTE_PRETINA * f)[:, None]
        Ns = mg.normales(Vs, mp[Ts]) if pz == "Short_PRETINA" else N[u]
        prims.append(_prim_nueva(E, Vs, mp[Ts], Ns, J4[u], W4[u], mat, pz))
    # cordón: al frente, bajo el borde de la cintura
    yk = y_cint - PRETINA * 0.55
    zs = np.linspace(c, c + 0.2, 4001)
    dz = S.sdf(np.stack([np.zeros_like(zs), np.full_like(zs, yk), zs], 1))
    z_frente = float(zs[np.argmax(dz > 0)])
    f, lo, hi = sg.cordon(yk, z_frente + 0.0012)
    Vc, Tc = sg.malla_sdf(f, lo, hi)
    Vc, Tc = v36.simplificar(Vc, Tc, 700, carpeta)
    Nc = mg.normales(Vc, Tc)
    Jc = np.zeros((len(Vc), 4), np.uint16); Jc[:, 0] = nombres.index("Hips")
    Wc = np.zeros((len(Vc), 4), np.float32); Wc[:, 0] = 1
    prims.append(_prim_nueva(E, Vc, Tc, Nc, Jc, Wc, m_cord, "Short_CORDON"))
    ntar = max(len(p.get("targets", [])) for p in viejas)
    malla_short["primitives"] = [p for p in malla_short["primitives"] if p not in viejas] + prims
    if ntar:
        for p in malla_short["primitives"]:
            nv = E.j["accessors"][p["attributes"]["POSITION"]]["count"]
            ceros = E._add(np.zeros((nv, 3), np.float32), "VEC3", None, True)
            p["targets"] = p.get("targets") or [{"POSITION": ceros} for _ in range(ntar)]
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return {"operacion": "short de una pieza", "tris_marching": int(n0), "tris_short": int(len(T)),
            "tris_cordon": int(len(Tc)), "cintura_u": round(y_cint, 4), "entrepierna_u": round(y_ent, 4),
            "dobladillo_u": round(y_dob, 4), "pretina_tris": int(arriba.sum())}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    t40 = dst + ".v40.glb"
    log = v40.main(src, t40)
    E = re.Editor(t40)
    log.append(short(E, os.path.dirname(os.path.abspath(dst))))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V41: manos corregidas y short de una pieza. SIN APROBAR.")
    compactar(tmp, dst)
    for f in (t40, tmp):
        os.remove(f)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-3:]:
        print(x)
