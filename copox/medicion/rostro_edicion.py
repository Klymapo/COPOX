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
