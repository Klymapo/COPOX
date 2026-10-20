"""Helpers de GLB que las recetas se prestaban entre sí (19 oct 2026).

Antes vivían como funciones privadas de recetas (`v24._add_raw`, `v39._leer`, `v41._prim_nueva`, `v49._pieza`…) y
cada receta dependía de la anterior. Aquí son una librería; las recetas conservan sus nombres viejos como alias, así
las recetas antiguas siguen dando el mismo SHA.
"""
from __future__ import annotations

import json
import os
import subprocess

import numpy as np

from copox import entorno as _entorno

GODOT = _entorno.godot()

def prims_de_pieza(E, pieza):
    return [p for m in E.j["meshes"] for p in m["primitives"] if p.get("extras", {}).get("pieza") == pieza]

def leer(E, p, attr):
    from copox.medicion.gltf import accesor
    return accesor(E.j, E.b, p["attributes"][attr])

def add_raw(E, arr, ctype, typ, target=None):
    arr = np.ascontiguousarray(arr)
    while len(E.out) % 4:
        E.out.append(0)
    v = {"buffer": 0, "byteOffset": len(E.out), "byteLength": arr.nbytes}
    if target:
        v["target"] = target
    E.out.extend(arr.tobytes()); E.j["bufferViews"].append(v)
    E.j["accessors"].append({"bufferView": len(E.j["bufferViews"]) - 1, "componentType": ctype, "count": len(arr), "type": typ})
    return len(E.j["accessors"]) - 1

def simplificar(V, T, meta, carpeta):
    """meshoptimizer vía Godot (ImporterMesh.generate_lods): se elige el LOD más cercano a `meta` triángulos.
    En ALTH_CALIDAD=borrador no se simplifica (iteración rápida; la malla sale más pesada)."""
    from copox.medicion.malla_rapida import simplificar_activo
    if not simplificar_activo():
        return V, T
    if not GODOT or not os.path.exists(GODOT):     # en calidad final NUNCA se entrega malla densa en silencio
        raise _entorno.EntornoIncompleto("simplificar(): no hay Godot (GODOT_BIN). Corre `python -m copox.entorno`.")
    np.save(os.path.join(carpeta, "V.npy"), V.astype(np.float32)); np.save(os.path.join(carpeta, "T.npy"), T.astype(np.int32))
    with open(os.path.join(carpeta, "malla.json"), "w") as f:
        json.dump({"V": V.astype(float).round(7).tolist(), "T": T.astype(int).tolist(), "meta": int(meta)}, f)
    gd = os.path.join(_entorno.RAIZ, "copox", "godot", "herramientas", "simplificar.gd")
    proy = os.path.join(_entorno.RAIZ, "copox", "godot")
    r = subprocess.run(["xvfb-run", "-a", GODOT, "--headless", "--path", proy, "--script", gd, "--",
                        os.path.join(carpeta, "malla.json"), os.path.join(carpeta, "lod.json")],
                       capture_output=True, text=True, timeout=600)
    out = os.path.join(carpeta, "lod.json")
    if not os.path.exists(out):
        raise RuntimeError("Godot no simplificó: " + r.stdout[-500:] + r.stderr[-500:])
    d = json.load(open(out))
    V2 = np.array(d["V"], float); T2 = np.array(d["T"], np.int64).reshape(-1, 3)
    usados = np.unique(T2)
    mapa = -np.ones(len(V2), np.int64); mapa[usados] = np.arange(len(usados))
    # Godot guarda los triángulos en sentido horario visto de frente; la malla de entrada iba antihorario
    T3 = mapa[T2]
    return V2[usados], T3

