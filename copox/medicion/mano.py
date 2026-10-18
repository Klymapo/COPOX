"""SENKU · mano contra la referencia con regla (refs/infografias/mano-con-regla.jpg).

Todo en razones (sin unidades), medido en pose T (palma abajo, dedos sobre ±x) y en la imagen de la regla
(palma de frente, dedos hacia arriba). Landmarks leídos sobre rejilla de 25 px (68.2 px/cm), error ≈ ±10 px:
  muñeca y = 760 · membranas y = 420 / 430 / 460 · puntas: índice 178, medio 122, anular 178, meñique 270
  palma ancho (nudillos) 345 px · ancho de dedo ≈ 80 px · huecos en la base ≈ 12 px
  pulgar: base (240, 650) → punta (60, 460): 262 px, 43° respecto a los dedos
Largo de dedo = de su membrana a la punta. Largo de palma = de la muñeca a la membrana media.
"""
from __future__ import annotations
import numpy as np

REF = {
    "dedo_medio/palma": 308 / 325,
    "ancho_palma/largo_palma": 345 / 325,
    "ancho_dedo/ancho_palma": 80 / 345,
    "hueco/ancho_palma": 12 / 345,
    "indice/medio": 242 / 308,
    "anular/medio": 267 / 308,
    "menique/medio": 190 / 308,
    "pulgar/palma": 262 / 325,
    "pulgar_angulo": 43.0,
}
TOL = {"pulgar_angulo": 12.0}
TOL_REL = 0.15            # ±15 % en razones


def _piezas(m, lado="Left"):
    j = m.j
    nm = [j["nodes"][k]["name"] for k in j["skins"][0]["joints"]]
    out = {}
    for p in m.prims:
        if p.joints is None or len(p.pos) > 400:
            continue
        dom = {nm[d] for d in np.unique(p.joints[np.arange(len(p.pos)), p.weights.argmax(1)])}
        for dedo in ("Index", "Middle", "Ring", "Little", "Thumb"):
            if lado + dedo + "Distal" in dom:
                out[dedo] = p.pos
        if dom == {lado + "Hand", lado + "LowerArm"} and np.abs(p.pos[:, 0]).min() > 0.29:
            out["palma"] = p.pos
    I = {n: i for i, n in enumerate(nm)}
    from .gltf import accesor
    ibm = accesor(j, m.b, j["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    H = {n: np.linalg.inv(ibm[I[n]])[:3, 3] for n in nm}
    return out, H


def medir(m, lado="Left"):
    pz, H = _piezas(m, lado)
    s = 1.0 if lado == "Left" else -1.0
    x = lambda P: s * P[:, 0]
    muneca = s * H[lado + "Hand"][0]
    # membrana: donde cada dedo sale de la palma = borde de la palma a la altura de ese dedo
    palma = pz["palma"]
    web = {}
    for d in ("Index", "Middle", "Ring", "Little"):
        z0, z1 = pz[d][:, 2].min(), pz[d][:, 2].max()
        cerca = palma[(palma[:, 2] > z0) & (palma[:, 2] < z1)]
        web[d] = float(x(cerca).max()) if len(cerca) else float(x(pz[d]).min())
    largo = {d: float(x(pz[d]).max() - web[d]) for d in web}
    largo_palma = web["Middle"] - muneca
    # anchos a media altura del dedo
    anchos, rangos = {}, {}
    for d in web:
        P = pz[d]; xm = web[d] + largo[d] * 0.5
        sec = P[np.abs(x(P) - xm) < 0.3 * largo[d]]
        rangos[d] = (sec[:, 2].min(), sec[:, 2].max())
        anchos[d] = float(rangos[d][1] - rangos[d][0])
    zs = sorted(rangos.values())
    huecos = [zs[i + 1][0] - zs[i][1] for i in range(3)]
    ancho_palma = float(max(r[1] for r in rangos.values()) - min(r[0] for r in rangos.values()))
    # pulgar: de su base (hueso metacarpo) a la punta de la pieza distal
    T = pz["Thumb"]; base = H[lado + "ThumbMetacarpal"]
    punta = T[np.argmax(np.linalg.norm(T - base, axis=1))]
    v = punta - base; L_pulgar = float(np.linalg.norm(v))
    ang = float(np.degrees(np.arccos(abs(s * v[0]) / L_pulgar)))
    return {
        "dedo_medio/palma": largo["Middle"] / largo_palma,
        "ancho_palma/largo_palma": ancho_palma / largo_palma,
        "ancho_dedo/ancho_palma": float(np.mean(list(anchos.values()))) / ancho_palma,
        "hueco/ancho_palma": float(np.mean(huecos)) / ancho_palma,
        "indice/medio": largo["Index"] / largo["Middle"],
        "anular/medio": largo["Ring"] / largo["Middle"],
        "menique/medio": largo["Little"] / largo["Middle"],
        "pulgar/palma": L_pulgar / largo_palma,
        "pulgar_angulo": ang,
        "_u": {"largo_palma": largo_palma, "ancho_palma": ancho_palma, "largos": largo, "huecos": huecos, "anchos": anchos},
    }


def comparar(m, lado="Left"):
    r = medir(m, lado)
    filas = []
    for k, ref in REF.items():
        v = r[k]
        ok = abs(v - ref) <= TOL[k] if k in TOL else abs(v - ref) <= TOL_REL * ref
        filas.append({"medida": k, "modelo": round(v, 3), "ref": round(ref, 3), "ok": bool(ok)})
    return filas, r["_u"]
