"""Adán V44 (sobre V43.1): manos como la hoja del brazo (dedos largos en abanico, pulgar abierto, dorso sin línea).

Pedido de Admin (18 oct 2026), Martillo tras revisar las manos de V43.1.
Medidas en refs/personajes/adan/adan-brazo-4-vistas.jpg (px de la hoja):
- FRONT: dedos de 55–58 de ancho; ranura de ~4 en la base que se abre a ~16 en la punta (abanico); dedos al largo de la
  hoja (V40–V43 los tenían al 86 %, "más cortos y gruesos" por una revisión de V40).
- SIDE: grueso del dedo ~0.85 de su ancho (V43: 0.92); la palma no es más delgada que la de V43, así que no cambia.
- Pulgar más abierto (~40° como la hoja; V43: 32°).
- Dorso: la línea salía donde termina el tubo de la muñeca, que acababa 12 % más grueso que la palma y un poco más arriba.
  Ahora el tubo termina con la sección exacta de la palma en ese punto (mismo centro y radios): no hay borde.
Lo demás es V43.1: pose de cada mano (abierta, puño, señalar), costura con el anillo del antebrazo, pesos, y puño y
señalar ocultos por defecto (KHR_node_visibility).
Uso: GODOT_BIN=… python receta_adan_v44.py ADAN_V43_1.glb ADAN_V44.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402

ESTILO = {"largo_dedo": 1.0, "grueso_dedo": 0.85, "separacion": 5, "pulgar_ang": 40.0}
ABANICO = {"Index": -5.0, "Middle": 0.0, "Ring": 4.0, "Little": 9.0}   # grados; la ranura se abre hacia la punta


def _poses():
    from copox.medicion import mano_bloques as mb
    P = {k: dict(v) for k, v in mb.POSES.items()}
    P["abierta"]["abanico"] = ABANICO
    return P


def _tubo_a_palma(M, x1=0.030):
    """Sección de la palma en x1 (centro y semiejes): el tubo de la muñeca termina exactamente ahí."""
    L, A, G = M.palma_largo, M.palma_ancho, M.grosor
    u = min(max(x1 / L, 0), 1); su = u * u * (3 - 2 * u)
    cu = M.e["cuna"]
    hh = G / 2 * (cu - (cu - 1) * su)
    hw = A / 2 * (0.78 + 0.22 * su)
    return [G / 2 - hh, M.w0], [hh, hw]


def mano(E, variante, lado, nombres, carpeta, poses):
    """Como receta_adan_v40.mano, con el estilo de V44 y el tubo de la muñeca acabando en la sección de la palma."""
    import receta_adan_v24 as v24
    import receta_adan_v36 as v36
    from copox.medicion import mano_bloques as mb
    from copox.medicion import mano_geo as mg
    s = 1.0 if lado == "Left" else -1.0
    _, H = v40.v38_skin(E)
    Wj = H[lado + "Hand"]
    RV, RN, RJ, RW = v40._anillo(E, lado)
    RVl = RV * [s, 1, 1]; RNl = RN * [s, 1, 1]
    x_ring = float(RVl[:, 0].mean())
    yc, zc = H[lado + "LowerArm"][1], H[lado + "LowerArm"][2]
    r0 = [float(np.abs(RVl[:, 1] - yc).max()), float(np.abs(RVl[:, 2] - zc).max())]
    largo = 0.1306 * v40.ESCALA_MANO
    M = mb.ManoBloques(largo, poses[variante], palma_w0=-0.0035 * v40.ESCALA_MANO, estilo=ESTILO)
    c1, r1 = _tubo_a_palma(M)
    M.muneca = {"x0": x_ring - v40.ENTRA - Wj[0] * s, "x1": 0.030, "c0": [yc - Wj[1], zc - Wj[2]], "r0": r0,
                "c1": c1, "r1": r1}
    V, T = M.malla()
    V = V + np.array([Wj[0] * s, Wj[1], Wj[2]])
    V, T = v36.simplificar(V, T, v40.TRIS_MANO[variante], carpeta)
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    V, T = mb.cortar(V, T, x_ring + v40.CORTE)
    V, T, oa, base = mb.coser(V, T, RVl, (yc, zc), x_ring + v40.CORTE)
    V = mb.ajustar_boca(V, base, RVl, (yc, zc), x_ring + v40.CORTE)
    N = mg.normales(V, T)
    N[base:] = RNl[oa]
    ia, ih = nombres.index(lado + "LowerArm"), nombres.index(lado + "Hand")
    f = np.clip((V[:, 0] - x_ring) / (Wj[0] * s + v40.RAMPA_MUNECA - x_ring), 0, 1); f = f * f * (3 - 2 * f)
    J4 = np.zeros((len(V), 4), np.uint16); J4[:, 0] = ih; J4[:, 1] = ia
    W4 = np.zeros((len(V), 4), np.float32); W4[:, 0] = f; W4[:, 1] = 1 - f
    J4[base:] = RJ[oa]; W4[base:] = (RW[oa] / RW[oa].sum(1, keepdims=True))
    if lado == "Right":
        V = V * [-1, 1, 1]; N = N * [-1, 1, 1]; T = T[:, ::-1].copy()
        V[base:] = RV[oa]
    return {"attributes": {"POSITION": E._add(V.astype(np.float32), "VEC3", 34962, True),
                           "NORMAL": E._add(N.astype(np.float32), "VEC3", 34962),
                           "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(J4, np.uint16), 5123, "VEC4", 34962),
                           "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
            "indices": v24._add_raw(E, np.ascontiguousarray(T.ravel(), np.uint32), 5125, "SCALAR", 34963)}, \
        {"variante": variante, "lado": lado, "tris": int(len(T))}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    j = E.j
    nombres, _ = v40.v38_skin(E)
    poses = _poses()
    carpeta = os.path.dirname(os.path.abspath(dst))
    log = []
    for variante in v40.MANOS:
        for lado in ("Left", "Right"):
            malla = next(m for m in j["meshes"] if m.get("name") == f"MANO_{variante.upper()}_{lado[0]}")
            viejo = malla["primitives"][0]
            prim, info = mano(E, variante, lado, nombres, carpeta, poses)
            prim["material"] = viejo["material"]
            if "extras" in viejo:
                prim["extras"] = viejo["extras"]
            malla["primitives"] = [prim]
            log.append({"operacion": "mano V44", **info})
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V44: manos como la hoja del brazo. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
