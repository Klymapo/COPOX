"""Lector GLB y evaluador de poses sin dependencias externas (solo NumPy).

Permite colocar un personaje en cualquier clip/tiempo (skin + morphs) para
renderizarlo imitando la pose de una referencia. Soporta interpolación LINEAR
y STEP; CUBICSPLINE se rechaza de forma explícita.
"""
from __future__ import annotations

import io
import json
import struct
from dataclasses import dataclass, field

import numpy as np

_CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def leer_glb(path: str) -> tuple[dict, bytes]:
    with open(path, "rb") as fh:
        data = fh.read()
    magic, _version, _total = struct.unpack("<III", data[:12])
    if magic != 0x46546C67:
        raise ValueError(f"No es GLB: {path}")
    jlen = struct.unpack("<I", data[12:16])[0]
    j = json.loads(data[20:20 + jlen])
    off = 20 + jlen
    binc = b""
    if off < len(data):
        blen = struct.unpack("<I", data[off:off + 4])[0]
        binc = data[off + 8:off + 8 + blen]
    return j, binc


def accesor(j: dict, binc: bytes, idx: int) -> np.ndarray:
    a = j["accessors"][idx]
    n = _NC[a["type"]]
    dt = _CT[a["componentType"]]
    if "bufferView" not in a:  # glTF: accesor sin datos = ceros
        return np.zeros((a["count"], n), dt)
    bv = j["bufferViews"][a["bufferView"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    isz = np.dtype(dt).itemsize * n
    st = bv.get("byteStride", isz)
    if st == isz:
        arr = np.frombuffer(binc, dt, a["count"] * n, off).reshape(a["count"], n)
    else:
        raw = np.frombuffer(binc, np.uint8, st * (a["count"] - 1) + isz, off)
        arr = np.lib.stride_tricks.as_strided(raw, (a["count"], isz), (st, 1)).copy().view(dt).reshape(a["count"], n)
    if a.get("normalized"):
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


def _q2m(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + t * (b - a)
        return r / np.linalg.norm(r)
    th = np.arccos(d)
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


@dataclass
class Primitiva:
    nodo: int
    material: dict
    indices: np.ndarray
    pos: np.ndarray
    joints: np.ndarray | None
    weights: np.ndarray | None
    morphs: list = field(default_factory=list)
    uv: np.ndarray | None = None
    textura: np.ndarray | None = None  # RGBA float 0-1
    color: np.ndarray | None = None    # COLOR_0 (lineal, RGB 0-1) si existe
    normal: np.ndarray | None = None   # NORMAL guardada en el archivo


class Modelo:
    """Escena glTF: nodos, skin, morphs y clips."""

    def __init__(self, path: str):
        self.path = path
        self.j, self.b = leer_glb(path)
        j = self.j
        self.padre = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
        self.clips = {a.get("name", f"clip_{i}"): a for i, a in enumerate(j.get("animations", []))}
        self._img = {}
        self.prims: list[Primitiva] = []
        for ni, n in enumerate(j["nodes"]):
            if "mesh" not in n:
                continue
            for p in j["meshes"][n["mesh"]]["primitives"]:
                if "indices" not in p:
                    continue
                at = p["attributes"]
                idx = accesor(j, self.b, p["indices"]).reshape(-1, 3).astype(np.int64)
                if len(idx) == 0:
                    continue
                mat = j["materials"][p["material"]] if "material" in p else {}
                tex = uv = None
                pb = mat.get("pbrMetallicRoughness", {})
                if "baseColorTexture" in pb and "TEXCOORD_0" in at:
                    uv = accesor(j, self.b, at["TEXCOORD_0"]).astype(float)
                    tex = self._imagen(j["textures"][pb["baseColorTexture"]["index"]]["source"])
                self.prims.append(Primitiva(
                    nodo=ni, material=mat, indices=idx,
                    pos=accesor(j, self.b, at["POSITION"]).astype(float),
                    joints=accesor(j, self.b, at["JOINTS_0"]).astype(np.int64) if "JOINTS_0" in at else None,
                    weights=accesor(j, self.b, at["WEIGHTS_0"]).astype(float) if "WEIGHTS_0" in at else None,
                    morphs=[accesor(j, self.b, t["POSITION"]).astype(float) for t in p.get("targets", []) if "POSITION" in t],
                    uv=uv, textura=tex,
                    color=accesor(j, self.b, at["COLOR_0"])[:, :3].astype(float) if "COLOR_0" in at else None,
                    normal=accesor(j, self.b, at["NORMAL"]).astype(float) if "NORMAL" in at else None))

    def _imagen(self, i: int) -> np.ndarray:
        if i not in self._img:
            from PIL import Image
            im = self.j["images"][i]
            bv = self.j["bufferViews"][im["bufferView"]]
            o = bv.get("byteOffset", 0)
            self._img[i] = np.asarray(Image.open(io.BytesIO(self.b[o:o + bv["byteLength"]])).convert("RGBA")).astype(float) / 255
        return self._img[i]

    # --- animación ---------------------------------------------------------
    def duracion(self, clip: str) -> float:
        a = self.clips[clip]
        return max(float(accesor(self.j, self.b, a["samplers"][c["sampler"]]["input"]).max()) for c in a["channels"])

    def muestrear(self, clip: str | None, t: float):
        trs, pesos = {}, {}
        if clip is None:
            return trs, pesos
        a = self.clips[clip]
        for ch in a["channels"]:
            sm = a["samplers"][ch["sampler"]]
            interp = sm.get("interpolation", "LINEAR")
            if interp == "CUBICSPLINE":
                raise NotImplementedError("CUBICSPLINE no soportado")
            I = accesor(self.j, self.b, sm["input"])[:, 0].astype(float)
            O = accesor(self.j, self.b, sm["output"]).astype(float)
            n = len(I)
            path, node = ch["target"]["path"], ch["target"]["node"]
            if path == "weights":
                O = O.reshape(n, -1)
            tt = float(np.clip(t, I[0], I[-1]))
            k = int(np.clip(np.searchsorted(I, tt, side="right") - 1, 0, max(n - 2, 0)))
            if n == 1:
                v = O[0]
            else:
                u = 0.0 if I[k + 1] == I[k] else (tt - I[k]) / (I[k + 1] - I[k])
                if interp == "STEP":
                    v = O[k]
                elif path == "rotation":
                    v = _slerp(O[k], O[k + 1], u)
                else:
                    v = O[k] * (1 - u) + O[k + 1] * u
            if path == "weights":
                pesos[node] = v
            else:
                trs.setdefault(node, {})[path] = v
        return trs, pesos

    def _mundo(self, trs):
        W = {}

        def local(i):
            n = self.j["nodes"][i]
            o = trs.get(i, {})
            M = np.eye(4)
            if "matrix" in n and not o:
                return np.array(n["matrix"], float).reshape(4, 4).T
            M[:3, :3] = _q2m(o.get("rotation", n.get("rotation", [0, 0, 0, 1]))) * np.array(o.get("scale", n.get("scale", [1, 1, 1])))
            M[:3, 3] = o.get("translation", n.get("translation", [0, 0, 0]))
            return M

        def g(i):
            if i not in W:
                W[i] = (g(self.padre[i]) if i in self.padre else np.eye(4)) @ local(i)
            return W[i]
        return g

    def posar(self, clip: str | None = None, frac: float = 0.0, normales: bool = False):
        """Posiciones en mundo de cada primitiva (skin + morphs) en clip/fracción.
        Con normales=True devuelve (posiciones, normales del archivo transformadas)."""
        t = self.duracion(clip) * frac if clip else 0.0
        trs, pesos = self.muestrear(clip, t)
        g = self._mundo(trs)
        cache = {}
        out, outn = [], []
        for p in self.prims:
            n = self.j["nodes"][p.nodo]
            P = p.pos.copy()
            w = pesos.get(p.nodo)
            if w is None:
                w = self.j["meshes"][n["mesh"]].get("weights")
            if w is not None:
                for wi, D in zip(w, p.morphs):
                    if wi:
                        P += wi * D
            if "skin" in n and p.joints is not None:
                si = n["skin"]
                if si not in cache:
                    sk = self.j["skins"][si]
                    ibm = accesor(self.j, self.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
                    cache[si] = np.array([g(jn) @ ibm[k] for k, jn in enumerate(sk["joints"])])
                JM = cache[si]
                M = (JM[p.joints] * p.weights[:, :, None, None]).sum(1)
                P = np.einsum("nij,nj->ni", M[:, :3, :3], P) + M[:, :3, 3]
                if normales and p.normal is not None:
                    Nn = np.einsum("nij,nj->ni", M[:, :3, :3], p.normal)
            else:
                M = g(p.nodo)
                P = P @ M[:3, :3].T + M[:3, 3]
                if normales and p.normal is not None:
                    Nn = p.normal @ M[:3, :3].T
            out.append(P)
            if normales:
                if p.normal is None:
                    outn.append(np.zeros_like(P))
                else:
                    outn.append(Nn / np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12))
        return (out, outn) if normales else out

    def color_triangulos(self, p: Primitiva) -> tuple[np.ndarray, np.ndarray]:
        """RGB (0-1, sRGB) y máscara de visibilidad por triángulo (alfa MASK)."""
        pb = p.material.get("pbrMetallicRoughness", {})
        n = len(p.indices)
        if p.textura is not None:
            uv = p.uv[p.indices].mean(1)
            h, w = p.textura.shape[:2]
            px = p.textura[np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int)]
            vis = px[:, 3] >= p.material.get("alphaCutoff", 0.5) if p.material.get("alphaMode") == "MASK" else np.ones(n, bool)
            return px[:, :3], vis
        c = np.array(pb.get("baseColorFactor", [1, 1, 1, 1])[:3], float)
        c = np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, 1) ** (1 / 2.4) - 0.055)
        return np.tile(c, (n, 1)), np.ones(n, bool)
