"""SENKU · proporciones del cuerpo contra la Hoja de vistas (refs/infografias/hoja-de-vistas-personaje.png).

Todo se expresa en Hc = altura de la barbilla sobre el piso (Adán no tiene pelo; en la hoja el pelo tapa la
coronilla, la barbilla y la suela sí se ven). Landmarks de la hoja leídos en la vista de frente (píxeles y de la
imagen 1254×1254; suela y = 690, barbilla y = 350 → Hc = 340 px). Se leyeron a ojo sobre una rejilla de 10 px:
error ≈ ±5 px (±0.015 Hc). La hoja trae zapatos gruesos y pantalón: tobillo, rodilla y entrepierna son aproximados.

Las medidas del modelo salen del esqueleto en reposo (T) y de la pose Idle-loop t=0 (brazos abajo).
"""
from __future__ import annotations
import numpy as np

SUELA, BARBILLA = 690.0, 350.0
HC_PX = SUELA - BARBILLA

# alturas sobre la suela (px de la hoja) y largos (px)
HOJA = {
    "hombro_altura": 400,          # centro del hombro (articulación)
    "codo_altura": 468,
    "muneca_altura": 510,
    "mano_punta_altura": 568,      # parte baja del puño, brazos abajo
    "entrepierna_altura": 556,
}


# Decisiones de Admin (18 oct 2026): con los brazos abajo la mano llega a la entrepierna; brazo y antebrazo casi
# iguales (estilo chibi). El codo de la hoja queda bajo la manga doblada: su altura no se usa como meta.
RAZON_BRAZO_ANTEBRAZO = (0.9, 1.25)


def ref():
    r = {k: (SUELA - v) / HC_PX for k, v in HOJA.items()}
    # hombro → muñeca (brazo casi vertical en la vista de frente)
    r["hombro_muneca"] = (HOJA["muneca_altura"] - HOJA["hombro_altura"]) / HC_PX
    r["mano_hasta_entrepierna"] = r["mano_punta_altura"] - r["entrepierna_altura"]
    return r


def _huesos(sesion):
    from .gltf import accesor
    j = sesion.m.j
    sk = j["skins"][0]
    nm = [j["nodes"][k]["name"] for k in sk["joints"]]
    I = accesor(j, sesion.m.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return {n: np.linalg.inv(I[i])[:3, 3] for i, n in enumerate(nm)}


def _entrepierna(P):
    """Punto más bajo del cuerpo en el plano medio (x ≈ 0), entre las piernas."""
    m = (np.abs(P[:, 0]) < 0.006) & (P[:, 1] < 0.3) & (P[:, 1] > 0.05)
    return float(P[m, 1].min())


def medir(sesion, clip="Idle-loop"):
    from .rugosidad import piel_cara
    H = _huesos(sesion)
    g0 = sesion.geo(None, 0.0)
    cara = piel_cara(sesion) & (g0.P[:, 2] > 0.05)
    hc = float(g0.P[cara, 1].min())                       # barbilla = punto más bajo de la piel de la cara
    gi = sesion.geo(clip, 0.0)
    mano = sesion._region("mano_izq") | sesion._region("mano_der")
    lado = lambda s: (H[f"Left{s}"] + H[f"Right{s}"] * np.array([-1, 1, 1])) / 2
    m = {
        "hc_u": hc,
        "hombro_altura": float(lado("UpperArm")[1]) / hc,
        "brazo_largo": float(np.linalg.norm(H["LeftLowerArm"] - H["LeftUpperArm"])) / hc,
        "antebrazo_largo": float(np.linalg.norm(H["LeftHand"] - H["LeftLowerArm"])) / hc,
        "mano_punta_altura": float(gi.P[mano, 1].min()) / hc,
        "entrepierna_altura": _entrepierna(gi.P) / hc,
        "hombro_muneca": float(np.linalg.norm(H["LeftHand"] - H["LeftUpperArm"])) / hc,
        "rodilla_altura": float(lado("LowerLeg")[1]) / hc,
        "tobillo_altura": float(lado("Foot")[1]) / hc,
    }
    m["mano_hasta_entrepierna"] = m["mano_punta_altura"] - m["entrepierna_altura"]
    return m


def comparar(sesion, tol=0.03):
    m, r = medir(sesion), ref()
    filas = []
    for k in ("hombro_altura", "entrepierna_altura", "hombro_muneca", "mano_hasta_entrepierna"):
        d = m[k] - r[k]
        filas.append({"medida": k, "modelo": round(m[k], 3), "hoja": round(r[k], 3), "dif": round(d, 3),
                      "ok": abs(d) <= tol})
    rz = m["brazo_largo"] / m["antebrazo_largo"]
    filas.append({"medida": "brazo/antebrazo", "modelo": round(rz, 2), "hoja": "0.9–1.25 (decisión)", "dif": None,
                  "ok": RAZON_BRAZO_ANTEBRAZO[0] <= rz <= RAZON_BRAZO_ANTEBRAZO[1]})
    return filas, m
