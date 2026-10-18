"""COPOX · sistema de agarre: mano + objeto → pose de dedos, posición del objeto y acciones (p. ej. apretar el gatillo).

Base reutilizable para sostener objetos complejos (armas, tazas, herramientas). Contrato del OBJETO (GLB):
  - nodo "AGARRE": marco de la palma. +y a lo largo del mango (del meñique al índice), +x hacia donde apuntarían los
    dedos estirados (el cañón, la hoja), z = x × y. Origen = centro del mango.
  - nodos "CONTACTO_<Dedo>" (opcional): punto donde debe quedar la yema de ese dedo (p. ej. CONTACTO_Index en la cara
    del gatillo). Pueden colgar de un nodo móvil.
  - nodos móviles (p. ej. "GATILLO") con extras.recorrido_rad: giro alrededor de su z al accionarlos.
Contrato del PERSONAJE (GLB): rig tipo Adán (Right/LeftHand, falanges Proximal/Intermediate/Distal, pulgar
Metacarpal/Proximal/Distal), reposo sin rotaciones (pose T, palma abajo) y la mano en una pieza "ManoR"/"ManoL".

Cómo resuelve (sin IA, todo medible):
  1. Distancia con signo del objeto (vóxeles de 0.6 mm + transformada de distancia).
  2. Piel de la mano posada por skinning lineal (los mismos pesos que usa Godot).
  3. Optimización (Powell) de 13 parámetros: posición y giro del objeto respecto a la mano, cierre de cada dedo
     y del pulgar. Costo = penetración (manda) + yemas tocando la superficie + palma apoyada + contactos con nombre.
  4. Acción: el nodo móvil gira su recorrido y el dedo de contacto lo sigue cuadro por cuadro.
Salida: rotaciones locales por hueso (cuaterniones glTF), transformación objeto→mano y la curva de la acción.
"""
from __future__ import annotations

import json

import numpy as np
from scipy import ndimage, optimize

from copox.medicion.gltf import leer_glb, accesor, Modelo

DEDOS = ("Index", "Middle", "Ring", "Little")
FAL = ("Proximal", "Intermediate", "Distal")
REPARTO = (0.42, 0.38, 0.20)            # cómo se reparte el cierre de un dedo entre sus falanges


