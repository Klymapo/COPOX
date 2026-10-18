"""Clips nuevos para Adán, hechos por código (sin Blender): caminar, correr, saltar, dash, puñetazos y señalar.

python -m copox.movimiento.locomocion ENTRADA.glb SALIDA.glb

Método: pose base = Idle-loop en t=0. Cada clave se describe como giros alrededor de ejes del MUNDO
(x = lado izquierdo del personaje, y = arriba, z = hacia adelante) aplicados a cada hueso en su pose base:
    R_local' = R_local_base · Rot(R_mundo_baseᵀ · eje, θ)
Así los ángulos se leen como "pierna adelante 25°" sin depender de cómo esté orientado cada hueso.
Convenciones: giro +θ en x lleva lo que apunta hacia abajo hacia ATRÁS (pierna atrás, rodilla doblada) y lo que
apunta hacia arriba hacia ADELANTE (torso inclinado al frente, cabeza mirando abajo); −θ al revés.
Las pistas se muestrean a 30 fps con interpolación entre claves (Catmull-Rom suave en el tiempo).
"""
from __future__ import annotations

import json
import struct
import sys

import numpy as np

from copox.medicion.gltf import Modelo, accesor
from copox.medicion import rostro_edicion as re


# --- cuaterniones (x, y, z, w) ----------------------------------------------------------------
def q_mul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def q_eje(eje, ang):
    eje = np.asarray(eje, float); eje = eje / max(np.linalg.norm(eje), 1e-12)
    return np.r_[eje * np.sin(ang / 2), np.cos(ang / 2)]