def lineal(hexa):
    c = np.array([int(hexa[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return [float(x) for x in np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)] + [1.0]

def material(E, nombre, hexa):
    """La tela es de dos caras: al caminar se ve el interior del short por la muesca y las perneras."""
    j = E.j
    for i, m in enumerate(j["materials"]):
        if m["name"] == nombre:
            m["pbrMetallicRoughness"]["baseColorFactor"] = lineal(hexa)
            m["doubleSided"] = True
            return i
    j["materials"].append({"name": nombre, "pbrMetallicRoughness": {"baseColorFactor": lineal(hexa),
                                                                    "metallicFactor": 0, "roughnessFactor": 0.9},
                           "doubleSided": True})
    return len(j["materials"]) - 1

def prim_nueva(E, V, T, N, J4, W4, mat, pieza):
    return {"attributes": {"POSITION": E._add(V.astype(np.float32), "VEC3", 34962, True),
                           "NORMAL": E._add(N.astype(np.float32), "VEC3", 34962),
                           "JOINTS_0": add_raw(E, np.ascontiguousarray(J4, np.uint16), 5123, "VEC4", 34962),
                           "WEIGHTS_0": add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
            "indices": add_raw(E, np.ascontiguousarray(T.ravel(), np.uint32), 5125, "SCALAR", 34963),
            "material": mat, "extras": {"pieza": pieza}}

def pesos_short(V, nombres, y_ent, y_cint, alto=0.060, centro=0.016, maximo=0.92):
    """Hips arriba; bajo la entrepierna cada lado pasa a su muslo (rampa de `alto`). Cerca del centro (|x| < centro)
    el muslo pesa menos: la muesca no cuelga entre las piernas al caminar."""
    ih, il, ir = nombres.index("Hips"), nombres.index("LeftUpperLeg"), nombres.index("RightUpperLeg")
    t = np.clip((y_ent + alto * 0.35 - V[:, 1]) / alto, 0, 1); t = t * t * (3 - 2 * t)
    c = np.clip(np.abs(V[:, 0]) / centro, 0, 1); c = c * c * (3 - 2 * c)
    w = t * maximo * (0.3 + 0.7 * c)                              # la tela sigue al muslo, sin pegarse del todo
    J4 = np.zeros((len(V), 4), np.uint16); W4 = np.zeros((len(V), 4), np.float32)
    J4[:, 0] = ih; J4[:, 1] = np.where(V[:, 0] >= 0, il, ir)
    W4[:, 0] = 1 - w; W4[:, 1] = w
    return J4, W4

def prims_por_pieza(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}

def pieza(E, n):
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion.gltf import accesor
    q = prims_por_pieza(E)[n]
    return ra.Pieza(leer(E, q, "POSITION"), leer(E, q, "NORMAL"), accesor(E.j, E.b, q["indices"]).reshape(-1, 3),
                    J=leer(E, q, "JOINTS_0"), W=leer(E, q, "WEIGHTS_0"))

def orientar(V, T, N):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    al_reves = np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0
    T = T.copy(); T[al_reves] = T[al_reves][:, ::-1]
    return T

def nodo(E, nombre, prims, junto_a="CAPA_SHORT", visible=True):
    E.j["meshes"].append({"name": nombre, "primitives": prims})
    E.j["nodes"].append({"name": nombre, "mesh": len(E.j["meshes"]) - 1, "skin": 0})
    k = len(E.j["nodes"]) - 1
    padre = next(n for n in E.j["nodes"] if any(E.j["nodes"][c].get("name") == junto_a for c in n.get("children", [])))
    padre["children"].append(k)
    if not visible:
        E.j["nodes"][k]["extensions"] = {"KHR_node_visibility": {"visible": False}}
        usados = E.j.setdefault("extensionsUsed", [])
        if "KHR_node_visibility" not in usados:
            usados.append("KHR_node_visibility")
    E.b = bytes(E.out)

def limpiar(carpeta):
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))

def normales_sdf(sdf, V, h=0.0004):
    g = np.zeros_like(V)
    for i in range(3):
        e = np.zeros(3); e[i] = h
        g[:, i] = sdf(V + e) - sdf(V - e)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)

def facetado(V, T):
    """Sombreado plano (como las facetas de la hoja de Theo): un vértice por esquina con la normal de su cara."""
    P = V[T].reshape(-1, 3)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return P, np.arange(len(P)).reshape(-1, 3), np.repeat(fn, 3, axis=0)

def skin(E):
    from copox.medicion.gltf import accesor
    j = E.j; sk = j["skins"][0]
    ibm = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    nombres = [j["nodes"][k]["name"] for k in sk["joints"]]
    H = {n: np.linalg.inv(ibm[i])[:3, 3] for i, n in enumerate(nombres)}
    return nombres, H
