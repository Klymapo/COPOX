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


def pelo(E):
    from copox.medicion import pelo_cascara as pc
    P = _prims(E)
    S = v39._leer(E, P[v482.PIEL], "POSITION").astype(float)
    orejas = np.abs(S[:, 0]) > 0.133
    nariz = (np.abs(S[:, 0]) < 0.03) & (S[:, 1] > 0.56) & (S[:, 1] < 0.635) & (S[:, 2] > 0.14)
    from copox.medicion.gltf import accesor
    R = v39._leer(E, P[v482.PELO[0]], "POSITION").astype(float)
    C = v39._leer(E, P[v482.PELO[1]], "POSITION").astype(float)
    T = accesor(E.j, E.b, P[v482.PELO[0]]["indices"]).reshape(-1, 3).astype(np.int64)
    R1, C1 = pc.rehacer(R, C, S[~orejas & ~nariz], CENTRO, T=T)
    S1, n_piel = pc.meter_piel(S, R1, CENTRO)
    v482._escribir(E, P[v482.PIEL], S, S1)
    return {"operacion": "pelo: cáscara nueva", "relleno": v482._escribir(E, P[v482.PELO[0]], R, R1),
            "contorno": v482._escribir(E, P[v482.PELO[1]], C, C1), "piel_metida": n_piel,
            "max_mm": round(float(np.linalg.norm(R1 - R, axis=1).max()) * 1000, 1)}


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
    log = [nuca_piel(E), frente(E), pelo(E)]
    E.b = bytes(E.out)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V48.3: cáscara del pelo nueva, nuca lisa, frente recta. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