def _rot(eje, grados):
    a = np.radians(grados); k = np.asarray(eje, float) / np.linalg.norm(eje)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def _entre(a, b):
    """Rotación mínima que lleva la dirección a a la dirección b."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else _rot(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0]), 180)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


def _m2q(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        return np.array([(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s])
    i = int(np.argmax(np.diag(R)))
    j_, k_ = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1 + R[i, i] - R[j_, j_] - R[k_, k_]) * 2
    q = np.zeros(4); q[i] = 0.25 * s; q[j_] = (R[j_, i] + R[i, j_]) / s; q[k_] = (R[k_, i] + R[i, k_]) / s; q[3] = (R[k_, j_] - R[j_, k_]) / s
    return q


X, Y, Z = np.eye(3)
FPS = 30
DEDOS = ["Thumb", "Index", "Middle", "Ring", "Little"]


class Autor:
    def __init__(self, glb):
        self.M = M = Modelo(glb)
        j = M.j
        self.idx = {n.get("name"): i for i, n in enumerate(j["nodes"])}
        trs, _ = M.muestrear("Idle-loop", 0.0)
        self.base_trs = trs
        g = M._mundo(trs)
        self.Rw = {nm: g(i)[:3, :3] for nm, i in self.idx.items()}
        self.base_q = {}
        for nm, i in self.idx.items():
            q = trs.get(i, {}).get("rotation", j["nodes"][i].get("rotation", [0, 0, 0, 1]))
            self.base_q[nm] = np.asarray(q, float)
        self.hips_t = np.asarray(trs[self.idx["Hips"]]["translation"], float)
        self.alto = 0.848
        # puño (dedos) tomado del clip M31_3_Puno al final
        tp, _ = M.muestrear("M31_3_Puno", M.duracion("M31_3_Puno"))
        self.puno = {nm: np.asarray(tp[i]["rotation"]) for nm, i in self.idx.items()
                     if i in tp and "rotation" in tp[i] and any(d in nm for d in DEDOS)}

    def dir_base(self, hueso):
        hijo = {"UpperArm": "LowerArm", "LowerArm": "Hand", "UpperLeg": "LowerLeg", "LowerLeg": "Foot",
                "Shoulder": "UpperArm", "Spine": "Chest", "Chest": "Neck", "Neck": "Head"}
        lado = "Left" if hueso.startswith("Left") else ("Right" if hueso.startswith("Right") else "")
        base = hueso[len(lado):]
        g = self.M._mundo(self.base_trs)
        a = g(self.idx[hueso])[:3, 3]; b = g(self.idx[lado + hijo[base]])[:3, 3]
        return (b - a) / np.linalg.norm(b - a)

    def rot(self, hueso, giros):
        """giros: lista de (eje_mundo, grados) aplicados en ese orden sobre la pose base."""
        q = self.base_q[hueso].copy()
        R = self.Rw[hueso]
        for eje, grados in giros:
            q = q_mul(q, q_eje(R.T @ np.asarray(eje, float), np.radians(grados)))
        return q / np.linalg.norm(q)


def _interp(t, ts, vs, ciclo):
    """Catmull-Rom sobre claves (ts, vs); ciclo=True envuelve."""
    ts = np.asarray(ts, float); vs = np.asarray(vs, float)
    n = len(ts)
    if ciclo:
        T = ts[-1]
        t = t % T
    k = int(np.clip(np.searchsorted(ts, t, side="right") - 1, 0, n - 2))
    t0, t1 = ts[k], ts[k + 1]
    u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
    def v(i):
        if ciclo:
            return vs[i % (n - 1)]
        return vs[int(np.clip(i, 0, n - 1))]
    p0, p1, p2, p3 = v(k - 1), v(k), v(k + 1), v(k + 2)
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


class Clip:
    """Clip con claves por canal: grados alrededor de ejes del mundo (por hueso) y desplazamiento de cadera."""
    def __init__(self, nombre, duracion, ciclo):
        self.nombre, self.dur, self.ciclo = nombre, duracion, ciclo
        self.canales = {}      # (hueso, eje_idx) -> (ts, grados)
        self.cadera = None     # (ts, [(dx,dy,dz)])
        self.dedos = {}        # hueso_mano_lado -> (ts, peso_puño)
        self.miras = {}        # hueso -> (ts, [dirección mundo o None = la de la pose base])

    def g(self, hueso, eje, ts, grados):
        self.canales[(hueso, eje)] = (ts, grados)
        return self

    def mira(self, hueso, ts, dirs):
        """El hueso apunta (de su cabeza a la de su hijo) en esas direcciones del mundo; se compone con el padre."""
        self.miras[hueso] = (ts, dirs)
        return self

    def mover_cadera(self, ts, d):
        self.cadera = (ts, d)
        return self

    def puno(self, lado, ts, pesos, excepto=()):
        """Cierra los dedos de esa mano (0 = pose base, 1 = puño de M31_3_Puno); `excepto` = dedos que quedan rectos."""
        self.dedos[lado] = (ts, pesos, tuple(excepto))
        return self


EJES = {"x": X, "y": Y, "z": Z}


def muestrear(A: Autor, c: Clip):
    n = int(round(c.dur * FPS)) + 1
    t = np.linspace(0, c.dur, n)
    pistas = {}
    huesos = sorted({h for h, _ in c.canales} | set(c.miras))
    # orden jerárquico (padres antes que hijos)
    prof = {h: 0 for h in huesos}
    for h in huesos:
        i = A.idx[h]
        while i in A.M.padre:
            i = A.M.padre[i]; prof[h] += 1
    huesos.sort(key=lambda h: prof[h])
    padres_de = {}
    for h in huesos:
        i, cad = A.idx[h], []
        while i in A.M.padre:
            i = A.M.padre[i]
            nm = A.M.j["nodes"][i].get("name")
            if nm in prof:
                cad.append(nm)
        padres_de[h] = cad
    Q = {h: [] for h in huesos}
    for ti in t:
        Rtot = {}
        for h in huesos:
            Rp = np.eye(3)
            for pa in reversed(padres_de[h]):   # el ancestro más alto primero
                pass
            if padres_de[h]:
                Rp = Rtot[padres_de[h][0]]       # el padre directo (con cadena) ya trae todo lo de arriba
            Rown = np.eye(3)
            for eje in "yxz":
                if (h, eje) in c.canales:
                    ts, gs = c.canales[(h, eje)]
                    Rown = _rot(EJES[eje], float(_interp(ti, ts, gs, c.ciclo))) @ Rown
            if h in c.miras:
                ts, ds = c.miras[h]
                d0 = A.dir_base(h)
                D = np.array([d0 if d is None else np.asarray(d, float) / np.linalg.norm(d) for d in ds])
                tgt = _interp(ti, ts, D, c.ciclo); tgt = tgt / np.linalg.norm(tgt)
                Rown = _entre(d0, Rp.T @ tgt)
            Rtot[h] = Rp @ Rown
            # local: q_base ⊗ q(R_base_mundoᵀ · Rown)
            Rl = A.Rw[h].T @ Rown @ A.Rw[h]
            Q[h].append(q_mul(A.base_q[h], _m2q(Rl)))
    for h in huesos:
        q = np.array(Q[h])
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        for i in range(1, len(q)):
            if q[i] @ q[i - 1] < 0:
                q[i] = -q[i]
        pistas[(h, "rotation")] = q
    if c.cadera:
        ts, d = c.cadera
        D = np.array([_interp(ti, ts, np.asarray(d, float), c.ciclo) for ti in t])
        pistas[("Hips", "translation")] = A.hips_t + D
    for lado, (ts, ps, excepto) in c.dedos.items():
        w = np.clip([_interp(ti, ts, ps, c.ciclo) for ti in t], 0, 1)
        for h, qp in A.puno.items():
            if not h.startswith(lado):
                continue
            if any(e in h for e in excepto):
                qr = np.asarray(A.M.j["nodes"][A.idx[h]].get("rotation", [0, 0, 0, 1]), float)   # recto = reposo
                pistas[(h, "rotation")] = np.tile(qr, (len(t), 1))
                continue
            q0 = A.base_q[h]
            if q0 @ qp < 0:
                qp = -qp
            Q = []
            for wi in w:                     # slerp base → puño
                d = np.clip(q0 @ qp, -1, 1); th = np.arccos(d)
                if th < 1e-6:
                    Q.append(q0)
                else:
                    Q.append((np.sin((1 - wi) * th) * q0 + np.sin(wi * th) * qp) / np.sin(th))
            pistas[(h, "rotation")] = np.array(Q)
    return t, pistas


# --- piernas por IK (pie plantado sin patinar) --------------------------------------------------
def _psi(v):
    return np.degrees(np.arctan2(v[2], v[1]))     # ángulo en el plano y-z (giro alrededor de x)


def piernas_ik(A: Autor, c: Clip, T, S, apoyo, lift, flex=0.95, lean_pie=0.0, n=None):
    """Piernas con IK de dos huesos en el plano sagital. Cada pie: apoyo (fracción del ciclo) plantado en el
    piso, moviéndose hacia atrás a velocidad constante 2S/(apoyo·T) (= velocidad de avance del personaje);
    vuelo: regresa adelante con una curva de altura `lift`. La cadera se ajusta para que la pierna de apoyo
    quede con `flex` de su largo (rebote natural). Devuelve la velocidad de avance en u/s."""
    g = A.M._mundo(A.base_trs)
    pos = lambda nm: g(A.idx[nm])[:3, 3]
    n = n or int(round(T * FPS))
    ts = np.linspace(0, T, n + 1)
    vel = 2 * S / (apoyo * T)
    datos = {}
    for lado, fase in (("Left", 0.0), ("Right", 0.5)):
        H, K, Ak = pos(f"{lado}UpperLeg"), pos(f"{lado}LowerLeg"), pos(f"{lado}Foot")
        a, b = np.linalg.norm(K - H), np.linalg.norm(Ak - K)
        datos[lado] = (H, K, Ak, a, b, fase)
    hip0 = A.hips_t
    piso_tobillo = {l: datos[l][2][1] for l in datos}         # altura del tobillo con el pie plano
    # trayectoria del tobillo relativa a la cadera (en z) y altura absoluta del tobillo
    def tobillo(lado, t):
        H, K, Ak, a, b, fase = datos[lado]
        u = ((t / T) - fase) % 1.0
        if u < apoyo:
            z = S - 2 * S * (u / apoyo); y = piso_tobillo[lado]; pie = 0.0
        else:
            w = (u - apoyo) / (1 - apoyo); s_ = w * w * (3 - 2 * w)
            z = -S + 2 * S * s_; y = piso_tobillo[lado] + lift * np.sin(np.pi * w); pie = 18 * np.sin(np.pi * w) * (1 - w) - 8 * w ** 3
        return z, y, pie, u < apoyo
    # altura de cadera por cuadro: la pierna (o piernas) de apoyo con flex·largo
    hy = []
    for t in ts:
        cand = []
        for lado in datos:
            H, K, Ak, a, b, fase = datos[lado]
            z, y, _, en_apoyo = tobillo(lado, t)
            if en_apoyo:
                Lr = flex * (a + b)
                cand.append(y + np.sqrt(max(Lr ** 2 - (z) ** 2, 1e-6)) - (H[1] - hip0[1]))
        hy.append(min(cand) if cand else None)
    hy = np.array([h if h is not None else np.nan for h in hy], float)
    # vuelo (correr): interpolar la cadera con un arco suave entre apoyos
    ok = ~np.isnan(hy)
    if not ok.all():
        hy = np.interp(np.arange(len(hy)), np.where(ok)[0], hy[ok])
        idx = np.where(~ok)[0]
        # arco hacia arriba en los tramos sin apoyo
        for grupo in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1):
            if len(grupo):
                m = len(grupo); hy[grupo] += 0.6 * lift * np.sin(np.pi * (np.arange(m) + 1) / (m + 1))
    for lado in datos:
        H, K, Ak, a, b, fase = datos[lado]
        th_b = _psi(K - H); sh_b = _psi(Ak - K)
        TH, SH, FT = [], [], []
        for t, hyi in zip(ts, hy):
            z, y, pie, _ = tobillo(lado, t)
            Hc = np.array([H[0], H[1] - hip0[1] + hyi, H[2]])
            P = np.array([Ak[0], y, Hc[2] + z + (Ak[2] - H[2])])
            d = P - Hc; d[0] = 0
            L = min(np.linalg.norm(d), (a + b) * 0.999)
            # ángulo de la rodilla (ley de cosenos); la rodilla dobla hacia adelante (muslo adelante, tibia atrás)
            cos_t = (a * a + L * L - b * b) / (2 * a * L)
            alpha = np.degrees(np.arccos(np.clip(cos_t, -1, 1)))
            base = _psi(d)
            th = base - alpha            # muslo hacia adelante de la línea cadera-tobillo
            Kp = Hc + a * np.array([0, np.cos(np.radians(th)), np.sin(np.radians(th))])
            sh = _psi(P - Kp)
            w180 = lambda x: (x + 180) % 360 - 180
            dth = w180(th - th_b); dsh = w180(sh - sh_b) - dth
            TH.append(dth); SH.append(dsh); FT.append(pie + lean_pie - (dth + dsh))
        # signo verificado: Rot x(+θ) suma θ a ψ = atan2(z, y); un vector hacia abajo (ψ≈180°) con +θ va hacia atrás.
        c.g(f"{lado}UpperLeg", "x", list(ts), TH).g(f"{lado}LowerLeg", "x", list(ts), SH).g(f"{lado}Foot", "x", list(ts), FT)
    c.mover_cadera(list(ts), [(0, h - hip0[1], 0) for h in hy])   # desplazamiento respecto a la cadera base
    return vel


# --- clips ------------------------------------------------------------------------------------
def clips_adan(A: Autor):
    H = A.alto
    out = []
    # CAMINAR (1.0 s, dos pasos). Fase: 0 = pie izq adelante en contacto
    T = 1.0; ts = [0, .25, .5, .75, 1.0]
    w = Clip("Walk-loop", T, True)
    A.vel_caminar = piernas_ik(A, w, T, S=0.075, apoyo=0.58, lift=0.035, flex=0.95)
    def brazo(phi, codo, lado, abre=0.18):
        sx = 1 if lado == "Left" else -1
        a = np.radians(phi); b = np.radians(phi + codo)
        return ([sx * abre, -np.cos(a), np.sin(a)], [sx * abre * 0.4, -np.cos(b), np.sin(b)])
    for lado, sg in (("Left", 1), ("Right", -1)):
        fases = [-sg * 18, 0, sg * 18, 0, -sg * 18]          # brazo opuesto a la pierna
        w.mira(f"{lado}UpperArm", ts, [brazo(f, 20, lado)[0] for f in fases])
        w.mira(f"{lado}LowerArm", ts, [brazo(f, 20, lado)[1] for f in fases])
    w.g("Spine", "y", ts, [-5, 0, 5, 0, -5]).g("Chest", "y", ts, [6, 0, -6, 0, 6]).g("Head", "y", ts, [-2, 0, 2, 0, -2])
    w.g("Hips", "z", ts, [3, 0, -3, 0, 3])
    out.append(w)
    # CORRER (0.6 s)
    T = 0.6; ts = [0, .15, .3, .45, .6]
    r = Clip("Run-loop", T, True)
    A.vel_correr = piernas_ik(A, r, T, S=0.10, apoyo=0.40, lift=0.075, flex=0.93, lean_pie=0)
    for lado, sg in (("Left", 1), ("Right", -1)):
        fases = [-sg * 40, 0, sg * 40, 0, -sg * 40]
        r.mira(f"{lado}UpperArm", ts, [brazo(f, 0, lado, 0.25)[0] for f in fases])
        r.mira(f"{lado}LowerArm", ts, [brazo(f + 85, 0, lado, 0.05)[0] for f in fases])
    r.g("Spine", "x", ts, [10] * 5).g("Chest", "y", ts, [10, 0, -10, 0, 10]).g("Spine", "y", ts, [-6, 0, 6, 0, -6])
    r.g("Head", "x", ts, [-6] * 5)
    r.puno("Left", [0, .6], [0.7, 0.7]).puno("Right", [0, .6], [0.7, 0.7])
    out.append(r)
    # SALTAR (1.0 s): agacharse, impulso, aire, caída, aterrizaje
    ts = [0, .18, .32, .5, .68, .82, 1.0]
    s = Clip("Jump", 1.0, False)
    s.g("LeftUpperLeg", "x", ts, [0, -40, 5, -35, -10, -38, 0]).g("RightUpperLeg", "x", ts, [0, -40, 5, -35, -10, -38, 0])
    s.g("LeftLowerLeg", "x", ts, [0, 70, 0, 70, 15, 65, 0]).g("RightLowerLeg", "x", ts, [0, 70, 0, 70, 15, 65, 0])
    s.g("LeftFoot", "x", ts, [0, -30, 25, -20, 5, -28, 0]).g("RightFoot", "x", ts, [0, -30, 25, -20, 5, -28, 0])
    s.g("Spine", "x", ts, [0, 18, -4, 8, 0, 16, 0]).g("Head", "x", ts, [0, -10, 4, -5, 0, -9, 0])
    s.g("LeftUpperArm", "x", ts, [0, 35, -70, -30, -15, 20, 0]).g("RightUpperArm", "x", ts, [0, 35, -70, -30, -15, 20, 0])
    s.g("LeftUpperArm", "z", ts, [0, 0, -25, -40, -30, 0, 0]).g("RightUpperArm", "z", ts, [0, 0, 25, 40, 30, 0, 0])
    s.g("LeftLowerArm", "x", ts, [0, -20, -10, -30, -20, -20, 0]).g("RightLowerArm", "x", ts, [0, -20, -10, -30, -20, -20, 0])
    s.mover_cadera(ts, [(0, 0, 0), (0, -.10 * H, .01 * H), (0, .08 * H, 0), (0, .20 * H, 0), (0, .10 * H, 0), (0, -.09 * H, .01 * H), (0, 0, 0)])
    out.append(s)
    # DASH (0.55 s): arranque inclinado, piernas en tijera, brazos atrás
    ts = [0, .1, .25, .42, .55]
    d = Clip("Dash", 0.55, False)
    d.g("Spine", "x", ts, [0, 28, 32, 15, 0]).g("Head", "x", ts, [0, -18, -20, -9, 0])
    d.g("LeftUpperLeg", "x", ts, [0, -50, -55, -20, 0]).g("RightUpperLeg", "x", ts, [0, 35, 40, 15, 0])
    d.g("LeftLowerLeg", "x", ts, [0, 40, 45, 20, 0]).g("RightLowerLeg", "x", ts, [0, 20, 30, 10, 0])
    d.g("LeftUpperArm", "x", ts, [0, 60, 65, 25, 0]).g("RightUpperArm", "x", ts, [0, 60, 65, 25, 0])
    d.g("LeftUpperArm", "z", ts, [0, 15, 15, 5, 0]).g("RightUpperArm", "z", ts, [0, -15, -15, -5, 0])
    d.mover_cadera(ts, [(0, 0, 0), (0, -.05 * H, .03 * H), (0, -.06 * H, .04 * H), (0, -.02 * H, .02 * H), (0, 0, 0)])
    d.puno("Left", ts, [0, .8, .8, .4, 0]).puno("Right", ts, [0, .8, .8, .4, 0])
    out.append(d)
    # PUÑETAZOS (0.6 s): guardia, golpe recto con giro de cadera, regreso. Brazos por dirección (mira).
    for lado, sg in (("Right", 1), ("Left", -1)):
        otro = "Left" if lado == "Right" else "Right"
        dentro = 1 if lado == "Right" else -1        # hacia el centro del cuerpo en x
        ts = [0, .12, .24, .36, .6]
        p = Clip(f"Punch_{lado[0]}", 0.6, False)
        guard_u = [dentro * 0.15, -0.85, 0.45]; guard_l = [dentro * 0.25, 0.75, 0.6]
        golpe = [dentro * 0.12, 0.08, 1.0]
        p.mira(f"{lado}UpperArm", ts, [None, guard_u, golpe, golpe, None])
        p.mira(f"{lado}LowerArm", ts, [None, guard_l, golpe, golpe, None])
        og_u = [-dentro * 0.15, -0.85, 0.45]; og_l = [-dentro * 0.3, 0.75, 0.55]
        p.mira(f"{otro}UpperArm", ts, [None, og_u, og_u, og_u, None])
        p.mira(f"{otro}LowerArm", ts, [None, og_l, og_l, og_l, None])
        p.g("Spine", "y", ts, [0, sg * 10, -sg * 25, -sg * 20, 0]).g("Chest", "y", ts, [0, sg * 5, -sg * 12, -sg * 10, 0])
        p.g("Head", "y", ts, [0, -sg * 8, sg * 18, sg * 15, 0])
        p.g(f"{otro}UpperLeg", "x", ts, [0, -8, -15, -12, 0]).g(f"{otro}LowerLeg", "x", ts, [0, 10, 18, 15, 0])
        p.mover_cadera(ts, [(0, 0, 0), (0, -.01 * H, 0), (0, -.02 * H, .015 * H), (0, -.02 * H, .01 * H), (0, 0, 0)])
        p.puno(lado, ts, [0, 1, 1, 1, 0]).puno(otro, ts, [0, .9, .9, .9, 0])
        out.append(p)
    # SEÑALAR AL FRENTE (1.6 s): brazo derecho estirado, índice recto, los demás dedos cerrados
    ts = [0, .25, 1.3, 1.6]
    pf = Clip("PointFwd", 1.6, False)
    d_ = [0.10, 0.22, 1.0]
    pf.mira("RightUpperArm", ts, [None, d_, d_, None]).mira("RightLowerArm", ts, [None, d_, d_, None])
    pf.g("Spine", "y", ts, [0, 12, 12, 0]).g("Head", "y", ts, [0, -6, -6, 0]).g("Head", "x", ts, [0, -4, -4, 0])
    pf.puno("Right", ts, [0, 1, 1, 0], excepto=("Index",))
    out.append(pf)
    # APUNTAR CON PISTOLA (bucle 1.2 s): brazo derecho al frente, la izquierda sostiene por debajo
    ts = [0, .6, 1.2]
    am = Clip("Aim-loop", 1.2, True)
    r_ = [0.06, 0.06, 1.0]
    am.mira("RightUpperArm", ts, [r_] * 3).mira("RightLowerArm", ts, [r_] * 3)
    lu = [-0.55, -0.30, 0.78]; ll = [-0.55, 0.12, 0.83]
    am.mira("LeftUpperArm", ts, [lu] * 3).mira("LeftLowerArm", ts, [ll] * 3)
    am.g("Spine", "y", ts, [14, 14, 14]).g("Spine", "x", ts, [2, 3.5, 2]).g("Head", "y", ts, [-10, -10, -10])
    am.puno("Right", ts, [0.9] * 3, excepto=("Index",)).puno("Left", ts, [0.7] * 3)
    out.append(am)
    return out


def senalar_corregido(A: Autor):
    """Point y M31_4_Senalar con el índice estirado de verdad (pose base del índice = recto)."""
    return {"LeftIndexProximal", "LeftIndexIntermediate", "LeftIndexDistal",
            "RightIndexProximal", "RightIndexIntermediate", "RightIndexDistal"}


def escribir(src, dst, clips_fn=clips_adan):
    A = Autor(src)
    E = re.Editor(src)
    j = E.j
    nuevos = []
    for c in clips_fn(A):
        t, pistas = muestrear(A, c)
        it = E._add(t.astype(np.float32), "SCALAR"); j["accessors"][it]["min"] = [0.0]; j["accessors"][it]["max"] = [float(t[-1])]
        anim = {"name": c.nombre, "samplers": [], "channels": []}
        for (h, path), vals in pistas.items():
            ot = E._add(np.asarray(vals, np.float32), "VEC4" if path == "rotation" else "VEC3")
            anim["samplers"].append({"input": it, "output": ot, "interpolation": "LINEAR"})
            anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": A.idx[h], "path": path}})
        j["animations"] = [a for a in j["animations"] if a.get("name") != c.nombre] + [anim]
        nuevos.append(c.nombre)
    # Señalar: el índice va recto (rotación de reposo del índice en los clips que señalan)
    rectos = senalar_corregido(A)
    for a in j["animations"]:
        if a.get("name") not in ("Point", "M31_4_Senalar", "M34_5_Tableta"):
            continue
        for ch in a["channels"]:
            h = j["nodes"][ch["target"]["node"]]["name"]
            if h in rectos and ch["target"]["path"] == "rotation":
                sm = a["samplers"][ch["sampler"]]
                n = len(accesor(j, E.b, sm["input"]))
                q = np.asarray(j["nodes"][A.idx[h]].get("rotation", [0, 0, 0, 1]), np.float32)
                sm["output"] = E._add(np.tile(q, (n, 1)).astype(np.float32), "VEC4")
        nuevos.append(a["name"] + " (índice recto)")
    E.b = bytes(E.out)
    E.log.append({"operacion": "clips nuevos por código", "clips": nuevos})
    E.guardar(dst, nota="Clips de locomoción, puñetazos y señalar (copox/movimiento/locomocion.py). SIN APROBAR.")
    return nuevos


def asentar(glb, clips=("Dash", "Punch_R", "Punch_L"), vuelo=()):
    """Pies en el piso: en cada cuadro la cadera sube o baja para que el pie más bajo toque y = 0
    (sin pies hundidos ni flotando). En Run-loop se respeta un poco de vuelo (la parte positiva del rebote)."""
    M = Modelo(glb)
    j = M.j
    pies = [k for k, p in enumerate(M.prims) if p.joints is not None and len(p.pos) < 300
            and np.ptp(p.pos[:, 1]) < 0.1 and p.pos[:, 1].min() < 0.01]
    piso0 = min(M.posar(None)[k][:, 1].min() for k in pies)
    E = re.Editor(glb)
    hips = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "Hips")
    hechos = {}
    for a in E.j["animations"]:
        if a.get("name") not in clips:
            continue
        ch = next(c for c in a["channels"] if c["target"]["node"] == hips and c["target"]["path"] == "translation")
        sm = a["samplers"][ch["sampler"]]
        t = accesor(E.j, E.b, sm["input"]).astype(float).ravel()
        T = accesor(E.j, E.b, sm["output"]).astype(float).reshape(-1, 3)
        dur = t[-1]
        dy = []
        for ti in t:
            Ps = M.posar(a["name"], ti / dur)
            dy.append(min(Ps[k][:, 1].min() for k in pies) - piso0)
        dy = np.array(dy)
        if a["name"] in vuelo:
            dy = dy - np.clip(T[:, 1] - T[:, 1].mean(), 0, None) * 0.6
        T[:, 1] -= dy
        sm["output"] = E._add(T.astype(np.float32), "VEC3")
        hechos[a["name"]] = round(float(np.abs(dy).max()), 4)
    E.b = bytes(E.out)
    E.log.append({"operacion": "pies asentados en el piso (ajuste de cadera por cuadro)", "corrección_max": hechos})
    E.guardar(glb, nota="Clips de locomoción con pies asentados. SIN APROBAR.")
    return hechos


if __name__ == "__main__":
    print(escribir(sys.argv[1], sys.argv[2]))
    print(asentar(sys.argv[2]))
