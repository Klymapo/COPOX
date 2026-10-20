"""Lleva la oclusión horneada (hornear_ao.py → .npz) al COLOR_0 de un GLB NUEVO (numpy; no toca el original).

  python -m copox.cine.aplicar_ao ORIGEN.glb AO.npz DESTINO.glb [--fuerza 0.6] [--solo NODO,NODO]

COLOR_0 multiplica el color base en glTF: color = color_previo × (1 − fuerza × (1 − ao)). Se empareja por nodo y por
posición (vecino más cercano en la pose de reposo, ejes glTF). Un GLB nuevo es una versión nueva: CHXP + Admin.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from scipy.spatial import cKDTree

from copox.medicion.gltf import _q2m, accesor
from copox.medicion.rostro_edicion import Editor


def _mundo(j):
    par = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}

    def local(i):
        n = j["nodes"][i]
        if "matrix" in n:
            return np.array(n["matrix"], float).reshape(4, 4).T
        M = np.eye(4)
        M[:3, :3] = _q2m(n.get("rotation", [0, 0, 0, 1])) @ np.diag(n.get("scale", [1, 1, 1]))
        M[:3, 3] = n.get("translation", [0, 0, 0])
        return M
    out = {}
    for i in range(len(j["nodes"])):
        M, k = local(i), i
        while k in par:
            k = par[k]; M = local(k) @ M
        out[i] = M
    return out


def _color_actual(j, b, p, n):
    if "COLOR_0" not in p["attributes"]:
        return np.ones((n, 4), np.float32)
    acc = j["accessors"][p["attributes"]["COLOR_0"]]
    C = accesor(j, b, p["attributes"]["COLOR_0"]).astype(np.float32)
    if acc["componentType"] == 5121:
        C /= 255.0
    elif acc["componentType"] == 5123:
        C /= 65535.0
    if C.shape[1] == 3:
        C = np.hstack([C, np.ones((len(C), 1), np.float32)])
    return C


def aplicar(origen, npz, destino, fuerza=0.6, solo=None):
    if os.path.abspath(origen) == os.path.abspath(destino):
        raise PermissionError("aplicar_ao escribe un GLB NUEVO; no sobrescribe el origen")
    E = Editor(origen)
    datos = np.load(npz)
    W = _mundo(E.j)
    log = {}
    for i, n in enumerate(E.j["nodes"]):
        nombre = n.get("name")
        if "mesh" not in n or (solo and nombre not in solo) or f"{nombre}|pos" not in datos:
            continue
        P, ao = datos[f"{nombre}|pos"], datos[f"{nombre}|ao"]
        arbol = cKDTree(P)
        M = W[i]
        for p in E.j["meshes"][n["mesh"]]["primitives"]:
            V = accesor(E.j, E.b, p["attributes"]["POSITION"]).astype(float)
            Vw = V @ M[:3, :3].T + M[:3, 3]
            d, k = arbol.query(Vw)
            a = np.where(d < 1e-3, ao[k], 1.0)                 # sin pareja confiable → sin oscurecer
            C = _color_actual(E.j, E.b, p, len(V))
            C[:, :3] *= (1 - fuerza * (1 - np.clip(a, 0, 1)))[:, None]
            p["attributes"]["COLOR_0"] = E._add(C, "VEC4", 34962)
            E.b = bytes(E.out)
            log[nombre] = log.get(nombre, 0) + len(V)
    E.log.append({"operacion": "oclusión horneada en COLOR_0", "fuerza": fuerza, "vertices": log})
    E.guardar(destino, nota="AO horneado (copox.cine)")
    return {"destino": destino, "nodos": len(log), "vertices": int(sum(log.values()))}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="AO horneado → COLOR_0 de un GLB nuevo")
    ap.add_argument("origen"); ap.add_argument("npz"); ap.add_argument("destino")
    ap.add_argument("--fuerza", type=float, default=0.6)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    print(aplicar(a.origen, a.npz, a.destino, a.fuerza, [x for x in a.solo.split(",") if x] or None))
