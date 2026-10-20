"""Mocap BVH (CMU, Mixamo…) → clip en el rig de Adán, con corrector chibi (20 oct 2026).

Ruta AAA §6.1. Fuente recomendada: CMU Graphics Lab Motion Capture Database (uso libre). Mixamo sólo a mano.

  python -m copox.movimiento.bvh CAMINAR.bvh --glb PERSONAJE.glb --clip Mocap_Caminar --salida OUT.glb
         [--fps 30] [--desde 0 --hasta -1] [--sin-avance] [--sin-corrector] [--radio-cabeza 0.17]

Retarget por rotaciones de mundo: ambos esqueletos en T-pose de reposo (el BVH con rotaciones 0; el de Adán en su
reposo glTF). Para cada hueso mapeado, Δ_mundo = R_bvh(cuadro) (su reposo es la identidad), alineado al frente de
Adán con un giro en Y detectado de las caderas; R_adan = Δ · R_reposo_adan; la local sale de la del padre.
Raíz: posición de Hips escalada por (alto de cadera Adán ÷ alto de cadera BVH) → zancada proporcional a la pierna chibi.
Corrector chibi:
  - manos fuera de la cabeza (esfera de radio `radio-cabeza` alrededor del centro de la cabeza): si una mano entra,
    se gira el brazo desde el hombro lo justo para sacarla (la cabeza chibi es 2–3× la humana);
  - pies nunca bajo el piso (la cadera sube lo necesario).
"""
from __future__ import annotations

import argparse
import json
import re

import numpy as np

MAPA = {   # BVH (CMU/cgspeed, Mixamo, genérico) → Adán
    "Hips": "Hips", "LowerBack": None, "Spine": "Spine", "Spine1": "Chest", "Spine2": "Chest", "Chest": "Chest",
    "Neck": "Neck", "Neck1": None, "Head": "Head",
    "LeftShoulder": "LeftShoulder", "LeftArm": "LeftUpperArm", "LeftForeArm": "LeftLowerArm", "LeftHand": "LeftHand",
    "RightShoulder": "RightShoulder", "RightArm": "RightUpperArm", "RightForeArm": "RightLowerArm", "RightHand": "RightHand",
    "LeftUpLeg": "LeftUpperLeg", "LeftLeg": "LeftLowerLeg", "LeftFoot": "LeftFoot", "LeftToeBase": "LeftToes",
    "RightUpLeg": "RightUpperLeg", "RightLeg": "RightLowerLeg", "RightFoot": "RightFoot", "RightToeBase": "RightToes",
}


# ---------------------------------------------------------------- BVH

