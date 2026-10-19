"""Adán V48.3 (sobre V47): cáscara del pelo nueva, nuca lisa y frente recta hasta la sien.

V48.2 no se aprobó (19 oct 2026): la terraza del pelo seguía y la visera apenas cambió. Admin aprobó cambiar de técnica
("Me sirve así", pelo liso por ahora):
1. Nuca: la piel bajo la orilla del pelo se alisa (Taubin, sin encoger) para que la cabeza cierre en una curva hacia
   el cuello, sin masa. El cuello no se toca.
2. Pelo (copox/medicion/pelo_cascara.py): cáscara rehecha con la envolvente radial suavizada de la vieja, con un piso de
   piel + 1.8 mm. Sin terraza ni motas; misma silueta y misma orilla que V47.
3. Frente: recta de y 0.674 (sobre los párpados) a 0.740, ahora hasta la sien (|x| < 0.128, antes 0.115). Las cejas se
   mueven con la piel.
Cara, ojos, boca, nariz, orejas y forma general: los de V47.
Uso: python receta_adan_v48_3.py ADAN_V47.glb ADAN_V48_3.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v48_2 as v482  # noqa: E402

CENTRO = (0.0, 0.665, -0.006)
FRENTE = dict(y0=0.674, y1=0.740, x_max=0.128)
NUCA_ALISADO = 30


def _prims(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}


def nuca_piel(E):
    from copox.medicion.gltf import accesor
    from copox.medicion.mano_geo import taubin
    p = _prims(E)[v482.PIEL]
    V = v39._leer(E, p, "POSITION").astype(float)
    T = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
    _, inv = np.unique(np.round(V, 6), axis=0, return_inverse=True); inv = inv.ravel()
    Vw = np.zeros((inv.max() + 1, 3)); Vw[inv] = V
    Tw = inv[T]
    e = np.sort(np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    borde = np.zeros(len(Vw), bool); borde[np.unique(u[c == 1])] = True
    S = taubin(Vw, Tw, NUCA_ALISADO)
    y, z, x = Vw[:, 1], Vw[:, 2], np.abs(Vw[:, 0])
    ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))      # noqa: E731
    w = ss((0.60 - y) / 0.03) * ss((-0.01 - z) / 0.03) * ss((y - 0.495) / 0.015) * ss((0.134 - x) / 0.006) * ~borde
    V1 = (Vw + (S - Vw) * w[:, None])[inv]
    return {"operacion": "nuca: piel alisada", "movidos": v482._escribir(E, p, V, V1)}


TRIS_PELO = 12000
PASO_PELO = 0.0011
ORILLA_PULIDO = 25


def pelo(E, carpeta):
    """Pelo con malla NUEVA (pelo_cascara.PeloImplicito): reemplaza la primitiva RELLENO; CONTORNO y la piel escondida
    se meten debajo del pelo nuevo. Pesos: los del vértice más cercano del pelo viejo."""
    import receta_adan_v36 as v36
    import receta_adan_v41 as v41
    from scipy.spatial import cKDTree
    from copox.medicion import pelo_cascara as pc
    P = _prims(E)
    viejo = P[v482.PELO[0]]
    R = v39._leer(E, viejo, "POSITION").astype(float)
    J = v39._leer(E, viejo, "JOINTS_0").astype(int); W = v39._leer(E, viejo, "WEIGHTS_0").astype(float)
    S0 = v39._leer(E, P[v482.PIEL], "POSITION").astype(float)
    N0 = v39._leer(E, P[v482.PIEL], "NORMAL").astype(float)
    sel = (np.abs(S0[:, 0]) <= 0.133) & (S0[:, 1] > 0.47)
    H = pc.PeloOrilla(CENTRO, R, S0[sel], N0[sel])
    E._pelo = H
    V, T = H.malla(paso=PASO_PELO)
    n0 = len(T)
    # orilla sin dientes: Taubin extra solo en la franja del borde (máscara 0.5–0.62), antes de simplificar
    from copox.medicion.mano_geo import taubin
    _, Mv = H.techo(V)
    w = np.clip((0.62 - Mv) / 0.06, 0, 1); w = w * w * (3 - 2 * w)
    V = V + (taubin(V, T, ORILLA_PULIDO) - V) * w[:, None]
    V, T = v36.simplificar(V, T, TRIS_PELO, carpeta)
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    N = H.normales(V)
    _, k = cKDTree(R).query(V)
    nueva = v41._prim_nueva(E, V, T, N, J[k].astype(np.uint16), W[k].astype(np.float32), viejo["material"],
                            v482.PELO[0])
    malla = next(m for m in E.j["meshes"] if viejo in m["primitives"])
    malla["primitives"] = [q if q is not viejo else nueva for q in malla["primitives"]]
    E.b = bytes(E.out)
    log = {"operacion": "pelo: malla nueva", "tris_marching": int(n0), "tris": int(len(T))}
    # debajo del pelo nuevo: la franja del nacimiento (CONTORNO) y la piel escondida
    q = _prims(E)[v482.PELO[1]]                     # la franja vieja del nacimiento: ya la dibuja la orilla nueva
    S = v39._leer(E, q, "POSITION").astype(float)
    c = np.asarray(CENTRO)
    log["contorno_escondido"] = v482._escribir(E, q, S, c + (S - c) * 0.95)
    return log


BORDE = dict(hueco=0.0020, rampa=0.03, iter_=4, tope=0.003, banda=0.65)


def cerrar_bordes(E):
    """Bordes del pelo cerrados: la piel que queda debajo del pelo (y solo esa) se mete hasta quedar `hueco` bajo la
    cara exterior del pelo. Afuera del pelo no se mueve nada; la orilla ya no comparte plano con la piel."""
    H = E._pelo
    q = _prims(E)[v482.PIEL]
    S = v39._leer(E, q, "POSITION").astype(float)
    N = v39._leer(E, q, "NORMAL").astype(float)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    cand = np.where((np.abs(S[:, 0]) <= 0.14) & (S[:, 1] > 0.47))[0]
    S1 = S.copy()
    for _ in range(BORDE["iter_"]):
        a, M = H.techo(S1[cand])
        w = np.clip((M - 0.5) / BORDE["rampa"], 0, 1); w = w * w * (3 - 2 * w)
        w *= np.clip((BORDE["banda"] - M) / 0.05, 0, 1)                 # solo la franja de la orilla
        S1[cand] -= N[cand] * (np.maximum(a + BORDE["hueco"], 0) * w)[:, None]
        D = S1 - S; L = np.linalg.norm(D, axis=1)                     # nunca más de `tope` mm
        S1 = S + D * np.minimum(1, BORDE["tope"] / np.maximum(L, 1e-12))[:, None]
    _, inv = np.unique(np.round(S, 6), axis=0, return_inverse=True); inv = inv.ravel()
    Sw = np.zeros((inv.max() + 1, 3)); Sw[inv] = S1                     # costuras soldadas: misma posición
    S1 = Sw[inv]
    return {"operacion": "bordes del pelo cerrados", "piel_metida": v482._escribir(E, q, S, S1),
            "max_mm": round(float(np.abs(S1 - S).max()) * 1000, 2)}


def frente(E):
    from copox.medicion import bultos_cabeza as bc
    f0 = bc.frente_recta
    bc.frente_recta = lambda piel, **kw: f0(piel, **{**FRENTE, **kw})          # noqa: E731
    try:
        log = v482.bultos.__wrapped__(E) if hasattr(v482.bultos, "__wrapped__") else _solo_frente(E, bc)
    finally:
        bc.frente_recta = f0
    return log


def _solo_frente(E, bc):
    from scipy.interpolate import LinearNDInterpolator
    mat = {i: m["name"] for i, m in enumerate(E.j["materials"])}
    p = _prims(E)[v482.PIEL]
    S = v39._leer(E, p, "POSITION").astype(float)
    S1 = bc.frente_recta(S)(S)
    dz = S1[:, 2] - S[:, 2]
    m = np.abs(dz) > 1e-7
    log = {"operacion": "frente recta hasta la sien", "piel": v482._escribir(E, p, S, S1),
           "max_mm": round(float(-dz.min()) * 1000, 2)}
    if m.any():
        D = LinearNDInterpolator(S[m][:, :2], dz[m], fill_value=0.0)
        n = 0
        for mm in E.j["meshes"]:
            for q in mm["primitives"]:
                nombre = mat[q["material"]]
                pz = q.get("extras", {}).get("pieza") or ""
                if q is p or pz.startswith(("PARPADO", "Ojo", "BORDE")) or not ("CEJA" in nombre or "PIEL" in nombre):
                    continue
                V = v39._leer(E, q, "POSITION").astype(float)
                cerca = (V[:, 2] > 0.06) & (np.abs(V[:, 0]) < 0.15) & (V[:, 1] > 0.66) & (V[:, 1] < 0.75)
                if not cerca.any():
                    continue
                V1 = V.copy(); V1[cerca, 2] += D(V[cerca, :2])
                n += v482._escribir(E, q, V, V1)
        log["otras_piezas"] = n
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    carpeta = os.path.dirname(os.path.abspath(dst))
    log = [nuca_piel(E), frente(E), pelo(E, carpeta), cerrar_bordes(E)]
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    E.b = bytes(E.out)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V48.3: cáscara del pelo nueva, nuca lisa, frente recta. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
