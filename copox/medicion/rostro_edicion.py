"""Edición de rasgos faciales (derivado; nunca toca el original).

Deformaciones locales con caída suave sobre la malla de la cabeza, aplicadas
en reposo. Los deltas de morph se transforman con el jacobiano local, así los
gestos siguen funcionando. También edita texturas de tarjetas (iris, cejas).
Todas las medidas en ED salvo que se diga otra cosa; v hacia abajo desde la
línea de ojos (y = y_ojos − v·ED).
"""
from __future__ import annotations

import io
import json
import struct

import numpy as np
from PIL import Image

from .gltf import leer_glb, accesor


def _suave(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class Editor:
    def __init__(self, src: str):
        self.j, self.b = leer_glb(src)
        self.out = bytearray(self.b)
        self.log = []

    # --- utilidades de buffer -------------------------------------------
    def _add(self, arr, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr, np.float32)
        while len(self.out) % 4:
            self.out.append(0)
        v = {"buffer": 0, "byteOffset": len(self.out), "byteLength": arr.nbytes}
        if target:
            v["target"] = target
        self.out.extend(arr.tobytes()); self.j["bufferViews"].append(v)
        a = {"bufferView": len(self.j["bufferViews"]) - 1, "componentType": 5126, "count": len(arr), "type": typ}
        if minmax:
            a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def prims(self, material: str):
        for n in self.j["nodes"]:
            if "mesh" not in n:
                continue
            for p in self.j["meshes"][n["mesh"]]["primitives"]:
                if self.j["materials"][p["material"]]["name"] == material:
                    yield p

    def leer(self, p):
        V = accesor(self.j, self.b, p["attributes"]["POSITION"]).astype(float)
        T = [accesor(self.j, self.b, t["POSITION"]).astype(float) for t in p.get("targets", [])]
        return V, T

    def escribir(self, p, V, T):
        p["attributes"]["POSITION"] = self._add(V, "VEC3", 34962, True)
        for t, D in zip(p.get("targets", []), T):
            if np.abs(D).max() > 0:
                t["POSITION"] = self._add(D, "VEC3", None, True)
        # las normales se conservan (cambios locales pequeños); se anota
        self.b = bytes(self.out)

    # --- deformación genérica -------------------------------------------
    def deformar(self, material, campo, nombre, filtro=None, primitiva=None):
        """campo(V) -> (V_nuevo, J) con J (n,3,3) jacobiano local para transformar deltas de morph.
        ``primitiva(V) -> bool`` elige primitivas completas (p. ej. solo la cabeza)."""
        total = 0
        for p in self.prims(material):
            V, T = self.leer(p)
            if primitiva is not None and not primitiva(V):
                continue
            if filtro is not None and not filtro(V).any():
                continue
            V1, J = campo(V)
            T1 = [np.einsum("nij,nj->ni", J, D) for D in T]
            total += int((np.abs(V1 - V).max(1) > 1e-7).sum())
            self.escribir(p, V1, T1)
        self.log.append({"operacion": nombre, "material": material, "vertices_movidos": total})

    def textura(self, material, funcion, nombre):
        mat = next(m for m in self.j["materials"] if m["name"] == material)
        ti = mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        si = self.j["textures"][ti]["source"]
        im = self.j["images"][si]
        bv = self.j["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        rgba = np.asarray(Image.open(io.BytesIO(self.b[o:o + bv["byteLength"]])).convert("RGBA"))
        nuevo = funcion(rgba)
        buf = io.BytesIO(); Image.fromarray(nuevo).save(buf, "PNG")
        data = buf.getvalue()
        while len(self.out) % 4:
            self.out.append(0)
        self.j["bufferViews"].append({"buffer": 0, "byteOffset": len(self.out), "byteLength": len(data)})
        self.out.extend(data)
        im["bufferView"] = len(self.j["bufferViews"]) - 1
        self.b = bytes(self.out)
        self.log.append({"operacion": nombre, "material": material})

    def guardar(self, dst, nota=""):
        self.j["asset"].setdefault("extras", {})["copox_rostro"] = {"nota": nota, "operaciones": self.log}
        while len(self.out) % 4:
            self.out.append(0)
        self.j["buffers"] = [{"byteLength": len(self.out)}]
        js = json.dumps(self.j, separators=(",", ":"), ensure_ascii=False).encode()
        js += b" " * (-len(js) % 4)
        with open(dst, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(self.out)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack("<II", len(self.out), 0x004E4942)); f.write(self.out)


# --- campos concretos ------------------------------------------------------
def campo_compresion_mandibula(y_pivote, k, z_centro, z_ancho):
    """Comprime verticalmente lo que está bajo y_pivote (factor k) solo en la mitad frontal (caída en z)."""
    def f(V):
        V1 = V.copy()
        abajo = V[:, 1] < y_pivote
        wz = _suave((V[:, 2] - z_centro) / z_ancho)
        w = np.where(abajo, wz, 0.0)
        ky = 1 - (1 - k) * w
        V1[:, 1] = np.where(abajo, y_pivote - (y_pivote - V[:, 1]) * ky, V[:, 1])
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 1, 1] = ky
        return V1, J
    return f


def campo_boca(centro, rx, ry, ensanche, dy, z_min):
    """Ensancha (factor en x) y desplaza en y una región elíptica frontal alrededor de la boca."""
    cx, cy = centro
    def f(V):
        r = np.sqrt(((V[:, 0] - cx) / rx) ** 2 + ((V[:, 1] - cy) / ry) ** 2)
        w = np.clip(1 - r ** 2, 0, 1) ** 2 * (V[:, 2] > z_min)
        V1 = V.copy()
        V1[:, 0] = cx + (V[:, 0] - cx) * (1 + (ensanche - 1) * w)
        V1[:, 1] = V[:, 1] + dy * w
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = 1 + (ensanche - 1) * w
        return V1, J
    return f


def campo_rigido(factor_x=1.0, factor_y=1.0, centro=(0, 0, 0), delta=(0, 0, 0)):
    c = np.array(centro, float); d = np.array(delta, float)
    def f(V):
        V1 = (V - c) * np.array([factor_x, factor_y, 1.0]) + c + d
        J = np.tile(np.diag([factor_x, factor_y, 1.0]), (len(V), 1, 1))
        return V1, J
    return f


def campo_orejas(x_base, y_rango, dy, encoger, rampa=0.012):
    """Baja las orejas (dy) y reduce cuánto sobresalen (encoger sobre |x|-x_base)."""
    y0, y1 = y_rango
    def f(V):
        ax = np.abs(V[:, 0])
        w = _suave((ax - (x_base - rampa)) / rampa) * _suave((V[:, 1] - (y0 - 0.02)) / 0.02) * _suave(((y1 + 0.02) - V[:, 1]) / 0.02)
        V1 = V.copy()
        fuera = np.maximum(ax - x_base, 0)
        V1[:, 0] = np.sign(V[:, 0]) * (ax - fuera * (1 - encoger) * w)
        V1[:, 1] = V[:, 1] + dy * w
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = 1 - (1 - encoger) * w * (ax > x_base)
        return V1, J
    return f


def iris_ancho(factor=1.6, borde_px=14):
    """Agranda el iris en horizontal dentro del ojo: escala el interior alrededor del centro del iris
    y conserva el contorno del ojo."""
    def f(rgba):
        a = rgba[..., 3] > 0
        lum = rgba[..., :3].astype(float).mean(-1)
        H, W = a.shape
        iris = a & (lum < 110)
        ys, xs = np.nonzero(iris)
        cx = float(np.median(xs))
        # interior = alfa a más de borde_px del límite
        from collections import deque
        dist = np.full(a.shape, 10 ** 6, int)
        q = deque()
        for y, x in zip(*np.nonzero(~a)):
            dist[y, x] = 0; q.append((y, x))
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and dist[yy, xx] > dist[y, x] + 1:
                    dist[yy, xx] = dist[y, x] + 1; q.append((yy, xx))
        interior = dist > borde_px
        Y, X = np.mgrid[0:H, 0:W]
        xs_src = np.clip(np.round(cx + (X - cx) / factor).astype(int), 0, W - 1)
        src = rgba[Y, xs_src]
        out = rgba.copy()
        m = interior & (src[..., 3] > 0)
        out[m] = src[m]
        return out
    return f


def suavizar_region(E: "Editor", material: str, peso, iteraciones=8, lam=0.5, mu=-0.53, primitiva=None, nombre="suavizado"):
    """Suavizado Taubin local (no encoge) sobre vértices con peso(V) en [0,1]; conserva los morphs.
    Equivale a la idea de la skill Scully: aplanar bultos con caída suave y zona protegida (peso 0)."""
    total = 0
    for p in E.prims(material):
        V, T = E.leer(p)
        if primitiva is not None and not primitiva(V):
            continue
        I = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        w = np.clip(peso(V), 0, 1)
        if not (w > 0).any():
            continue
        # vecinos por aristas (soldando posiciones duplicadas para cruzar costuras de UV/normales)
        clave = np.round(V / 1e-6).astype(np.int64)
        _, rep = np.unique(clave, axis=0, return_inverse=True)
        rep = rep.ravel()
        e = np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]])
        e = rep[e]
        n = rep.max() + 1
        P = np.zeros((n, 3)); np.add.at(P, rep, V); cnt = np.bincount(rep, minlength=n)[:, None]; P /= cnt
        W = np.zeros(n); np.maximum.at(W, rep, w)
        deg = np.bincount(np.concatenate([e[:, 0], e[:, 1]]), minlength=n)[:, None]
        for it in range(iteraciones):
            for f in (lam, mu):
                S = np.zeros_like(P)
                np.add.at(S, e[:, 0], P[e[:, 1]]); np.add.at(S, e[:, 1], P[e[:, 0]])
                L = S / np.maximum(deg, 1) - P
                P = P + f * W[:, None] * L
        V1 = P[rep]
        total += int((np.abs(V1 - V).max(1) > 1e-7).sum())
        E.escribir(p, V1, T)
    E.log.append({"operacion": nombre, "material": material, "vertices_movidos": total})