class BVH:
    def __init__(self, texto):
        self.nombres, self.padre, self.offset, self.canales = [], [], [], []
        tok = texto.replace("{", " { ").replace("}", " } ").split()
        i, pila = 0, []
        while i < len(tok) and tok[i] != "MOTION":
            t = tok[i]
            if t in ("ROOT", "JOINT"):
                self.nombres.append(re.sub(r"^.*:", "", tok[i + 1]))             # quita «mixamorig:»
                self.padre.append(pila[-1] if pila else -1)
                self.offset.append(None); self.canales.append([])
                i += 2; continue
            if t == "End":
                self.nombres.append(None); self.padre.append(pila[-1]); self.offset.append(None); self.canales.append([])
                i += 2; continue
            if t == "{":
                pila.append(len(self.nombres) - 1)
            elif t == "}":
                pila.pop()
            elif t == "OFFSET":
                self.offset[pila[-1]] = [float(x) for x in tok[i + 1:i + 4]]; i += 4; continue
            elif t == "CHANNELS":
                n = int(tok[i + 1]); self.canales[pila[-1]] = tok[i + 2:i + 2 + n]; i += 2 + n; continue
            i += 1
        i += 1
        n_frames = int(tok[i + 1]); self.dt = float(tok[i + 4])
        datos = np.array(tok[i + 5:], float)
        self.n_canales = sum(len(c) for c in self.canales)
        self.cuadros = datos[: n_frames * self.n_canales].reshape(n_frames, self.n_canales)
        self.offset = np.array([o if o is not None else [0, 0, 0] for o in self.offset], float)

    def fk(self):
        """Rotaciones y posiciones de mundo por cuadro: R [n, J, 3, 3], P [n, J, 3]."""
        n, J = len(self.cuadros), len(self.nombres)
        R = np.zeros((n, J, 3, 3)); P = np.zeros((n, J, 3))
        col = 0
        locR = np.tile(np.eye(3), (n, J, 1, 1)); locT = np.tile(self.offset[None], (n, 1, 1))
        for j, ch in enumerate(self.canales):
            for c in ch:
                v = self.cuadros[:, col]; col += 1
                if c.endswith("position"):
                    locT[:, j, "XYZ".index(c[0])] = v
                else:
                    locR[:, j] = locR[:, j] @ _rot_eje("XYZ".index(c[0]), np.radians(v))
        for j in range(J):
            p = self.padre[j]
            if p < 0:
                R[:, j], P[:, j] = locR[:, j], locT[:, j]
            else:
                R[:, j] = R[:, p] @ locR[:, j]
                P[:, j] = P[:, p] + np.einsum("nij,nj->ni", R[:, p], locT[:, j])
        return R, P

    def reposo(self):
        P = np.zeros((len(self.nombres), 3))
        for j in range(len(self.nombres)):
            P[j] = self.offset[j] + (P[self.padre[j]] if self.padre[j] >= 0 else 0)
        return P


def _rot_eje(eje, a):
    a = np.asarray(a, float)
    c, s = np.cos(a), np.sin(a)
    M = np.zeros(a.shape + (3, 3)); M[..., eje, eje] = 1
    i, k = [(1, 2), (2, 0), (0, 1)][eje]
    M[..., i, i] = c; M[..., k, k] = c; M[..., i, k] = -s; M[..., k, i] = s
    return M


def _m2q(M):
    """Matrices [..., 3, 3] → cuaterniones glTF [x, y, z, w] (con hemisferio continuo)."""
    M = np.asarray(M, float)
    t = np.trace(M, axis1=-2, axis2=-1)
    q = np.zeros(M.shape[:-2] + (4,))
    w = np.sqrt(np.maximum(0, 1 + t)) / 2
    x = np.sqrt(np.maximum(0, 1 + M[..., 0, 0] - M[..., 1, 1] - M[..., 2, 2])) / 2
    y = np.sqrt(np.maximum(0, 1 - M[..., 0, 0] + M[..., 1, 1] - M[..., 2, 2])) / 2
    z = np.sqrt(np.maximum(0, 1 - M[..., 0, 0] - M[..., 1, 1] + M[..., 2, 2])) / 2
    x = np.copysign(x, M[..., 2, 1] - M[..., 1, 2]); y = np.copysign(y, M[..., 0, 2] - M[..., 2, 0])
    z = np.copysign(z, M[..., 1, 0] - M[..., 0, 1])
    q = np.stack([x, y, z, w], -1)
    q /= np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-12)
    for i in range(1, q.shape[0]):                                          # continuidad en el tiempo
        flip = np.einsum("...i,...i->...", q[i], q[i - 1]) < 0
        q[i][flip] *= -1
    return q


def _q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


# ---------------------------------------------------------------- esqueleto destino

