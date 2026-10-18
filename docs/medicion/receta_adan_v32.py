"""Adán V32 (sobre V22 HABLA → V31): manos — rediseño del cuerpo, paso 2.

Diagnóstico (CHXP, pose T, palma abajo; SENKU tamaño contra la Hoja de vistas):
  - Tamaño: con los brazos abajo la mano mide 0.082 u de alto (hoja: puño 0.084). Se conserva.
  - Dedos: prismas de sección cuadrada (anillos de 12 vértices con bisel chico) y punta plana cortada.
  - Palma: rectángulo con esquinas vivas en la vista de arriba.
Arreglo (solo se mueven vértices: topología, pesos, UV y morphs intactos):
  1) Dedos y pulgar: cada anillo de la sección pasa a una superelipse (n = 2.6, "cuadrado redondo") con los mismos
     semiejes; la punta se vuelve domo (el vértice central sale, el último anillo se cierra un poco).
  2) Palma: el contorno visto desde arriba (plano de la palma) se recorta a una superelipse n = 4 → esquinas
     redondeadas sin perder el ancho de los nudillos; el dorso sube un poco al centro (domo suave).
  3) Normales suaves recalculadas por pieza (soldando costuras).
Uso: python receta_adan_v32.py ADAN_V22_HABLA.glb ADAN_V32.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v31 as v31  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402

N_DEDO, N_PALMA = 2.3, 3.0
DOMO_PUNTA = 0.22          # salida del vértice de la punta, en radios
CIERRE_PUNTA = 0.90        # último anillo de la punta
DOMO_DORSO = 0.0025        # u


def _superelipse(ang, a, b, n):
    c, s = np.abs(np.cos(ang)), np.abs(np.sin(ang))
    return (np.power(c / a, n) + np.power(s / b, n)) ** (-1.0 / n)


def _normales(V, F):
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True); w = w.reshape(-1)
    n = w.max() + 1
    P = np.zeros((n, 3)); np.add.at(P, w, V); P /= np.bincount(w, minlength=n)[:, None]
    T = P[w[F]]; Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    N = np.zeros((n, 3))
    for k in range(3):
        np.add.at(N, w[F[:, k]], Nf)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N[w]


def redondear_dedo(V):
    """Pieza de dedo: eje = componente principal; anillos agrupados a lo largo del eje."""
    c = V.mean(0)
    _, _, vt = np.linalg.svd(V - c, full_matrices=False)
    ax, e1, e2 = vt[0], vt[1], vt[2]
    t = (V - c) @ ax
    # la punta es el extremo lejos de la palma: el de mayor |x| (pose T)
    if np.sign(ax[0]) != np.sign(c[0]):
        ax, t = -ax, -t
    orden = np.argsort(t)
    grupos, g = [], [orden[0]]
    for i in orden[1:]:
        if t[i] - t[g[-1]] > 0.0012:
            grupos.append(g); g = [i]
        else:
            g.append(i)
    grupos.append(g)
    V2 = V.copy()
    anillos = [np.array(g) for g in grupos if len(g) >= 6]
    for k, g in enumerate(anillos):
        cc = V[g].mean(0)
        u, v = (V[g] - cc) @ e1, (V[g] - cc) @ e2
        r = np.hypot(u, v)
        centro = r < 0.35 * np.median(r)          # vértice central de la tapa (punta o base)
        a, b = np.abs(u[~centro]).max(), np.abs(v[~centro]).max()
        r_obj = _superelipse(np.arctan2(v, u), a, b, N_DEDO)
        f = np.where(r > 1e-9, r_obj / np.maximum(r, 1e-9), 1.0)
        f = np.minimum(f, 1.0)                 # solo redondea (recorta esquinas), no infla
        f[centro] = 1.0
        es_punta = k == len(anillos) - 1
        if es_punta:
            f = f * CIERRE_PUNTA
        V2[g] = cc + (u * f)[:, None] * e1 + (v * f)[:, None] * e2 + (((V[g] - cc) @ ax)[:, None] * ax)
        if es_punta and centro.any():
            V2[np.array(g)[centro]] += ax * DOMO_PUNTA * float(np.median(r[~centro]))
    return V2


def redondear_palma(V):
    c = V.mean(0)
    # plano de la palma: x (largo) y z (ancho) en pose T; espesor en y
    u, w = V[:, 0] - c[0], V[:, 2] - c[2]
    a, b = np.abs(u).max(), np.abs(w).max()
    r = np.hypot(u, w)
    r_obj = _superelipse(np.arctan2(w, u), a, b, N_PALMA)
    f = np.minimum(1.0, r_obj / np.maximum(r, 1e-9))
    V2 = V.copy()
    V2[:, 0] = c[0] + u * f; V2[:, 2] = c[2] + w * f
    # domo del dorso (arriba, +y), más alto al centro
    dorso = V[:, 1] > c[1]
    cen = np.clip(1 - (u / a) ** 2, 0, 1) * np.clip(1 - (w / b) ** 2, 0, 1)
    V2[:, 1] += dorso * DOMO_DORSO * cen
    return V2


def manos(E):
    j = E.j
    nombres = [j["nodes"][k]["name"] for k in j["skins"][0]["joints"]]
    hechos = []
    for m in j["meshes"]:
        for p in m["primitives"]:
            at = p["attributes"]
            if "JOINTS_0" not in at:
                continue
            V = accesor(j, E.b, at["POSITION"]).astype(float)
            if len(V) > 400:
                continue
            Jt = accesor(j, E.b, at["JOINTS_0"]).astype(np.int64)
            Wt = accesor(j, E.b, at["WEIGHTS_0"]).astype(float)
            dom = {nombres[x] for x in np.unique(Jt[np.arange(len(Jt)), Wt.argmax(1)])}
            base = {d.replace("Left", "").replace("Right", "") for d in dom}
            if base & {"IndexDistal", "MiddleDistal", "RingDistal", "LittleDistal", "ThumbDistal"}:
                V2, tipo = redondear_dedo(V), "dedo"
            elif base == {"Hand", "LowerArm"} and np.abs(V[:, 0]).min() > 0.29:
                V2, tipo = redondear_palma(V), "palma"
            else:
                continue
            F = accesor(j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
            E.escribir(p, V2, [])
            at["NORMAL"] = E._add(_normales(V2, F), "VEC3", 34962)
            hechos.append((tipo, sorted(dom)[0], round(float(np.abs(V2 - V).max()), 4)))
    E.b = bytes(E.out)
    E.log.append({"operacion": "manos: dedos redondos con punta en domo, palma con esquinas redondeadas", "piezas": hechos})
    return hechos


def main(src, dst):
    t31 = dst + ".v31.glb"
    v31.main(src, t31)
    E = re.Editor(t31)
    manos(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V32: V31 + manos (dedos redondos, punta en domo, palma redondeada). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t31)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-1:]:
        print(x)