def textura_ceja_barra(color=(82, 46, 23), grosor=0.55, inicio=0.05, fin=0.95, centro_v=0.55, inclinacion=0.06, chaflan=0.10, tam=512):
    """Textura nueva de ceja: barra gruesa casi recta (estilo ALTH). u=0 es el extremo interno.
    grosor/centro/inclinación en fracción del alto de la tarjeta; chaflán en fracción del largo."""
    def f(_rgba):
        H = W = tam
        Y, X = np.mgrid[0:H, 0:W]
        u = (X + 0.5) / W; v = (Y + 0.5) / H
        t = np.clip((u - inicio) / (fin - inicio), 0, 1)
        cv = centro_v + inclinacion * (0.5 - t)          # extremo interno un poco más bajo
        g = grosor * (1.0 - 0.15 * t)                      # se afina levemente hacia afuera
        dentro = (u >= inicio) & (u <= fin) & (np.abs(v - cv) <= g / 2)
        # chaflán en las esquinas externas (aspecto low-poly)
        ch = chaflan * (fin - inicio)
        esq = (u > fin - ch) & ((v - (cv - g / 2)) < (u - (fin - ch)) * (g / ch) * 0.6)
        dentro &= ~esq
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = color
        out[..., 3] = np.where(dentro, 255, 0)
        borde = dentro & (np.abs(v - (cv + g / 2)) < 0.035)  # sombra inferior sutil
        out[borde, :3] = (np.array(color) * 0.75).astype(np.uint8)
        return out
    return f


