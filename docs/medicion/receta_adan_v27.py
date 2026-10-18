"""Adán V27 (sobre V22 HABLA → V26): pesos de piel suaves en uniones de brazos, piernas, manos y dedos.

Hallazgo (SENKU · copox/movimiento/analizar.py + estiramiento por pieza):
  - Brazos (piezas de 226 vértices): con el brazo arriba (P15_3_Timido) las aristas del hombro se aplastaban
    a 1 % de su largo; pesos casi duros (57 % de vértices con un solo hueso).
  - Dedos: segmentos con peso 100 % a un solo hueso → pliegues que estiran ×2.5–2.9 en los nudillos.
  - Pieza del tobillo (y 0.03–0.07, debajo de la articulación) pesada a LowerLeg → estira ×3.1 al mover el pie.
Arreglo: cada pieza se repesa a lo largo de su cadena de huesos (posición de las articulaciones del bind):
el peso pasa de un hueso al siguiente con una rampa suave centrada en la articulación (ancho por unión).
Uso: python receta_adan_v27.py ADAN_V22_HABLA.glb ADAN_V27.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402
import receta_adan_v26 as v26  # noqa: E402

S = re._suave

# cadenas por pieza: (hueso dominante que identifica la pieza, cadena, anchos de cada unión en u)
# los anchos son la mitad de la rampa: ~ medio grosor del miembro en esa unión
CADENAS = [
    ({"UpperArm", "Shoulder"}, ["Shoulder", "UpperArm", "LowerArm"], [0.030, 0.022]),
    ({"LowerArm", "Hand"}, ["LowerArm", "Hand"], [0.014]),                       # puño de la muñeca
    ({"IndexDistal"}, ["Hand", "IndexProximal", "IndexIntermediate", "IndexDistal"], [0.007, 0.005, 0.004]),
    ({"MiddleDistal"}, ["Hand", "MiddleProximal", "MiddleIntermediate", "MiddleDistal"], [0.007, 0.005, 0.004]),
    ({"RingDistal"}, ["Hand", "RingProximal", "RingIntermediate", "RingDistal"], [0.007, 0.005, 0.004]),
    ({"LittleDistal"}, ["Hand", "LittleProximal", "LittleIntermediate", "LittleDistal"], [0.006, 0.005, 0.004]),
    # las dos piezas del pulgar usan la MISMA cadena y anchos: así no se separan al doblarse (el "pulgar en pedazos")
    ({"ThumbMetacarpal", "ThumbProximal", "ThumbDistal"}, ["Hand", "ThumbMetacarpal", "ThumbProximal", "ThumbDistal"], [0.008, 0.006, 0.005]),
    ({"LowerLeg", "Foot"}, ["LowerLeg", "Foot"], [0.020]),
    ({"Foot", "Toes"}, ["Foot", "Toes"], [0.014]),
    ({"UpperLeg"}, ["UpperLeg", "LowerLeg"], [0.022]),
]


def _cadena_param(P, H, tail):
    """Parámetro de longitud de arco de la proyección de P sobre la polilínea H (+ cola)."""
    pts = np.vstack([H, tail])
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    mejor_d = np.full(len(P), np.inf); s = np.zeros(len(P))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a; l2 = max(ab @ ab, 1e-12)
        t = (P - a) @ ab / l2
        tc = np.clip(t, -0.5 if i == 0 else 0, 1.5 if i == len(pts) - 2 else 1)
        q = a + tc[:, None] * ab
        d = np.linalg.norm(P - q, axis=1)
        m = d < mejor_d
        mejor_d[m] = d[m]; s[m] = L[i] + tc[m] * np.sqrt(l2)
    return s, L


def pesos_cadena(P, H, tail, anchos):
    s, L = _cadena_param(P, H, tail)
    n = len(H)
    W = np.zeros((len(P), n))
    # rampa en cada unión k (entre hueso k-1 y k), centrada en L[k]
    prev = np.ones(len(P))
    for k in range(1, n):
        x = np.clip((s - L[k]) / (2 * anchos[k - 1]) + 0.5, 0, 1)
        r = x * x * (3 - 2 * x)          # smoothstep
        W[:, k - 1] = prev * (1 - r)
        prev = prev * r
    W[:, n - 1] = prev
    return W


def repesar(E):
    j = E.j
    sk = j["skins"][0]["joints"]
    nombres = [j["nodes"][k]["name"] for k in sk]
    ibm = accesor(j, E.b, j["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    cabeza = {nm: np.linalg.inv(ibm[i])[:3, 3] for i, nm in enumerate(nombres)}
    nodo, malla = v24._malla_rostro(E)
    hechos = []
    mallas = [m for m in j["meshes"]]
    for m in mallas:
        for p in m["primitives"]:
            at = p["attributes"]
            if "JOINTS_0" not in at:
                continue
            Jt = accesor(j, E.b, at["JOINTS_0"]).astype(np.int64)
            Wt = accesor(j, E.b, at["WEIGHTS_0"]).astype(float)
            if Wt.max() > 1.5:
                Wt = Wt / (65535.0 if Wt.max() > 300 else 255.0)
            V = accesor(j, E.b, at["POSITION"]).astype(float)
            if len(V) > 5000:
                continue
            dom = {nombres[jj] for jj in np.unique(Jt[np.arange(len(Jt)), Wt.argmax(1)])}
            lado = "Left" if any(d.startswith("Left") for d in dom) else ("Right" if any(d.startswith("Right") for d in dom) else None)
            if lado is None:
                continue
            base = {d[len(lado):] for d in dom if d.startswith(lado)}
            cad = None
            for clave, cadena, anchos in CADENAS:
                if base <= set(cadena) and (base & clave):
                    cad = (cadena, anchos); break
            if cad is None:
                continue
            cadena, anchos = cad
            bones = [lado + c for c in cadena]
            H = np.array([cabeza[b] for b in bones])
            # cola: sigue la dirección del último hueso (o hacia el centro de la pieza)
            d = H[-1] - H[-2]
            tail = H[-1] + d / max(np.linalg.norm(d), 1e-9) * max(np.linalg.norm(d), 0.01)
            Wn = pesos_cadena(V, H, tail, anchos)
            idx = np.array([nombres.index(b) for b in bones])
            # a lo más 4 huesos: los de mayor peso por vértice
            orden = np.argsort(-Wn, axis=1)[:, :4]
            J4 = np.zeros((len(V), 4), np.uint16); W4 = np.zeros((len(V), 4), np.float32)
            for c in range(min(4, Wn.shape[1])):
                J4[:, c] = idx[orden[:, c]]
                W4[:, c] = Wn[np.arange(len(V)), orden[:, c]]
            W4 /= W4.sum(1, keepdims=True)
            at["JOINTS_0"] = v26.v24._add_raw(E, J4, 5123, "VEC4", 34962)
            at["WEIGHTS_0"] = v26.v24._add_raw(E, W4, 5126, "VEC4", 34962)
            hechos.append("/".join(bones))
    E.b = bytes(E.out)
    E.log.append({"operacion": "pesos de piel por cadena (rampas en uniones)", "piezas": hechos})
    return hechos


def muneca(E):
    """El "aro oscuro" de la muñeca: el borde del puño (pieza LowerArm/Hand) sobresalía 1–2 mm·u de la orilla de la
    mano (radio 0.028 contra 0.027) y su cara interior oscura se veía como anillo. El tramo final del puño se
    mete hacia el eje del brazo (hasta 85 %) para quedar dentro de la mano."""
    j = E.j
    nombres = [j["nodes"][k]["name"] for k in j["skins"][0]["joints"]]
    ibm = accesor(j, E.b, j["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    hechos = 0
    for lado, sg in (("Left", 1), ("Right", -1)):
        C = np.linalg.inv(ibm[nombres.index(lado + "Hand")])[:3, 3]
        for p in E.prims(v24.PIEL):
            V, T = E.leer(p)
            if not (90 <= len(V) <= 100) or sg * V[:, 0].mean() < 0.30 or sg * V[:, 0].mean() > 0.36:
                continue
            t = np.clip((sg * (V[:, 0] - C[0]) + 0.012) / 0.012, 0, 1)      # 0 a 1.2 cm de la muñeca → 1 en la orilla
            k = 1 - 0.15 * t * t * (3 - 2 * t)
            V2 = V.copy()
            V2[:, 1:] = C[1:] + (V[:, 1:] - C[1:]) * k[:, None]
            E.escribir(p, V2, T)
            hechos += 1
    E.log.append({"operacion": "borde del puño metido en la mano (sin aro)", "piezas": hechos})


def main(src, dst):
    tmp26 = dst + ".v26.glb"
    v26.main(src, tmp26)
    E = re.Editor(tmp26)
    repesar(E)
    muneca(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V27: V26 + pesos de piel suaves en uniones (brazos, piernas, manos, dedos). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(tmp26)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-1:]:
        print(x)
