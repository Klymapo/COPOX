"""Escribir clips en un GLB (huesos y morphs) — utilidades comunes de las herramientas de animación (20 oct 2026).

  agregar_clip(E, nombre, t, pistas)                pistas {(indice_nodo, "rotation"|"translation"): valores}
  agregar_clip_morphs(E, nombre, t, pesos, nodo)    pesos [n_cuadros, n_targets] sobre el nodo de malla (ADAN_CUERPO)
El GLB resultante es una VERSIÓN NUEVA (nombre nuevo): pasa por CHXP y por Admin antes de congelarse.
"""
from __future__ import annotations

import numpy as np


def _tiempos(E, t):
    t = np.asarray(t, np.float32)
    it = E._add(t, "SCALAR")
    E.j["accessors"][it]["min"] = [float(t.min())]
    E.j["accessors"][it]["max"] = [float(t.max())]
    return it


def _poner(E, anim):
    E.j["animations"] = [a for a in E.j.get("animations", []) if a.get("name") != anim["name"]] + [anim]
    E.b = bytes(E.out)


def agregar_clip(E, nombre, t, pistas, interpolacion="LINEAR"):
    it = _tiempos(E, t)
    anim = {"name": nombre, "samplers": [], "channels": []}
    for (nodo, path), vals in pistas.items():
        v = np.asarray(vals, np.float32)
        ot = E._add(v, "VEC4" if path == "rotation" else "VEC3")
        anim["samplers"].append({"input": it, "output": ot, "interpolation": interpolacion})
        anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": int(nodo), "path": path}})
    _poner(E, anim)
    return anim


def nodo_por_nombre(E, nombre):
    for i, n in enumerate(E.j["nodes"]):
        if n.get("name") == nombre:
            return i
    raise KeyError(f"no hay nodo {nombre!r}")


def nombres_morphs(E, malla="ADAN_CUERPO"):
    m = next(m for m in E.j["meshes"] if m.get("name") == malla)
    return list(m.get("extras", {}).get("targetNames", []))


def agregar_clip_morphs(E, nombre, t, pesos, nodo="ADAN_CUERPO", extra=None):
    """pesos: [n_cuadros, n_targets] en el orden de targetNames. `extra`: pistas de huesos opcionales (mirada…)."""
    n_t = len(nombres_morphs(E, nodo))
    P = np.asarray(pesos, np.float32)
    if P.shape[1] != n_t:
        raise ValueError(f"pesos con {P.shape[1]} columnas; la malla tiene {n_t} morphs")
    it = _tiempos(E, t)
    anim = {"name": nombre, "samplers": [], "channels": []}
    ot = E._add(P.reshape(-1, 1), "SCALAR")
    anim["samplers"].append({"input": it, "output": ot, "interpolation": "LINEAR"})
    anim["channels"].append({"sampler": 0, "target": {"node": nodo_por_nombre(E, nodo), "path": "weights"}})
    for (n, path), vals in (extra or {}).items():
        o = E._add(np.asarray(vals, np.float32), "VEC4" if path == "rotation" else "VEC3")
        anim["samplers"].append({"input": it, "output": o, "interpolation": "LINEAR"})
        anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": int(n), "path": path}})
    _poner(E, anim)
    return anim