def campo_cubificar(centro, semiejes, fuerza=0.7, z_min=None):
    """Empuja los vértices de una protuberancia hacia la superficie de una caja (esquinas más duras)."""
    c = np.array(centro, float); h = np.array(semiejes, float)
    def f(V):
        d = V - c
        q = np.abs(d) / h
        dentro = (q.max(1) < 1.6) & ((V[:, 2] > z_min) if z_min is not None else True)
        n2 = np.sqrt((q ** 2).sum(1)); ninf = q.max(1)
        s = np.where(ninf > 1e-6, n2 / np.maximum(ninf, 1e-6), 1.0)
        s = np.minimum(s, 1.35)                       # no inflar más del 35 %
        w = fuerza * dentro * np.clip(1.6 - ninf, 0, 1)
        V1 = V.copy()
        V1 = c + d * (1 + (s - 1) * w)[:, None]
        V1[:, 2] = np.maximum(V1[:, 2], V[:, 2] - 1e-9) if z_min is None else V1[:, 2]
        J = np.tile(np.eye(3), (len(V), 1, 1)) * (1 + (s - 1) * w)[:, None, None]
        return V1, J
    return f


def campo_aplanar_oreja(y_rango, z_rango, x_craneo):
    """Hunde la oreja vieja contra el cráneo: |x| se limita a x_craneo(y) dentro de la región."""
    y0, y1 = y_rango; z0, z1 = z_rango
    def f(V):
        w = _suave((V[:, 1] - y0) / 0.01) * _suave((y1 - V[:, 1]) / 0.01) * _suave((V[:, 2] - z0) / 0.01) * _suave((z1 - V[:, 2]) / 0.01)
        lim = x_craneo(V[:, 1])
        ax = np.abs(V[:, 0])
        nuevo = np.minimum(ax, lim)
        V1 = V.copy()
        V1[:, 0] = np.sign(V[:, 0]) * (ax + (nuevo - ax) * w)
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