class Destino:
    def __init__(self, E):
        j = E.j
        self.j = j
        self.joints = j["skins"][0]["joints"]
        self.par = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
        self.idx = {j["nodes"][i]["name"]: i for i in self.joints}
        self.Rl = {i: _q2m(j["nodes"][i].get("rotation", [0, 0, 0, 1])) for i in range(len(j["nodes"]))}
        self.Tl = {i: np.array(j["nodes"][i].get("translation", [0, 0, 0]), float) for i in range(len(j["nodes"]))}
        self.Sl = {i: np.array(j["nodes"][i].get("scale", [1, 1, 1]), float) for i in range(len(j["nodes"]))}
        self.orden = sorted(self.joints, key=self._prof)
        self.Rg0, self.Pg0 = self.fk({})

    def _prof(self, i):
        d = 0
        while i in self.par:
            i = self.par[i]; d += 1
        return d

    def fk(self, Rloc, Thips=None, hips=None):
        """Global de todos los nodos-ancestro + huesos con rotaciones locales dadas (las demás de reposo)."""
        Rg, Pg = {}, {}

        def g(i):
            if i in Rg:
                return Rg[i], Pg[i]
            R = Rloc.get(i, self.Rl[i]); T = Thips if (hips is not None and i == hips and Thips is not None) else self.Tl[i]
            if i in self.par:
                pR, pP = g(self.par[i])
                Rg[i] = pR @ R; Pg[i] = pP + pR @ (T * 1.0)
            else:
                Rg[i] = R; Pg[i] = T.copy()
            return Rg[i], Pg[i]
        for i in self.joints:
            g(i)
        return Rg, Pg


# ---------------------------------------------------------------- retarget

def retarget(bvh, E, fps=30, desde=0, hasta=-1, avance=True, corrector=True, radio_cabeza=0.17):
    D = Destino(E)
    R, P = bvh.fk()
    hasta = len(R) if hasta in (-1, None) else hasta
    R, P = R[desde:hasta], P[desde:hasta]
    # remuestreo al fps pedido
    t_src = np.arange(len(R)) * bvh.dt
    t = np.arange(int(round(t_src[-1] * fps)) + 1) / fps
    k = np.clip(np.round(t / bvh.dt).astype(int), 0, len(R) - 1)
    R, P = R[k], P[k]
    src = {n: j for j, n in enumerate(bvh.nombres) if n}
    mapa = {D.idx[MAPA[n]]: src[n] for n in src if MAPA.get(n) and MAPA[n] in D.idx}
    if D.idx.get("Hips") not in mapa:
        raise ValueError("el BVH no trae Hips mapeable")
    # alineación de frente: caderas izquierda→derecha del BVH contra las de Adán
    P0 = bvh.reposo()
    def lado(nombres, Pm):
        a = next((Pm[nombres[n]] for n in ("LeftUpLeg", "LeftUpperLeg") if n in nombres), None)
        b = next((Pm[nombres[n]] for n in ("RightUpLeg", "RightUpperLeg") if n in nombres), None)
        return None if a is None or b is None else (a - b)
    vs = lado(src, P0)
    vt = D.Pg0[D.idx["LeftUpperLeg"]] - D.Pg0[D.idx["RightUpperLeg"]]
    yaw = 0.0
    if vs is not None:
        yaw = np.arctan2(vs[0], vs[2]) - np.arctan2(vt[0], vt[2])
    Y = _rot_eje(1, -yaw)
    hips_t, hips_s = D.idx["Hips"], src["Hips"]
    esc = D.Pg0[hips_t][1] / max(P0[hips_s][1] - min(P0[:, 1].min(), 0), 1e-6)
    piso_bvh = P[:, :, 1].min()
    pistas_R = {i: [] for i in D.orden}
    pistas_T = []
    cab = D.idx.get("Head")
    pa_h = D.par.get(hips_t)
    Rpg, Ppg = D.Rg0.get(pa_h, np.eye(3)), D.Pg0.get(pa_h, np.zeros(3))
    for f in range(len(R)):
        G, Rloc = {}, {}
        for i in D.orden:                                                    # de la raíz a las puntas
            pa = D.par.get(i)
            pg = G.get(pa, D.Rg0.get(pa, np.eye(3))) if pa is not None else np.eye(3)
            if i in mapa:
                G[i] = Y @ R[f, mapa[i]] @ Y.T @ D.Rg0[i]
                Rloc[i] = pg.T @ G[i]
            else:
                G[i] = pg @ D.Rl[i]
        ph = Y @ (P[f, hips_s] - np.array([0, piso_bvh, 0])) * esc
        if not avance:
            ph[[0, 2]] = (Y @ ((P[0, hips_s] - np.array([0, piso_bvh, 0])) * esc))[[0, 2]]
        Th = Rpg.T @ (ph - Ppg)
        if corrector:
            Rloc, Th = _corregir(D, Rloc, Th, hips_t, cab, radio_cabeza)
        for i in D.orden:
            pistas_R[i].append(Rloc.get(i, D.Rl[i]))
        pistas_T.append(Th)
    pistas = {}
    for i, Ms in pistas_R.items():
        if i in mapa or any(i == D.par.get(m) for m in mapa):
            pistas[(i, "rotation")] = _m2q(np.array(Ms)).astype(np.float32)
    pistas[(hips_t, "translation")] = np.array(pistas_T, np.float32)
    return t, pistas, {"cuadros": len(t), "fps": fps, "huesos": len(mapa), "giro_frente_grados": round(float(np.degrees(yaw)), 1),
                       "escala_raiz": round(float(esc), 5)}


