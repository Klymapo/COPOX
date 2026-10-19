"""Adán V40 (sobre V39): torso suave como la referencia y manos intercambiables de bloques (abierta, puño, señalar)
soldadas al antebrazo por una boca de muñeca estándar.

Decisiones de Admin (18 oct 2026): torso "pecho suave + clavícula"; manos "bloques redondeados, suave", medidas contra
las hojas de Adán (no la mano con regla); juego inicial abierta relajada, puño y señalar; todas en el GLB de Adán.
La mano con pistola se hace después de aprobar las manos base.
Uso: GODOT_BIN=… python receta_adan_v40.py ADAN_V22_HABLA.glb ADAN_V40.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402


def rasgos_suaves(T0):
    """Como la hoja del torso: pecho plano, clavícula insinuada, deltoides y trapecio fundidos. Nada más."""
    def borde(y, x, lado):
        a, b, c = [float(np.ravel(v)[0]) for v in T0.seccion(np.array([y]))]
        return c + lado * b * max(1 - (abs(x) / a) ** T0.p, 0) ** (1 / T0.p)
    fr = lambda y, x: borde(y, x, 1)      # noqa: E731
    R = []
    # sin volumen de pecho: cualquier elipsoide ahí se lee como pectoral con contorno (revisión V40)
    R.append(dict(tipo="suma", forma="capsula", a=[0.012, 0.461, fr(0.461, 0.012) - 0.003], b=[0.080, 0.465, 0.052], r1=0.0040, r2=0.0022, k=0.008))  # clavícula
    R.append(dict(tipo="suma", forma="elipsoide", c=[0.100, 0.434, 0.016], r=[0.032, 0.036, 0.038], k=0.025))     # deltoides: se funde con el brazo
    R.append(dict(tipo="suma", forma="capsula", a=[0.035, 0.478, 0.014], b=[0.105, 0.456, 0.014], r1=0.016, k=0.018))  # trapecio
    return R


MANOS = ("abierta", "puno", "senalar")
ESCALA_MANO = 1.3             # Admin: "manos más grandes", para igualar el antebrazo de V39 (hoja del cuerpo)
TRIS_MANO = {"abierta": 2600, "puno": 2400, "senalar": 2500}
ENTRA = 0.006                 # u: la mano empieza dentro del antebrazo
CORTE = 0.002                 # u: se corta 2 mm después del anillo y se cose a él
RAMPA_MUNECA = 0.006          # u: pesos del antebrazo → mano, hasta 6 mm después de la muñeca
MANO_FIJA = {"Idle": "abierta"}   # Admin: en reposo, mano abierta relajada (el clip traía puños)
UMBRAL_PUNO, UMBRAL_RECTO = 55.0, 30.0   # grados de la falange proximal para decidir la mano de cada clip


def _anillo(E, lado):
    """Último anillo del antebrazo: posiciones, normales, joints y pesos (la boca de muñeca estándar)."""
    p = v39._prim(E, "Brazo" + lado[0])
    V = v39._leer(E, p, "POSITION").astype(float); N = v39._leer(E, p, "NORMAL").astype(float)
    J = v39._leer(E, p, "JOINTS_0").astype(int); W = v39._leer(E, p, "WEIGHTS_0").astype(float)
    x = np.abs(V[:, 0]); m = np.isclose(x, x.max(), atol=0.0006)
    # sin duplicados (costura de UV): uno por posición
    _, u = np.unique(np.round(V[m], 6), axis=0, return_index=True)
    idx = np.where(m)[0][np.sort(u)]
    return V[idx], N[idx], J[idx], W[idx]


def mano(E, variante, lado, nombres, carpeta):
    """Una mano de bloques en su pose, cosida a la boca de muñeca de ese lado. Devuelve la primitiva glTF."""
    import receta_adan_v24 as v24
    import receta_adan_v36 as v36
    from copox.medicion import mano_bloques as mb
    from copox.medicion import mano_geo as mg
    s = 1.0 if lado == "Left" else -1.0
    _, H = v38_skin(E)
    Wj = H[lado + "Hand"]
    RV, RN, RJ, RW = _anillo(E, lado)
    RVl = RV * [s, 1, 1]; RNl = RN * [s, 1, 1]                    # al marco de la izquierda
    x_ring = float(RVl[:, 0].mean())
    yc, zc = H[lado + "LowerArm"][1], H[lado + "LowerArm"][2]
    r0 = [float(np.abs(RVl[:, 1] - yc).max()), float(np.abs(RVl[:, 2] - zc).max())]
    largo = 0.1306 * ESCALA_MANO
    M = mb.ManoBloques(largo, mb.POSES[variante], palma_w0=-0.0035 * ESCALA_MANO)
    M.muneca = {"x0": x_ring - ENTRA - Wj[0] * s, "x1": 0.030, "c0": [yc - Wj[1], zc - Wj[2]], "r0": r0,
                "c1": [-M.grosor * 0.10, M.w0], "r1": [M.grosor / 2 * 1.25, M.palma_ancho / 2 * 0.85]}
    V, T = M.malla()
    V = V + np.array([Wj[0] * s, Wj[1], Wj[2]])                # local → mundo (marco izquierdo)
    V, T = v36.simplificar(V, T, TRIS_MANO[variante], carpeta)
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    V, T = mb.cortar(V, T, x_ring + CORTE)
    V, T, oa, base = mb.coser(V, T, RVl, (yc, zc), x_ring + CORTE)
    V = mb.ajustar_boca(V, base, RVl, (yc, zc), x_ring + CORTE)
    N = mg.normales(V, T)
    N[base:] = RNl[oa]
    # pesos: antebrazo en la orilla → mano rígida (las manos se modelan en su pose: no hay huesos de dedos)
    ia, ih = nombres.index(lado + "LowerArm"), nombres.index(lado + "Hand")
    f = np.clip((V[:, 0] - x_ring) / (Wj[0] * s + RAMPA_MUNECA - x_ring), 0, 1); f = f * f * (3 - 2 * f)
    J4 = np.zeros((len(V), 4), np.uint16); J4[:, 0] = ih; J4[:, 1] = ia
    W4 = np.zeros((len(V), 4), np.float32); W4[:, 0] = f; W4[:, 1] = 1 - f
    J4[base:] = RJ[oa]; W4[base:] = (RW[oa] / RW[oa].sum(1, keepdims=True))
    if lado == "Right":
        V = V * [-1, 1, 1]; N = N * [-1, 1, 1]; T = T[:, ::-1].copy()
        V[base:] = RV[oa]                                         # exactos los del anillo derecho
    pieza = ("Mano" + lado[0]) if variante == "abierta" else f"Mano{lado[0]}_{variante}"
    prim = {"attributes": {"POSITION": E._add(V.astype(np.float32), "VEC3", 34962, True),
                           "NORMAL": E._add(N.astype(np.float32), "VEC3", 34962),
                           "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(J4, np.uint16), 5123, "VEC4", 34962),
                           "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
            "indices": v24._add_raw(E, np.ascontiguousarray(T.ravel(), np.uint32), 5125, "SCALAR", 34963),
            "extras": {"pieza": pieza}}
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return prim, {"variante": variante, "lado": lado, "vertices": int(len(V)), "triangulos": int(len(T)),
                  "anillo_vertices": int(len(RV))}


def v38_skin(E):
    import receta_adan_v38 as v38
    return v38._skin(E)


def mapa_manos(E):
    """Qué mano lleva cada clip y cuándo: por la flexión de las falanges proximales que trae el clip."""
    from copox.medicion.gltf import accesor
    j = E.j
    nm = {i: n.get("name") for i, n in enumerate(j["nodes"])}
    out = {}
    for a in j.get("animations", []):
        porlado = {}
        for ch in a["channels"]:
            n = nm[ch["target"]["node"]]
            if ch["target"]["path"] != "rotation" or not n or not n.endswith("Proximal") or "Thumb" in n:
                continue
            lado = "L" if n.startswith("Left") else "R"
            dedo = n.replace("Left", "").replace("Right", "").replace("Proximal", "")
            sm = a["samplers"][ch["sampler"]]
            t = accesor(j, E.b, sm["input"]).astype(float).ravel()
            q = accesor(j, E.b, sm["output"]).reshape(-1, 4)
            ang = np.degrees(2 * np.arccos(np.clip(np.abs(q[:, 3]), 0, 1)))
            porlado.setdefault(lado, {})[dedo] = (t, ang)
        if not porlado:
            continue
        nombre = a["name"]
        cl = {}
        fija = MANO_FIJA.get(nombre.replace("-loop", ""))
        if fija:
            out[nombre] = out[nombre.replace("-loop", "")] = {l: [[0.0, fija]] for l in porlado}
            continue
        for lado, dd in porlado.items():
            ts = sorted(set(np.concatenate([v[0] for v in dd.values()]).round(4)))
            estados = []
            for t in ts:
                g = {d: float(np.interp(t, *dd[d])) for d in dd}
                otros = [g.get(d, 0) for d in ("Middle", "Ring", "Little")]
                if min(otros) > UMBRAL_PUNO and g.get("Index", 0) > UMBRAL_PUNO:
                    e = "puno"
                elif min(otros) > UMBRAL_PUNO and g.get("Index", 90) < UMBRAL_RECTO:
                    e = "senalar"
                else:
                    e = "abierta"
                if not estados or estados[-1][1] != e:
                    estados.append([round(float(t), 4), e])
            cl[lado] = estados
        out[nombre] = cl
        out[nombre.replace("-loop", "")] = cl                     # Godot quita "-loop" del nombre
    return out


def manos(E, carpeta):
    nombres, _ = v38_skin(E)
    log = []
    j = E.j
    mat = v39._prim(E, "ManoL")["material"]
    raiz = j["scenes"][j.get("scene", 0)]["nodes"]
    for variante in MANOS:
        for lado in ("Left", "Right"):
            prim, info = mano(E, variante, lado, nombres, carpeta)
            prim["material"] = mat
            j["meshes"].append({"name": f"MANO_{variante.upper()}_{lado[0]}", "primitives": [prim]})
            j["nodes"].append({"name": f"MANO_{variante.upper()}_{lado[0]}", "mesh": len(j["meshes"]) - 1, "skin": 0})
            raiz.append(len(j["nodes"]) - 1)
            log.append(info)
    # fuera las manos viejas (de una pieza con huesos de dedos)
    j["meshes"][0]["primitives"] = [p for p in j["meshes"][0]["primitives"]
                                    if p.get("extras", {}).get("pieza") not in ("ManoL", "ManoR")]
    j["nodes"].append({"name": "MANOS", "extras": {"variantes": list(MANOS), "defecto": "abierta",
                                                   "por_clip": mapa_manos(E)}})
    raiz.append(len(j["nodes"]) - 1)
    E.b = bytes(E.out)
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    r0 = v39.rasgos
    v39.rasgos = rasgos_suaves
    t39 = dst + ".v39.glb"
    try:
        log = v39.main(src, t39)
    finally:
        v39.rasgos = r0
    E = re.Editor(t39)
    log += [{"operacion": "mano de bloques", **x} for x in manos(E, os.path.dirname(os.path.abspath(dst)))]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V40: torso suave y manos intercambiables de bloques. SIN APROBAR.")
    compactar(tmp, dst)
    for f in (t39, tmp):
        os.remove(f)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-6:]:
        print(x)