def agregar_caja(E: "Editor", nodo_nombre: str, material: str, centro, semiejes, hueso: str, inset=None, bisel=0.15):
    """Agrega una caja low-poly (con bisel y opcionalmente un panel hundido en la cara +X/-X) como
    primitiva nueva del nodo, pesada 100 % al hueso. Rellena morphs en cero para respetar glTF."""
    c = np.array(centro, float); h = np.array(semiejes, float)
    # caja biselada: octaedro truncado simple = cubo con esquinas recortadas en las aristas verticales
    b = bisel
    xs, ys, zs = (-1, 1), (-1, 1), (-1, 1)
    V, F = [], []
    def quad(a, bb, cc, d):
        i = len(V); V.extend([a, bb, cc, d]); F.extend([[i, i + 1, i + 2], [i, i + 2, i + 3]])
    p = lambda x, y, z: c + np.array([x, y, z]) * h
    # 6 caras con bisel en x (cara exterior más chica): cara exterior recortada
    s = 1 - b
    for sx in (-1, 1):
        # cara lateral (exterior/interior) más chica
        quad(p(sx, -s, -s), p(sx, -s, s), p(sx, s, s), p(sx, s, -s)) if sx > 0 else quad(p(sx, -s, -s), p(sx, s, -s), p(sx, s, s), p(sx, -s, s))
    # bandas biseladas que unen la cara exterior chica con el contorno completo a x=±(1-b)
    for sx in (-1, 1):
        xo, xi = sx, sx * (1 - b)
        quad(p(xo, -s, -s), p(xo, s, -s), p(xi, 1, -1), p(xi, -1, -1))  # z-
        quad(p(xo, s, s), p(xo, -s, s), p(xi, -1, 1), p(xi, 1, 1))      # z+
        quad(p(xo, s, -s), p(xo, s, s), p(xi, 1, 1), p(xi, 1, -1))      # y+
        quad(p(xo, -s, s), p(xo, -s, -s), p(xi, -1, -1), p(xi, -1, 1))  # y-
    # cuerpo central entre x=-(1-b) y x=+(1-b)
    xi = 1 - b
    quad(p(-xi, -1, -1), p(xi, -1, -1), p(xi, 1, -1), p(-xi, 1, -1))
    quad(p(-xi, 1, 1), p(xi, 1, 1), p(xi, -1, 1), p(-xi, -1, 1))
    quad(p(-xi, 1, -1), p(xi, 1, -1), p(xi, 1, 1), p(-xi, 1, 1))
    quad(p(-xi, -1, 1), p(xi, -1, 1), p(xi, -1, -1), p(-xi, -1, -1))
    V = np.array(V); F = np.array(F)
    # orientar caras hacia afuera
    cen = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    flip = (nrm * (cen - c)).sum(1) < 0
    F[flip] = F[flip][:, ::-1]
    # normales planas: duplicar vértices por cara
    V2 = V[F].reshape(-1, 3); F2 = np.arange(len(V2)).reshape(-1, 3)
    N = np.cross(V2[1::3] - V2[0::3], V2[2::3] - V2[0::3]); N /= np.linalg.norm(N, axis=1, keepdims=True)
    N2 = np.repeat(N, 3, axis=0)
    nodo = next(n for n in E.j["nodes"] if n.get("name") == nodo_nombre)
    malla = E.j["meshes"][nodo["mesh"]]
    mat = next(i for i, m in enumerate(E.j["materials"]) if m["name"] == material)
    jn = [E.j["nodes"][k]["name"] for k in E.j["skins"][0]["joints"]].index(hueso)
    J = np.zeros((len(V2), 4), np.uint16); J[:, 0] = jn
    W = np.zeros((len(V2), 4), np.float32); W[:, 0] = 1
    def add_raw(arr, ctype, typ, target=None):
        arr = np.ascontiguousarray(arr)
        while len(E.out) % 4:
            E.out.append(0)
        v = {"buffer": 0, "byteOffset": len(E.out), "byteLength": arr.nbytes}
        if target:
            v["target"] = target
        E.out.extend(arr.tobytes()); E.j["bufferViews"].append(v)
        a = {"bufferView": len(E.j["bufferViews"]) - 1, "componentType": ctype, "count": len(arr), "type": typ}
        E.j["accessors"].append(a); return len(E.j["accessors"]) - 1
    pos = E._add(V2, "VEC3", 34962, True)
    nor = E._add(N2, "VEC3", 34962)
    joi = add_raw(J, 5123, "VEC4", 34962)
    wei = add_raw(W, 5126, "VEC4", 34962)
    idx = add_raw(F2.astype(np.uint16).ravel(), 5123, "SCALAR", 34963)
    ntar = len(malla["primitives"][0].get("targets", []))
    cero = {"componentType": 5126, "count": len(V2), "type": "VEC3", "min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]}
    targets = []
    for _ in range(ntar):
        E.j["accessors"].append(dict(cero)); targets.append({"POSITION": len(E.j["accessors"]) - 1})
    prim = {"attributes": {"POSITION": pos, "NORMAL": nor, "JOINTS_0": joi, "WEIGHTS_0": wei}, "indices": idx, "material": mat}
    if targets:
        prim["targets"] = targets
    malla["primitives"].append(prim)
    E.b = bytes(E.out)
    E.log.append({"operacion": f"caja nueva {nodo_nombre}/{material}", "centro": c.round(4).tolist(), "semiejes": h.round(4).tolist(), "triangulos": int(len(F2))})