def _corregir(D, Rloc, Th, hips, cab, radio):
    """Manos fuera de la cabeza chibi y pies sobre el piso."""
    Rg, Pg = D.fk(Rloc, Th, hips)
    if cab is not None:
        centro = Pg[cab] + Rg[cab] @ np.array([0, radio * 0.9, 0])
        for lado in ("Left", "Right"):
            hu, ma = D.idx.get(lado + "UpperArm"), D.idx.get(lado + "Hand")
            if hu is None or ma is None:
                continue
            for _ in range(12):
                v = Pg[ma] - centro
                if np.linalg.norm(v) >= radio:
                    break
                hombro = Pg[hu]
                a, b = Pg[ma] - hombro, centro - hombro
                eje = np.cross(b, a)
                if np.linalg.norm(eje) < 1e-9:
                    eje = np.array([0, 0, 1.0])
                eje /= np.linalg.norm(eje)
                Rw = _rodrigues(eje, np.radians(6))
                pg = Rg[D.par[hu]]
                Rloc[hu] = pg.T @ Rw @ Rg[hu]
                Rg, Pg = D.fk(Rloc, Th, hips)
    pies = [D.idx[n] for n in ("LeftFoot", "RightFoot", "LeftToes", "RightToes") if n in D.idx]
    bajo = min(Pg[i][1] for i in pies)
    if bajo < 0:
        pa = D.par.get(hips)
        Rp = D.Rg0.get(pa, np.eye(3))
        Th = Th + Rp.T @ np.array([0, -bajo, 0])
    return Rloc, Th


def _rodrigues(eje, a):
    K = np.array([[0, -eje[2], eje[1]], [eje[2], 0, -eje[0]], [-eje[1], eje[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def main(argv=None):
    ap = argparse.ArgumentParser(description="BVH (CMU/Mixamo) → clip en el rig de Adán con corrector chibi")
    ap.add_argument("bvh")
    ap.add_argument("--glb", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--desde", type=int, default=0)
    ap.add_argument("--hasta", type=int, default=-1)
    ap.add_argument("--sin-avance", action="store_true")
    ap.add_argument("--sin-corrector", action="store_true")
    ap.add_argument("--radio-cabeza", type=float, default=0.17)
    a = ap.parse_args(argv)
    from copox.medicion.rostro_edicion import Editor
    from copox.movimiento import clip_gltf as cg
    B = BVH(open(a.bvh).read())
    E = Editor(a.glb)
    t, pistas, info = retarget(B, E, a.fps, a.desde, a.hasta, not a.sin_avance, not a.sin_corrector, a.radio_cabeza)
    cg.agregar_clip(E, a.clip, t, pistas)
    E.log.append({"operacion": "clip desde BVH", "clip": a.clip, **info})
    E.guardar(a.salida, nota=f"Clip {a.clip} desde mocap BVH. SIN APROBAR.")
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
