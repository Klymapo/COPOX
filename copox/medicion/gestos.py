"""Morphs nuevos (gestos) y pistas de pesos en clips, sobre el Editor de rostro.

- agregar_morph(E, nombre, combinacion, campo, elegible): agrega un target a TODAS las primitivas de la
  malla con morphs (glTF exige el mismo número); delta = Σ peso·target_existente + campo(V) en las
  primitivas elegibles. Los ceros se comparten (un accesor por número de vértices).
- rellenar_pesos(E): extiende las pistas de pesos existentes con ceros para los targets nuevos.
- pista_pesos(E, clip, tiempos, pesos_por_nombre): agrega (o reemplaza) la pista de pesos de un clip.
"""
from __future__ import annotations

import numpy as np

from .gltf import accesor


def _malla(E):
    for ni, n in enumerate(E.j["nodes"]):
        if "mesh" in n and E.j["meshes"][n["mesh"]].get("extras", {}).get("targetNames"):
            return ni, E.j["meshes"][n["mesh"]]
    raise ValueError("No hay malla con targetNames")


def _vecindad(E, p, V):
    F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True); w = w.ravel()
    Fw = w[F]
    E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]])
    E2 = np.unique(np.concatenate([E2, E2[:, ::-1]]), axis=0)
    return w, E2


def suavizar_delta(E, p, V, D, iteraciones=10, mascara=None):
    """Suaviza un campo de desplazamiento sobre la malla soldada (bordes del gesto limpios, sin dientes)."""
    w, E2 = _vecindad(E, p, V)
    nw = w.max() + 1
    Dw = np.zeros((nw, 3)); np.add.at(Dw, w, D); Dw /= np.bincount(w, minlength=nw)[:, None]
    cnt = np.bincount(E2[:, 0], minlength=nw)
    activo = np.ones(nw) if mascara is None else np.bincount(w, weights=mascara(V), minlength=nw) / np.bincount(w, minlength=nw)
    for _ in range(iteraciones):
        s = np.zeros_like(Dw); np.add.at(s, E2[:, 0], Dw[E2[:, 1]])
        Dw += 0.5 * activo[:, None] * (s / np.maximum(cnt, 1)[:, None] - Dw)
    return Dw[w]


def agregar_morph(E, nombre: str, combinacion: dict, campo=None, elegible=None, suavizar=0, mascara=None):
    ni, m = _malla(E)
    nombres = m["extras"]["targetNames"]
    if nombre in nombres:
        raise ValueError(f"Ya existe el morph {nombre}")
    ceros = getattr(E, "_ceros", {})
    E._ceros = ceros
    total = 0
    for p in m["primitives"]:
        V, T = E.leer(p)
        D = np.zeros_like(V)
        for k, w in combinacion.items():
            D += w * T[nombres.index(k)]
        ok = elegible is None or elegible(p, V)
        if campo is not None and ok:
            D += campo(V)
        if suavizar and ok and len(V) > 1000 and np.abs(D).max() > 0:
            D = suavizar_delta(E, p, V, D, suavizar, mascara)
        if np.abs(D).max() > 0:
            acc = E._add(D, "VEC3", None, True)
            total += int((np.abs(D).max(1) > 1e-7).sum())
        else:
            n = len(V)
            if n not in ceros:   # ceros con datos reales (más compatible que un accesor sin bufferView)
                ceros[n] = E._add(np.zeros((n, 3), np.float32), "VEC3", None, True)
            acc = ceros[n]
        p.setdefault("targets", []).append({"POSITION": acc})
    nombres.append(nombre)
    m["weights"] = list(m.get("weights", [0.0] * (len(nombres) - 1))) + [0.0]
    E.b = bytes(E.out)
    E.log.append({"operacion": f"morph nuevo {nombre}", "combinacion": combinacion, "vertices": total})


def rellenar_pesos(E):
    ni, m = _malla(E)
    n = len(m["extras"]["targetNames"])
    hechos = 0
    for a in E.j.get("animations", []):
        for ch in a["channels"]:
            if ch["target"]["path"] != "weights" or ch["target"]["node"] != ni:
                continue
            sm = a["samplers"][ch["sampler"]]
            O = accesor(E.j, E.b, sm["output"]).astype(np.float32).reshape(-1)
            k = len(accesor(E.j, E.b, sm["input"]))
            filas = O.size // k if sm.get("interpolation") != "CUBICSPLINE" else O.size // (3 * k)
            if filas == n:
                continue
            Om = O.reshape(-1, filas)
            O2 = np.zeros((Om.shape[0], n), np.float32); O2[:, :filas] = Om
            sm["output"] = E._add(O2.reshape(-1), "SCALAR")
            hechos += 1
    E.b = bytes(E.out)
    E.log.append({"operacion": "pistas de pesos extendidas a los morphs nuevos", "pistas": hechos})


def pista_pesos(E, clip: str, tiempos, pesos: dict):
    """pesos: {nombre_morph: lista de valores por tiempo}. Reemplaza la pista de pesos del clip si existe."""
    ni, m = _malla(E)
    nombres = m["extras"]["targetNames"]
    a = next(x for x in E.j["animations"] if x.get("name") == clip)
    t = np.asarray(tiempos, np.float32)
    O = np.zeros((len(t), len(nombres)), np.float32)
    for k, vals in pesos.items():
        O[:, nombres.index(k)] = vals
    i_acc = E._add(t, "SCALAR")
    E.j["accessors"][i_acc]["min"] = [float(t.min())]; E.j["accessors"][i_acc]["max"] = [float(t.max())]
    o_acc = E._add(O.reshape(-1), "SCALAR")
    a["channels"] = [c for c in a["channels"] if not (c["target"]["path"] == "weights" and c["target"]["node"] == ni)]
    a["samplers"].append({"input": i_acc, "output": o_acc, "interpolation": "LINEAR"})
    a["channels"].append({"sampler": len(a["samplers"]) - 1, "target": {"node": ni, "path": "weights"}})
    E.b = bytes(E.out)
    E.log.append({"operacion": f"pista de pesos en {clip}", "claves": len(t), "morphs": sorted(pesos)})