# --- utilidades -------------------------------------------------------------------------------------------
def rot(eje, ang):
    eje = np.asarray(eje, float); eje = eje / np.linalg.norm(eje)
    K = np.array([[0, -eje[2], eje[1]], [eje[2], 0, -eje[0]], [-eje[1], eje[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def rvec(v):
    a = np.linalg.norm(v)
    return np.eye(3) if a < 1e-12 else rot(v / a, a)


def a_quat(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        return np.array([(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s])
    i = int(np.argmax(np.diag(R))); j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2
    q = np.zeros(4); q[i] = 0.25 * s; q[j] = (R[j, i] + R[i, j]) / s; q[k] = (R[k, i] + R[i, k]) / s; q[3] = (R[k, j] - R[j, k]) / s
    return q


def de_quat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _trs(n):
    M = np.eye(4)
    if "matrix" in n:
        return np.array(n["matrix"], float).reshape(4, 4).T
    if "rotation" in n:
        M[:3, :3] = de_quat(n["rotation"])
    if "scale" in n:
        M[:3, :3] = M[:3, :3] * np.array(n["scale"])
    if "translation" in n:
        M[:3, 3] = n["translation"]
    return M


# --- objeto ---------------------------------------------------------------------------------------------
class Objeto:
    def __init__(self, glb, paso=0.0006):
        j, b = leer_glb(glb)
        self.j, self._b = j, b
        padre = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
        self.idx = {n.get("name"): i for i, n in enumerate(j["nodes"])}

        def mundo(i, giros=None):
            M = np.eye(4)
            while i is not None:
                L = _trs(j["nodes"][i])
                nm = j["nodes"][i].get("name")
                if giros and nm in giros:
                    G = np.eye(4); G[:3, :3] = rot([0, 0, 1], -giros[nm]); L = L @ G
                M = L @ M
                i = padre.get(i)
            return M
        self._mundo = mundo
        self.agarre = mundo(self.idx["AGARRE"])
        self.contactos = {n["name"][9:]: n["name"] for n in j["nodes"] if n.get("name", "").startswith("CONTACTO_")}
        self.moviles = {n["name"]: n.get("extras", {}).get("recorrido_rad", 0.0) for n in j["nodes"]
                        if n.get("extras", {}).get("recorrido_rad")}
        tris = []
        for i, n in enumerate(j["nodes"]):
            if "mesh" not in n:
                continue
            M = mundo(i)
            for p in j["meshes"][n["mesh"]]["primitives"]:
                V = accesor(j, b, p["attributes"]["POSITION"]).astype(float)
                F = accesor(j, b, p["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in p else np.arange(len(V)).reshape(-1, 3)
                tris.append((V @ M[:3, :3].T + M[:3, 3])[F])
        self.T = np.concatenate(tris)
        self._sdf(paso)

    def contacto(self, dedo, giros=None):
        return self._mundo(self.idx[self.contactos[dedo]], giros)[:3, 3]

    def _sdf(self, paso):
        T = self.T
        lo = T.reshape(-1, 3).min(0) - 0.01; hi = T.reshape(-1, 3).max(0) + 0.01
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ys = lo[1] + paso * np.arange(n[1]); zs = lo[2] + paso * np.arange(n[2])
        Y, Z = np.meshgrid(ys, zs, indexing="ij")
        dentro = np.zeros(n, bool)
        xs = lo[0] + paso * np.arange(n[0])
        # paridad de cruces de un rayo +x por columna (y, z): mallas cerradas
        cuenta = np.zeros((n[0], n[1], n[2]), np.int16)
        for t in T:
            a, b_, c = t
            mn = np.minimum(np.minimum(a, b_), c); mx = np.maximum(np.maximum(a, b_), c)
            iy = slice(max(int((mn[1] - lo[1]) / paso), 0), min(int((mx[1] - lo[1]) / paso) + 2, n[1]))
            iz = slice(max(int((mn[2] - lo[2]) / paso), 0), min(int((mx[2] - lo[2]) / paso) + 2, n[2]))
            py, pz = Y[iy, iz], Z[iy, iz]
            # baricéntricas en el plano yz
            v0 = c[1:] - a[1:]; v1 = b_[1:] - a[1:]
            d = v0[0] * v1[1] - v0[1] * v1[0]
            if abs(d) < 1e-16:
                continue
            wy, wz = py - a[1], pz - a[2]
            u = (wy * v1[1] - wz * v1[0]) / d
            v = (v0[0] * wz - v0[1] * wy) / d
            ok = (u >= 0) & (v >= 0) & (u + v <= 1)
            if not ok.any():
                continue
            xh = a[0] + u * (c[0] - a[0]) + v * (b_[0] - a[0])
            ix = np.clip(((xh - lo[0]) / paso).astype(int) + 1, 0, n[0])
            sub = cuenta[:, iy, iz]
            for (k, l) in zip(*np.nonzero(ok)):
                if ix[k, l] < n[0]:
                    sub[ix[k, l]:, k, l] += 1
        dentro = (cuenta % 2) == 1
        fuera_d = ndimage.distance_transform_edt(~dentro) * paso
        dentro_d = ndimage.distance_transform_edt(dentro) * paso
        self.sdf_grid = np.where(dentro, -dentro_d, fuera_d).astype(np.float32)
        self.lo, self.paso = lo, paso
        del xs

    def extension(self, origen, eje, maxd=0.08):
        """Distancia desde `origen` (adentro) hasta la superficie a lo largo de ±eje (promedio de los dos lados)."""
        ts = np.linspace(0, maxd, 400)
        d = []
        for s_ in (1, -1):
            v = self.sdf(origen + s_ * np.outer(ts, eje))
            k = np.argmax(v > 0)
            d.append(ts[k] if v[k] > 0 else maxd)
        return float(np.mean(d))

    def sdf(self, P):
        """Distancia con signo (negativa adentro) en coordenadas del objeto."""
        c = ((P - self.lo) / self.paso).T
        return ndimage.map_coordinates(self.sdf_grid, c, order=1, mode="nearest")


# --- mano -----------------------------------------------------------------------------------------------
class Mano:
    def __init__(self, glb, lado="Right"):
        self.lado = lado
        M = Modelo(glb)
        j = M.j
        sk = j["skins"][0]
        self.nombres = [j["nodes"][k]["name"] for k in sk["joints"]]
        ibm = accesor(j, M.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.H = {n: np.linalg.inv(ibm[i])[:3, 3] for i, n in enumerate(self.nombres)}
        idx = {n.get("name"): i for i, n in enumerate(j["nodes"])}
        padre = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
        self.padre = {n: j["nodes"][padre[idx[n]]]["name"] for n in self.nombres if idx[n] in padre}
        pieza = "Mano" + lado[0]
        gp = [q for m in j["meshes"] for q in m["primitives"]]
        p = next(pr for pr, g in zip(M.prims, gp) if g.get("extras", {}).get("pieza") == pieza)
        self.V, self.F = p.pos, p.indices.reshape(-1, 3)
        Wf = np.zeros((len(self.V), len(self.nombres)))
        for q in range(4):
            np.add.at(Wf, (np.arange(len(self.V)), p.joints[:, q]), p.weights[:, q])
        self.huesos = [lado + "Hand"] + [lado + d + f for d in DEDOS for f in FAL] + \
                      [lado + "Thumb" + f for f in ("Metacarpal", "Proximal", "Distal")]
        cols = [self.nombres.index(h) for h in self.huesos]
        self.W = Wf[:, cols] / np.maximum(Wf[:, cols].sum(1, keepdims=True), 1e-9)
        H = self.H; L = lado
        self.s = 1.0 if lado == "Left" else -1.0
        # marco de la mano en reposo: x = de la muñeca a los nudillos, y = del meñique al índice, n = normal de la palma
        nud = np.mean([H[L + d + "Proximal"] for d in DEDOS], 0)
        self.x = (nud - H[L + "Hand"]) / np.linalg.norm(nud - H[L + "Hand"])
        y = H[L + "IndexProximal"] - H[L + "LittleProximal"]; y -= self.x * (y @ self.x); self.y = y / np.linalg.norm(y)
        self.z = np.cross(self.x, self.y)
        self.n_palma = np.array([0.0, -1.0, 0.0])         # pose T: palma abajo
        self.centro_palma = H[L + "Hand"] + 0.55 * (nud - H[L + "Hand"])
        # ejes de flexión (reposo): la punta va hacia la palma
        self.eje = {}
        for d in DEDOS:
            dd = H[L + d + "Distal"] - H[L + d + "Proximal"]
            self.eje[d] = np.cross(dd / np.linalg.norm(dd), self.n_palma)
        td = H[L + "ThumbDistal"] - H[L + "ThumbMetacarpal"]; td /= np.linalg.norm(td)
        self.eje["Thumb"] = np.cross(td, self.n_palma)
        # yemas: vértice de la cara de la palma más cercano a 2/3 de la falange distal
        self.yema = {}
        for d in DEDOS + ("Thumb",):
            dist = L + d + "Distal"
            k = self.huesos.index(dist)
            cand = np.where(self.W[:, k] > 0.6)[0]
            if len(cand) == 0:
                continue
            lado_palma = (self.V[cand] - H[dist]) @ self.n_palma
            self.yema[d] = cand[np.argsort(-lado_palma)[: max(3, len(cand) // 8)]]

    def rotaciones(self, cierre, pulgar):
        """cierre: {dedo: (ang_prox, ang_resto)} en rad; pulgar: (oposición, flexión). Devuelve {hueso: R local}."""
        L = self.lado; R = {}
        for d in DEDOS:
            a0, a1 = cierre[d]
            R[L + d + "Proximal"] = rot(self.eje[d], a0)
            R[L + d + "Intermediate"] = rot(self.eje[d], a1 * 0.62)
            R[L + d + "Distal"] = rot(self.eje[d], a1 * 0.38)
        op, fl = pulgar
        R[L + "ThumbMetacarpal"] = rot(-self.n_palma, -self.s * op)     # hacia los dedos
        R[L + "ThumbProximal"] = rot(self.eje["Thumb"], fl * 0.5)
        R[L + "ThumbDistal"] = rot(self.eje["Thumb"], fl * 0.5)
        return R

    def posar(self, R):
        """Skinning lineal (marco de reposo; la muñeca queda fija)."""
        H = self.H
        Rw, Tw = {}, {}
        for h in self.huesos:
            p = self.padre.get(h)
            if h == self.lado + "Hand" or p not in Rw:
                Rw[h] = R.get(h, np.eye(3)); Tw[h] = H[h]
            else:
                Rw[h] = Rw[p] @ R.get(h, np.eye(3))
                Tw[h] = Tw[p] + Rw[p] @ (H[h] - H[p])
        V = np.zeros_like(self.V)
        for k, h in enumerate(self.huesos):
            w = self.W[:, k]
            m = w > 0
            if m.any():
                V[m] += w[m, None] * ((self.V[m] - H[h]) @ Rw[h].T + Tw[h])
        return V


# --- solucionador ---------------------------------------------------------------------------------------
class Agarre:
    def __init__(self, mano: Mano, obj: Objeto, rodean=("Middle", "Ring", "Little"), contactos=None):
        self.m, self.o = mano, obj
        self.rodean = rodean
        self.contactos = contactos if contactos is not None else list(obj.contactos)
        m = mano
        # pose inicial: AGARRE alineado al marco de la mano, mango del lado de la palma
        Bm = np.stack([m.x, m.y, m.z], 1)
        Ba = obj.agarre[:3, :3]
        self.R0 = Bm @ Ba.T                               # objeto → mundo (reposo de la mano)
        # el mango va bajo la palma, cerca de los nudillos (los dedos lo rodean de enfrente hacia el otro lado):
        # centro del mango = nudillos − x·(radio del mango) + n·(medio grosor de palma + radio del mango).
        # El radio del mango sale de la distancia con signo en el origen de AGARRE (profundidad = medio grosor).
        o0 = obj.agarre[:3, 3]
        ext = {k: obj.extension(o0, obj.agarre[:3, i]) for i, k in ((0, "x"), (2, "z"))}
        self.r_mango = ext
        nud = np.mean([m.H[m.lado + d + "Proximal"] for d in DEDOS], 0)
        medio_palma = float(np.median(np.abs((m.V - m.centro_palma) @ m.n_palma)))
        # de enfrente (x) a la mitad del mango le toca quedar bajo los nudillos; de lado (z), bajo la palma
        centro = nud - m.x * ext["x"] + m.n_palma * (medio_palma + ext["z"])
        self.t0 = centro - self.R0 @ obj.agarre[:3, 3]

    peso_contacto = 2e5

    def desempacar(self, x):
        R = rvec(x[0:3]) @ self.R0
        t = self.t0 + x[3:6]
        cierre = {}
        k = 6
        for d in DEDOS:
            cierre[d] = (x[k], x[k + 1]); k += 2
        pulgar = (x[k], x[k + 1])
        return R, t, cierre, pulgar

    def costo(self, x, giros=None, detalle=False, fijo_obj=None):
        m, o = self.m, self.o
        R, t, cierre, pulgar = self.desempacar(x)
        if fijo_obj is not None:
            R, t = fijo_obj
        V = m.posar(m.rotaciones(cierre, pulgar))
        Vo = (V - t) @ R                                  # a coordenadas del objeto
        sd = o.sdf(Vo)
        pen = np.sum(np.clip(0.0004 - sd, 0, None) ** 2) * 2e5
        rod = 0.0
        # rodear: la yema toca la superficie Y queda del otro lado del mango (más allá de su eje, lejos de la palma);
        # sin lo segundo, el dedo "resuelve" acostándose plano sobre la cara del mango
        eje_o = o.agarre[:3, 3]; ey = o.agarre[:3, 1]
        dp = R.T @ m.n_palma                                   # de la palma hacia el objeto, en coords del objeto
        for d in self.rodean:
            if d in m.yema:
                Y = Vo[m.yema[d]]
                rel = Y - eje_o; rel -= np.outer(rel @ ey, ey)  # componente perpendicular al eje del mango
                rod += np.mean(np.clip(sd[m.yema[d]] - 0.0004, 0, None) ** 2) * 3e4
                rod += np.mean(np.clip(0.004 - rel @ dp, 0, None) ** 2) * 3e4
        # palma apoyada: los vértices de la cara de la palma más cerca del objeto deben tocar
        palma = np.argsort((m.V - m.centro_palma) @ m.n_palma)[-40:]
        apoyo = (np.min(sd[palma]) - 0.0006) ** 2 * 3e4
        cont = 0.0
        for d in self.contactos:
            if d in m.yema:
                p = o.contacto(d, giros)
                cont += np.min(np.linalg.norm(Vo[m.yema[d]] - p, axis=1)) ** 2 * self.peso_contacto
        pul = np.mean(np.clip(sd[m.yema["Thumb"]] - 0.001, 0, None) ** 2) * 1e4 if "Thumb" in m.yema else 0.0
        reg = np.sum(x[0:3] ** 2) * 0.5
        c = pen + rod + apoyo + cont + pul + reg
        if detalle:
            return {"total": c, "penetracion": pen, "rodear": rod, "palma": apoyo, "contactos": cont, "pulgar": pul,
                    "min_sdf": float(sd.min()), "dist_contacto": {d: float(np.min(np.linalg.norm(Vo[m.yema[d]] - o.contacto(d, giros), axis=1)))
                                                                   for d in self.contactos if d in m.yema}}
        return c

    # límites anatómicos (rad) y de colocación del objeto: el optimizador no puede "resolver" girando el arma o
    # doblando un dedo al revés
    GIRO_OBJ, MOVER_OBJ = 0.35, 0.025
    LIM_PROX, LIM_RESTO = (-0.15, 1.6), (0.0, 2.0)
    LIM_OPOS, LIM_FLEX = (-0.3, 1.1), (0.0, 1.3)

    def limites(self):
        b = [(-self.GIRO_OBJ, self.GIRO_OBJ)] * 3 + [(-self.MOVER_OBJ, self.MOVER_OBJ)] * 3
        for _ in DEDOS:
            b += [self.LIM_PROX, self.LIM_RESTO]
        return b + [self.LIM_OPOS, self.LIM_FLEX]

    def resolver(self, iter_=3):
        x = np.zeros(6 + 2 * len(DEDOS) + 2)
        k = 6
        for d in DEDOS:
            x[k], x[k + 1] = (0.2, 0.3) if d in self.contactos else (0.6, 0.6)
            k += 2
        x[k], x[k + 1] = 0.3, 0.3
        b = self.limites()
        for _ in range(iter_):
            r = optimize.minimize(self.costo, x, method="Powell", bounds=b,
                                  options={"maxiter": 6000, "xtol": 1e-4, "ftol": 1e-8})
            x = r.x
        # afinado: la yema de contacto llega a su punto (peso alto), con el objeto y los otros dedos casi fijos
        if self.contactos:
            idx = [6 + 2 * DEDOS.index(d) + i for d in self.contactos if d in DEDOS for i in (0, 1)] + [3, 4, 5]
            pc, self.peso_contacto = self.peso_contacto, 2e6

            def f(v):
                y = x.copy(); y[idx] = v
                return self.costo(y)
            r = optimize.minimize(f, x[idx], method="Powell", bounds=[b[i] for i in idx], options={"xtol": 1e-5, "ftol": 1e-9})
            x = x.copy(); x[idx] = r.x
            self.peso_contacto = pc
        self.x = x
        return x

    def accion(self, movil, n=7):
        """El nodo móvil recorre su ángulo; el/los dedos de contacto lo siguen (el objeto y los demás dedos quedan)."""
        R, t, cierre, pulgar = self.desempacar(self.x)
        rec = self.o.moviles[movil]
        out = []
        xi = self.x.copy()
        for a in np.linspace(0, rec, n):
            giros = {movil: a}
            idx = [6 + 2 * DEDOS.index(d) + i for d in self.contactos for i in (0, 1)]

            def f(v):
                y = xi.copy(); y[idx] = v
                pc, self.peso_contacto = self.peso_contacto, 2e6
                c = self.costo(y, giros=giros, fijo_obj=(R, t))
                self.peso_contacto = pc
                return c
            bl = [self.limites()[i] for i in idx]
            r = optimize.minimize(f, xi[idx], method="Powell", bounds=bl, options={"xtol": 1e-4, "ftol": 1e-8})
            xi[idx] = r.x
            out.append((float(a), xi.copy()))
        return out

    def resultado(self, x=None):
        x = self.x if x is None else x
        m = self.m
        R, t, cierre, pulgar = self.desempacar(x)
        Rl = m.rotaciones(cierre, pulgar)
        quats = {h: a_quat(M).tolist() for h, M in Rl.items()}
        # objeto (raíz) → hueso de la mano en reposo (sin rotación): T = [R | t − H_mano]
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t - m.H[m.lado + "Hand"]
        return {"rotaciones": quats, "objeto_en_mano": T.tolist()}


def guardar(ruta, datos):
    with open(ruta, "w") as f:
        json.dump(datos, f, indent=1)


def lamina(A: Agarre, x, ruta, giros=None, vistas=((0, 0), (180, 0), (0, 89.9), (35, 25)), tam=360, zoom=1.0, marco="objeto",
           centro=None, solo_objeto_cerca=None):
    """Lámina de control: mano (piel) y objeto (gris). marco="objeto": vistas en ejes del objeto (de lado = perfil del
    arma, x adelante, y arriba); marco="mano": en el marco de reposo de la mano."""
    from PIL import Image
    from copox.render.raster import rasterizar
    from copox.medicion.camara import Camara
    m, o = A.m, A.o
    R, t, cierre, pulgar = A.desempacar(x)
    Vm = m.posar(m.rotaciones(cierre, pulgar))
    To = o.T if not giros else _tris_girados(o, giros)
    if marco == "objeto":
        Vm = (Vm - t) @ R; Tw = To
    else:
        Tw = To @ R.T + t
    tris = np.concatenate([Vm[m.F], Tw]); col = np.r_[np.zeros(len(m.F)), np.ones(len(Tw))]
    c = (Vm.mean(0) + Tw.reshape(-1, 3).mean(0)) / 2 if centro is None else np.asarray(centro, float)
    ims = []
    for yaw, el in vistas:
        cam = Camara(yaw, el, 0, None, objetivo=tuple(c))
        x_, y_, z_ = cam.proyectar(tris.reshape(-1, 3))
        esc = tam / (0.17 / zoom)
        X = (tam / 2 + x_ * esc).reshape(-1, 3); Y = (tam / 2 - y_ * esc).reshape(-1, 3); Z = z_.reshape(-1, 3)
        tri, bary, prof = rasterizar(X, Y, Z, (tam, tam))
        T3 = tris; N = np.cross(T3[:, 1] - T3[:, 0], T3[:, 2] - T3[:, 0]); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        luz = np.abs(N @ cam.base()[2])
        img = np.full((tam, tam, 3), 236, np.uint8)
        f = tri >= 0
        base = np.where(col[tri[f]][:, None] > 0, [[70, 70, 78]], [[240, 190, 150]])
        img[f] = np.clip(base * (0.45 + 0.55 * luz[tri[f]][:, None]), 0, 255).astype(np.uint8)
        ims.append(img)
    Image.fromarray(np.hstack(ims)).save(ruta)


def _tris_girados(o: Objeto, giros):
    j = o.j
    tris = []
    for i, n in enumerate(j["nodes"]):
        if "mesh" not in n:
            continue
        M = o._mundo(i, giros)
        from copox.medicion.gltf import leer_glb as _l
        for p in j["meshes"][n["mesh"]]["primitives"]:
            V = accesor(j, o._b, p["attributes"]["POSITION"]).astype(float)
            F = accesor(j, o._b, p["indices"]).reshape(-1, 3).astype(np.int64)
            tris.append((V @ M[:3, :3].T + M[:3, 3])[F])
    return np.concatenate(tris)


def escribir_en_personaje(E, nombre, res, lado="Right", t_apretar=0.10, t_sostener=0.06, t_soltar=0.16):
    """Mete el agarre en el GLB del personaje (re.Editor E):
      - nodo "AGARRE_<NOMBRE>" hijo del hueso de la mano: transformación de la RAÍZ del objeto respecto a la mano
        (en Godot queda pegado al hueso; el controlador pone ahí el objeto);
      - clip "<Nombre>_Agarre-loop": dedos sosteniendo (solo huesos de la mano);
      - clip "<Nombre>_Accion": aprieta (cuadros de la acción), sostiene y suelta;
      - extras del nodo: nodo móvil, ángulos y tiempos de la acción (para mover el gatillo en sincronía)."""
    j = E.j
    idx = {n.get("name"): i for i, n in enumerate(j["nodes"])}
    T = np.array(res["objeto_en_mano"])
    nodo = {"name": f"AGARRE_{nombre.upper()}", "translation": T[:3, 3].tolist(), "rotation": a_quat(T[:3, :3]).tolist()}
    acc = res.get("accion")
    cuadros = acc["cuadros"] if acc else []
    n_c = len(cuadros)
    ts_ap = np.linspace(0, t_apretar, n_c) if n_c else np.array([])
    tiempos = list(ts_ap) + [t_apretar + t_sostener] + list(t_apretar + t_sostener + np.linspace(0, t_soltar, n_c)[1:])
    angulos = [c["angulo"] for c in cuadros] + ([cuadros[-1]["angulo"]] if n_c else []) + [c["angulo"] for c in cuadros[::-1][1:]]
    if acc:
        nodo["extras"] = {"accion_nodo": acc["nodo"], "accion_tiempos": [float(t) for t in tiempos],
                          "accion_angulos": [float(a) for a in angulos], "clip_agarre": f"{nombre}_Agarre",
                          "clip_accion": f"{nombre}_Accion"}
    j["nodes"].append(nodo)
    j["nodes"][idx[lado + "Hand"]].setdefault("children", []).append(len(j["nodes"]) - 1)

    def clip(nombre_clip, ts, poses):
        it = E._add(np.asarray(ts, np.float32), "SCALAR")
        j["accessors"][it]["min"] = [float(ts[0])]; j["accessors"][it]["max"] = [float(ts[-1])]
        anim = {"name": nombre_clip, "samplers": [], "channels": []}
        for h in poses[0]:
            q = np.array([p[h] for p in poses], np.float32)
            anim["samplers"].append({"input": it, "output": E._add(q, "VEC4"), "interpolation": "LINEAR"})
            anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": idx[h], "path": "rotation"}})
        j["animations"] = [a for a in j["animations"] if a.get("name") != nombre_clip] + [anim]

    clip(f"{nombre}_Agarre-loop", [0.0, 1.0], [res["rotaciones"], res["rotaciones"]])
    if acc:
        poses = [c["rotaciones"] for c in cuadros] + [cuadros[-1]["rotaciones"]] + [c["rotaciones"] for c in cuadros[::-1][1:]]
        clip(f"{nombre}_Accion", tiempos, poses)
    E.b = bytes(E.out)
    E.log.append({"operacion": f"agarre {nombre}", "nodo": nodo["name"], "clips": [f"{nombre}_Agarre-loop", f"{nombre}_Accion"]})


# --- solucionador por cierre hasta contacto (V37b) ------------------------------------------------------
class AgarreCierre(Agarre):
    """Agarre robusto y determinista, como lo haría una mano real:
      1. Colocación del objeto: búsqueda en rejilla (no gradiente) alrededor de la pose inicial — desplazamiento a lo
         largo de los dedos, de la normal de la palma y del mango, y un giro del mango sobre la palma.
      2. Cada dedo que RODEA se cierra articulación por articulación hasta tocar: se avanza en pasos pequeños y,
         cuando una falange toca la superficie, se congelan esa articulación y las anteriores; las siguientes siguen
         cerrando (así el dedo envuelve en vez de quedarse plano o atravesar).
      3. Dedos con CONTACTO (índice en el gatillo): rejilla 2D (proximal, resto) que lleva la yema al punto sin
         penetrar, y afinado acotado.
      4. Pulgar: rejilla de oposición + cierre hasta contacto.
    Puntaje de colocación = penetración (veto práctico) + palma sin tocar + dedos que no envuelven + contacto lejos."""

    LIM3 = (1.55, 1.75, 1.2)          # proximal, intermedia, distal (rad)
    PASO = 0.03
    TOL_PEN = 0.0006                  # penetración tolerada (m) — la malla de 0.6 mm de la SDF
    TOCA = 0.0008                     # se considera contacto
    PIEL = 0.0025                     # los dedos chibi son blandos: la yema/falange puede hundirse 2.5 mm al apretar

    def __init__(self, mano, obj, rodean=("Middle", "Ring", "Little"), contactos=None):
        super().__init__(mano, obj, rodean, contactos)
        m = self.m; L = m.lado
        dom = np.argmax(m.W, 1)
        self.seg = {}
        for d in DEDOS:
            ks = [m.huesos.index(L + d + f) for f in FAL]
            self.seg[d] = [np.where(dom == k)[0] for k in ks]
        kt = [m.huesos.index(L + "Thumb" + f) for f in ("Metacarpal", "Proximal", "Distal")]
        self.seg["Thumb"] = [np.where(dom == k)[0] for k in kt]
        self.sub = {d: np.unique(np.concatenate(self.seg[d])) for d in self.seg}
        dedos = np.concatenate([self.sub[d] for d in self.sub])
        self.rigido = np.setdiff1d(np.arange(len(m.V)), dedos)
        self.palma = np.argsort((m.V - m.centro_palma) @ m.n_palma)[-60:]
        # eje de abducción palmar: a lo largo del metacarpo del pulgar, con el signo que lleva la punta hacia la palma
        td = m.H[L + "ThumbDistal"] - m.H[L + "ThumbMetacarpal"]; td = td / np.linalg.norm(td)
        e = np.cross(m.n_palma, td); e /= np.linalg.norm(e)
        self.eje_abd = e if (rot(e, 0.3) @ td) @ m.n_palma > 0 else -e

    # rotaciones con 3 ángulos por dedo y (oposición, flexión1, flexión2) en el pulgar
    def rot3(self, ang, pulg):
        m = self.m; L = m.lado; R = {}
        for d in DEDOS:
            for f, a in zip(FAL, ang.get(d, (0, 0, 0))):
                R[L + d + f] = rot(m.eje[d], a)
        op, f1, f2 = pulg[:3]
        abd = pulg[3] if len(pulg) > 3 else 0.0
        # abd: abducción palmar (el pulgar sale del plano de la palma hacia el lado de la palma, para cruzar el mango)
        R[L + "ThumbMetacarpal"] = rot(self.eje_abd, abd) @ rot(-m.n_palma, -m.s * op)
        R[L + "ThumbProximal"] = rot(m.eje["Thumb"], f1)
        R[L + "ThumbDistal"] = rot(m.eje["Thumb"], f2)
        return R

    def _posar_sub(self, R, idx):
        """Skinning lineal sólo de los vértices idx."""
        m = self.m; H = m.H
        Rw, Tw = {}, {}
        for h in m.huesos:
            p = m.padre.get(h)
            if h == m.lado + "Hand" or p not in Rw:
                Rw[h] = R.get(h, np.eye(3)); Tw[h] = H[h]
            else:
                Rw[h] = Rw[p] @ R.get(h, np.eye(3)); Tw[h] = Tw[p] + Rw[p] @ (H[h] - H[p])
        V0 = m.V[idx]; W = m.W[idx]; out = np.zeros_like(V0)
        for k, h in enumerate(m.huesos):
            w = W[:, k]; s = w > 0
            if s.any():
                out[s] += w[s, None] * ((V0[s] - H[h]) @ Rw[h].T + Tw[h])
        return out

    def _sd(self, V, R, t, giros=None):
        return self.o.sdf((V - t) @ R)

    def _cerrar(self, d, R, t, base=(0.0, 0.0, 0.0), pesos=(1.0, 1.0, 0.75)):
        """Cierra el dedo d hasta contacto. Devuelve (ángulos, min_sdf por falange)."""
        a = list(base); vivo = [True, True, True]
        idx = self.sub[d]; pos = {v: i for i, v in enumerate(idx)}
        segs = [np.array([pos[v] for v in s]) for s in self.seg[d]]
        lim = self.LIM3
        sd = self._sd(self._posar_sub(self.rot3({d: a}, (0, 0, 0)), idx), R, t)
        for _ in range(200):
            if not any(vivo):
                break
            b = [a[k] + (self.PASO * pesos[k] if vivo[k] else 0.0) for k in range(3)]
            b = [min(b[k], lim[k]) for k in range(3)]
            sdn = self._sd(self._posar_sub(self.rot3({d: b}, (0, 0, 0)), idx), R, t)
            choca = [len(s) and sdn[s].min() < -self.PIEL for s in segs]
            if any(choca):
                kmax = max(k for k in range(3) if choca[k])
                for k in range(kmax + 1):
                    vivo[k] = False          # la falange k tocó: congela k y anteriores; las siguientes siguen
                continue
            a = b; sd = sdn
            for k in range(3):
                if a[k] >= lim[k] - 1e-9:
                    vivo[k] = False
        return a, [float(sd[s].min()) if len(s) else 9.0 for s in segs]

    def _pulgar(self, R, t):
        mejor = None
        idx = self.sub["Thumb"]; pos = {v: i for i, v in enumerate(idx)}
        yema = np.array([pos[v] for v in self.m.yema["Thumb"] if v in pos])
        for op in np.linspace(-0.3, 1.1, 15):
            f = [0.0, 0.0]; vivo = [True, True]
            sd = self._sd(self._posar_sub(self.rot3({}, (op, 0, 0)), idx), R, t)
            if sd.min() < -self.TOL_PEN:
                continue
            for _ in range(80):
                if not any(vivo):
                    break
                g = [f[k] + (self.PASO if vivo[k] else 0) for k in range(2)]
                g = [min(g[0], 1.0), min(g[1], 1.2)]
                sdn = self._sd(self._posar_sub(self.rot3({}, (op, g[0], g[1])), idx), R, t)
                if sdn.min() < -self.TOL_PEN:
                    vivo = [False, False]; continue
                f = g; sd = sdn
                vivo = [f[0] < 1.0, f[1] < 1.2]
            c = (max(sd[yema].min(), 0) if len(yema) else 0) * 1e3 + 0.05 * abs(op - 0.5)
            if mejor is None or c < mejor[0]:
                mejor = (c, (float(op), float(f[0]), float(f[1])))
        return mejor[1] if mejor else (0.3, 0.2, 0.2)

    def _pulgar_contacto(self, R, t):
        """Pulgar a su CONTACTO_Thumb (p. ej. el costado opuesto del mango, bajo la corredera) sin penetrar:
        rejilla de (oposición, abducción) y afinado de los 4 grados (oposición, flexión 1, flexión 2, abducción)."""
        p = self.o.contacto("Thumb")
        idx = self.sub["Thumb"]; pos = {v: i for i, v in enumerate(idx)}
        yema = np.array([pos[v] for v in self.m.yema["Thumb"] if v in pos])
        # la base del pulgar (metacarpo) se apoya en el lomo del mango y puede hundirse lo de la piel; el castigo de
        # penetración cuenta sólo las falanges que se mueven
        mov = np.array([pos[v] for v in np.concatenate(self.seg["Thumb"][1:])])

        def c(v):
            Vo = (self._posar_sub(self.rot3({}, tuple(v)), idx) - t) @ R
            sd = self.o.sdf(Vo[mov])
            dist = np.min(np.linalg.norm(Vo[yema] - p, axis=1))
            return dist ** 2 * 1e6 + np.sum(np.clip(-self.PIEL - sd, 0, None) ** 2) * 1e7
        b = [(-0.4, 1.2), (0.0, 1.0), (0.0, 1.2), (-0.9, 1.4)]
        G = [(c((op, f, f, ab)), (op, f, f, ab)) for op in np.linspace(-0.4, 1.2, 9)
             for ab in np.linspace(-0.9, 1.4, 12) for f in (0.0, 0.3, 0.6, 0.9)]
        x0 = min(G, key=lambda g: g[0])[1]
        r = optimize.minimize(c, x0, method="Powell", bounds=b, options={"xtol": 1e-4, "ftol": 1e-10})
        Vo = (self._posar_sub(self.rot3({}, tuple(r.x)), idx) - t) @ R
        self.dist_pulgar = float(np.min(np.linalg.norm(Vo[yema] - p, axis=1)))
        self.pen_pulgar = float(-min(self.o.sdf(Vo[mov]).min(), 0))
        return tuple(float(v) for v in r.x)

    def _contacto(self, d, R, t, giros=None, x0=None):
        """Lleva la yema de d a su CONTACTO sin penetrar (rejilla + afinado)."""
        p = self.o.contacto(d, giros)
        idx = self.sub[d]; pos = {v: i for i, v in enumerate(idx)}
        yema = np.array([pos[v] for v in self.m.yema[d] if v in pos])

        def c(v):
            a0, a1 = v
            ang = (a0, a1 * 0.62, a1 * 0.38)
            Vo = (self._posar_sub(self.rot3({d: ang}, (0, 0, 0)), idx) - t) @ R
            sd = self.o.sdf(Vo)
            dist = np.min(np.linalg.norm(Vo[yema] - p, axis=1))
            return dist ** 2 * 1e6 + np.sum(np.clip(-self.TOL_PEN * 2 - sd, 0, None) ** 2) * 1e7
        if x0 is None:
            G = [(c((a0, a1)), a0, a1) for a0 in np.linspace(-0.1, 1.5, 17) for a1 in np.linspace(0, 1.9, 17)]
            x0 = min(G)[1:]
        r = optimize.minimize(c, x0, method="Powell", bounds=[(-0.15, 1.6), (0, 2.0)], options={"xtol": 1e-4, "ftol": 1e-10})
        a0, a1 = r.x
        Vo = (self._posar_sub(self.rot3({d: (a0, a1 * .62, a1 * .38)}, (0, 0, 0)), idx) - t) @ R
        return (float(a0), float(a1 * 0.62), float(a1 * 0.38)), float(np.min(np.linalg.norm(Vo[yema] - p, axis=1))), (a0, a1)

    def _evaluar(self, R, t, completo=False):
        m = self.m
        sd_r = self._sd(m.V[self.rigido], R, t)
        pen = np.sum(np.clip(-self.TOL_PEN - sd_r, 0, None)) * 1e3
        sd_p = self._sd(m.V[self.palma], R, t)
        palma = max(sd_p.min() - self.TOCA, 0) * 1e3
        ang, toques = {}, {}
        envol = 0.0
        eje_o = self.o.agarre[:3, 3]; ey = self.o.agarre[:3, 1]; dp = R.T @ m.n_palma
        for d in self.rodean:
            a, sds = self._cerrar(d, R, t)
            ang[d] = a; toques[d] = sds
            # envuelve: la yema queda más allá del eje del mango (lejos de la palma) y toca algo
            Vo = (self._posar_sub(self.rot3({d: a}, (0, 0, 0)), m.yema[d]) - t) @ R
            rel = Vo - eje_o; rel -= np.outer(rel @ ey, ey)
            envol += max(0.004 - float(np.max(rel @ dp)), 0) * 1e3 + max(min(sds) - self.TOCA, 0) * 1e3
        res = {"pen": pen, "palma": palma, "envol": envol, "ang": ang, "toques": toques}
        dist = 0.0
        if completo or True:
            for d in self.contactos:
                if d in DEDOS:
                    a, dd, v = self._contacto(d, R, t)
                    ang[d] = a; res.setdefault("dist", {})[d] = dd; res.setdefault("x_contacto", {})[d] = v
                    dist += dd * 1e3
        res["costo"] = pen * 10 + palma * 2 + envol + dist * 3
        return res

    def _apoyar(self, R, t):
        """Desliza el objeto a lo largo de la normal de la palma hasta que la mano rígida (palma, sin dedos ni
        pulgar) apenas lo toca: bisección sobre la penetración. Devuelve t ajustado."""
        n = self.m.n_palma; Vr = self.m.V[self.rigido]
        pen = lambda d: float(self._sd(Vr, R, t + n * d).min())
        lo, hi = -0.02, 0.04
        if pen(hi) < -self.TOL_PEN:
            return t + n * hi
        for _ in range(22):
            mid = 0.5 * (lo + hi)
            if pen(mid) < -self.TOL_PEN * 0.5:
                lo = mid
            else:
                hi = mid
        return t + n * hi

    def colocar(self, rejilla=None):
        m = self.m
        if rejilla is None:
            rejilla = dict(dx=np.arange(-0.016, 0.0121, 0.004), dy=np.arange(-0.008, 0.0321, 0.004),
                           giro=(-0.6, -0.45, -0.3, -0.15, 0.0, 0.15))
        c0 = self.R0 @ self.o.agarre[:3, 3] + self.t0           # centro del mango (mundo)
        mejor = None
        for g in rejilla["giro"]:
            R = rot(m.n_palma, g) @ self.R0
            for dx in rejilla["dx"]:
                for dy in rejilla["dy"]:
                    # girar alrededor del centro del mango, luego desplazar y apoyar en la palma
                    t = c0 - R @ self.o.agarre[:3, 3] + m.x * dx + m.y * dy
                    t = self._apoyar(R, t)
                    r = self._evaluar(R, t)
                    if mejor is None or r["costo"] < mejor[0]["costo"]:
                        mejor = (r, R, t, (dx, float((t - (c0 - R @ self.o.agarre[:3, 3] + m.x * dx + m.y * dy)) @ m.n_palma), dy, g))
        return mejor

    def resolver(self, iter_=1):
        r, R, t, prm = self.colocar()
        self.R, self.t, self.prm, self.eval = R, t, prm, r
        self.ang = dict(r["ang"])
        for d in DEDOS:
            self.ang.setdefault(d, (0.3, 0.3, 0.2))
        self.pulg = self._pulgar_contacto(R, t) if "Thumb" in self.o.contactos else self._pulgar(R, t)
        return r

    def accion(self, movil, n=7):
        rec = self.o.moviles[movil]
        out = []
        x0 = {d: self.eval.get("x_contacto", {}).get(d) for d in self.contactos}
        for a in np.linspace(0, rec, n):
            ang = dict(self.ang)
            for d in self.contactos:
                if d in DEDOS:
                    ang[d], dd, x0[d] = self._contacto(d, self.R, self.t, giros={movil: a}, x0=x0[d])
            out.append((float(a), ang))
        return out

    def resultado(self, ang=None):
        m = self.m
        ang = self.ang if ang is None else ang
        quats = {h: a_quat(M).tolist() for h, M in self.rot3(ang, self.pulg).items()}
        T = np.eye(4); T[:3, :3] = self.R; T[:3, 3] = self.t - m.H[m.lado + "Hand"]
        return {"rotaciones": quats, "objeto_en_mano": T.tolist()}

    def detalle(self):
        e = self.eval
        return {"penetracion": float(e["pen"]), "palma": float(e["palma"]), "envolver": float(e["envol"]),
                "dist_contacto_mm": {d: round(v * 1e3, 2) for d, v in e.get("dist", {}).items()},
                "colocacion_mm_rad": [round(float(v), 4) for v in self.prm],
                "angulos_grados": {d: [round(float(np.degrees(v)), 1) for v in a] for d, a in self.ang.items()},
                "pulgar_grados": [round(float(np.degrees(v)), 1) for v in self.pulg],
                **({"pulgar_dist_mm": round(self.dist_pulgar * 1e3, 2), "pulgar_pen_mm": round(self.pen_pulgar * 1e3, 2)}
                   if hasattr(self, "dist_pulgar") else {})}
