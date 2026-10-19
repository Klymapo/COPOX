"""Edición de proporciones por huesos sobre un GLB con skin (derivado; nunca toca el original).

Cada edición define, para un conjunto de huesos, una transformación afín en el
espacio de reposo. Los vértices se mueven con la mezcla de pesos de sus huesos
(v' = Σ w_j A_j(v)); los huesos se mueven a A_j(p_j); se recalculan las
traslaciones locales de los nodos, las inverseBindMatrices y las claves de
traslación animadas, así las rotaciones de los clips siguen siendo válidas.

Ediciones soportadas (lista en ``ediciones``):
  {"tipo": "mover", "huesos": "Head*", "delta": [dx, dy, dz]}
      mueve el hueso, su descendencia y sus vértices.
  {"tipo": "escala_eje", "raiz": "LeftHand", "hacia": "LeftMiddleProximal", "factor": 0.7}
      escala a lo largo del eje raíz→hacia, con pivote en la raíz; afecta la raíz y su descendencia.
  {"tipo": "escala_vertices", "huesos": "Neck", "factores": [sx, sy, sz], "pivote": [x, y, z]}
      escala solo los vértices pesados por esos huesos (no mueve huesos).
  {"tipo": "rotar", "raiz": "LeftThumbMetacarpal", "eje": [0, 1, 0], "grados": 30}
      gira el hueso, su descendencia y sus vértices (pivote = cabeza del hueso). Las claves de rotación de los
      clips se conjugan con ``conjugar_claves`` para que las poses giren igual.
  {"tipo": "escalar", "raiz": "LeftHand", "factor": 1.08}
      escala uniforme del hueso, su descendencia y sus vértices (pivote = cabeza del hueso).
  {"tipo": "acortar", "hasta": ["LeftFoot", "RightFoot"], "fijos": ["Root"], "delta": 0.0135}
      acorta las piernas manteniendo los pies en el piso: todo lo que NO es la
      descendencia de ``hasta`` (ni ``fijos``) baja ``delta``.
  {"tipo": "mover_articulacion", "hueso": "LeftLowerArm", "delta": -0.015}
      mueve SOLO esa articulación a lo largo del eje padre→hueso (p. ej. subir el codo) sin mover sus hijos: el
      segmento del padre se escala con pivote en su cabeza y el del hueso con pivote en la cabeza de su hijo
      (la muñeca queda fija). En el codo ambas transformaciones coinciden: la piel no se rompe.
Requisito: reposo sin rotaciones/escalas en los nodos del esqueleto (se verifica).
"""
from __future__ import annotations

import json
import struct

import numpy as np

from .gltf import leer_glb, accesor


def _hijos(j):
    return {i: n.get("children", []) for i, n in enumerate(j["nodes"])}


def _desc(j, raiz):
    h = _hijos(j)
    out, pila = [], [raiz]
    while pila:
        k = pila.pop(); out.append(k); pila.extend(h[k])
    return out


def _idx(j, nombre):
    return next(i for i, n in enumerate(j["nodes"]) if n.get("name") == nombre)


def editar(src: str, dst: str, ediciones: list[dict], nota: str = "") -> dict:
    j, b = leer_glb(src)
    out = bytearray(b)
    padre = {c: i for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
    skin = j["skins"][0]
    joints = skin["joints"]
    for k in joints:
        n = j["nodes"][k]
        if n.get("rotation") not in (None, [0, 0, 0, 1]) or n.get("scale") not in (None, [1, 1, 1]) or "matrix" in n:
            raise ValueError(f"Hueso con rotación/escala en reposo no soportado: {n.get('name')}")

    def mundo(i):
        p = np.zeros(3)
        while i is not None:
            p += np.array(j["nodes"][i].get("translation", [0, 0, 0]), float)
            i = padre.get(i)
        return p

    P0 = {k: mundo(k) for k in joints}
    # transformación afín por hueso, en espacio mundo de reposo: x -> L x + t
    L = {k: np.eye(3) for k in joints}
    T = {k: np.zeros(3) for k in joints}
    Lv = {k: np.eye(3) for k in joints}  # solo vértices
    Tv = {k: np.zeros(3) for k in joints}

    def componer(k, Lx, tx, solo_vertices=False):
        if not solo_vertices:
            L[k], T[k] = Lx @ L[k], Lx @ T[k] + tx
        Lv[k], Tv[k] = Lx @ Lv[k], Lx @ Tv[k] + tx

    for e in ediciones:
        if e["tipo"] == "mover":
            for raiz in e["huesos"] if isinstance(e["huesos"], list) else [e["huesos"]]:
                for k in _desc(j, _idx(j, raiz)):
                    if k in L:
                        componer(k, np.eye(3), np.array(e["delta"], float))
        elif e["tipo"] == "escala_eje":
            r, h = _idx(j, e["raiz"]), _idx(j, e["hacia"])
            piv = P0[r]
            d = P0[h] - piv; d /= np.linalg.norm(d)
            S = np.eye(3) + (e["factor"] - 1) * np.outer(d, d)
            for k in _desc(j, r):
                if k in L:
                    componer(k, S, piv - S @ piv)
        elif e["tipo"] == "rotar":
            # gira el hueso raíz, su descendencia y sus vértices en el reposo (pivote = cabeza de la raíz);
            # las rotaciones de los clips de esos huesos se conjugan aparte (rotar_claves) para que cada pose
            # quede girada igual que el reposo
            r = _idx(j, e["raiz"])
            piv = P0[r]
            ax = np.asarray(e["eje"], float); ax /= np.linalg.norm(ax)
            a = np.radians(e["grados"])
            K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            Rm = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
            for k in _desc(j, r):
                if k in L:
                    componer(k, Rm, piv - Rm @ piv)
        elif e["tipo"] == "mover_articulacion":
            k = _idx(j, e["hueso"]); pa = padre[k]
            hijos = [c for c in j["nodes"][k].get("children", []) if c in L]
            if not hijos:
                raise ValueError("mover_articulacion necesita un hijo en el esqueleto")
            ch = hijos[0]
            ps, pe, pw = P0[pa], P0[k], P0[ch]
            d = (pe - ps) / np.linalg.norm(pe - ps)
            Lu, Lf, dl = float(np.linalg.norm(pe - ps)), float(np.linalg.norm(pw - pe)), float(e["delta"])
            Su = np.eye(3) + ((Lu + dl) / Lu - 1) * np.outer(d, d)
            dw = (pw - pe) / Lf
            Sf = np.eye(3) + ((Lf - dl) / Lf - 1) * np.outer(dw, dw)
            componer(pa, Su, ps - Su @ ps)
            componer(k, Sf, pw - Sf @ pw)
        elif e["tipo"] == "escalar":
            # escala uniforme del hueso raíz, su descendencia y sus vértices (pivote = cabeza de la raíz)
            r = _idx(j, e["raiz"]); piv = P0[r]
            S = np.eye(3) * float(e["factor"])
            for k in _desc(j, r):
                if k in L:
                    componer(k, S, piv - S @ piv)
        elif e["tipo"] == "escala_vertices":
            S = np.diag(e["factores"]).astype(float)
            piv = np.array(e["pivote"], float)
            for nombre in e["huesos"] if isinstance(e["huesos"], list) else [e["huesos"]]:
                k = _idx(j, nombre)
                componer(k, S, piv - S @ piv, solo_vertices=True)
        elif e["tipo"] == "acortar":
            fijos = set()
            for h in e["hasta"] if isinstance(e["hasta"], list) else [e["hasta"]]:
                fijos |= set(_desc(j, _idx(j, h)))
            fijos |= {_idx(j, x) for x in e.get("fijos", [])}
            for k in joints:
                if k not in fijos:
                    componer(k, np.eye(3), np.array([0.0, -e["delta"], 0.0]))
        else:
            raise ValueError(e["tipo"])

    P1 = {k: L[k] @ P0[k] + T[k] for k in joints}

    def add(arr, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr, np.float32)
        while len(out) % 4:
            out.append(0)
        v = {"buffer": 0, "byteOffset": len(out), "byteLength": arr.nbytes}
        if target:
            v["target"] = target
        out.extend(arr.tobytes()); j["bufferViews"].append(v)
        n = {"SCALAR": 1, "VEC3": 3, "VEC4": 4, "MAT4": 16}[typ]
        a = {"bufferView": len(j["bufferViews"]) - 1, "componentType": 5126, "count": len(arr) if arr.ndim > 1 or n == 1 else len(arr) // n, "type": typ}
        if minmax:
            a["min"] = arr.reshape(-1, n).min(0).tolist(); a["max"] = arr.reshape(-1, n).max(0).tolist()
        j["accessors"].append(a)
        return len(j["accessors"]) - 1

    # vértices y normales de todas las primitivas con skin
    jl = list(joints)
    Lv_arr = np.array([Lv[k] for k in jl]); Tv_arr = np.array([Tv[k] for k in jl])
    hechos = {}
    resumen = {"vertices_movidos": 0, "desplazamiento_max": 0.0}
    for ni, n in enumerate(j["nodes"]):
        if "mesh" not in n or "skin" not in n:
            continue
        for p in j["meshes"][n["mesh"]]["primitives"]:
            at = p["attributes"]
            if at["POSITION"] in hechos:
                at["POSITION"], nn = hechos[at["POSITION"]]
                if nn is not None:
                    at["NORMAL"] = nn
                continue
            V = accesor(j, b, at["POSITION"]).astype(float)
            J = accesor(j, b, at["JOINTS_0"]).astype(int)
            W = accesor(j, b, at["WEIGHTS_0"]).astype(float)
            W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
            Lb = np.einsum("nk,nkij->nij", W, Lv_arr[J])
            Tb = np.einsum("nk,nki->ni", W, Tv_arr[J])
            V1 = np.einsum("nij,nj->ni", Lb, V) + Tb
            dmax = float(np.abs(V1 - V).max()) if len(V) else 0.0
            resumen["desplazamiento_max"] = max(resumen["desplazamiento_max"], dmax)
            resumen["vertices_movidos"] += int((np.abs(V1 - V).max(1) > 1e-7).sum())
            viejo = at["POSITION"]
            at["POSITION"] = add(V1, "VEC3", 34962, True)
            hechos[viejo] = (at["POSITION"], None)
            if "NORMAL" in at:
                N = accesor(j, b, at["NORMAL"]).astype(float)
                N1 = np.einsum("nji,nj->ni", np.linalg.inv(Lb), N)  # inversa transpuesta
                N1 /= np.maximum(np.linalg.norm(N1, axis=1, keepdims=True), 1e-12)
                at["NORMAL"] = add(N1, "VEC3", 34962)
                hechos[viejo] = (at["POSITION"], at["NORMAL"])
    # nodos: nuevas traslaciones locales
    dloc = {}
    for k in joints:
        pp = P1[padre[k]] if padre.get(k) in P1 else (mundo(padre[k]) if k in padre else np.zeros(3))
        t_old = np.array(j["nodes"][k].get("translation", [0, 0, 0]), float)
        t_new = P1[k] - pp
        dloc[k] = t_new - t_old
        j["nodes"][k]["translation"] = t_new.tolist()
    # inverseBindMatrices (reposo sin rotación: IBM = traslación −p)
    ibm = np.zeros((len(jl), 16), np.float32)
    for i, k in enumerate(jl):
        M = np.eye(4); M[:3, 3] = -P1[k]
        ibm[i] = M.T.reshape(-1)
    skin["inverseBindMatrices"] = add(ibm, "MAT4")
    # claves de traslación animadas: se desplazan igual que el reposo
    claves = 0
    for a in j.get("animations", []):
        for ch in a["channels"]:
            k = ch["target"]["node"]
            if ch["target"]["path"] == "translation" and k in dloc and np.abs(dloc[k]).max() > 0:
                sm = a["samplers"][ch["sampler"]]
                O = accesor(j, b, sm["output"]).astype(float) + dloc[k]
                sm["output"] = add(O, "VEC3", None, True)
                claves += 1
    resumen["canales_traslacion_ajustados"] = claves
    resumen["huesos_movidos"] = sorted(j["nodes"][k]["name"] for k in joints if np.abs(P1[k] - P0[k]).max() > 1e-9)
    j["asset"].setdefault("extras", {})["copox_proporciones"] = {"ediciones": ediciones, "nota": nota, **{k: v for k, v in resumen.items() if k != "huesos_movidos"}}
    while len(out) % 4:
        out.append(0)
    j["buffers"] = [{"byteLength": len(out)}]
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * (-len(js) % 4)
    with open(dst, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(out), 0x004E4942)); f.write(out)
    return resumen


def conjugar_claves(src: str, dst: str, giros: list[dict]) -> int:
    """Para cada giro {"raiz", "eje", "grados"}: las claves de rotación de la raíz y su descendencia pasan a
    q' = R q R⁻¹ (R en el marco de reposo, sin rotación). Así la cadena posada queda igual que antes, girada R
    alrededor de la cabeza de la raíz en el marco del padre."""
    j, b = leer_glb(src)
    out = bytearray(b)

    def qmul(a, c):
        x1, y1, z1, w1 = a.T if a.ndim > 1 else a
        x2, y2, z2, w2 = c.T if c.ndim > 1 else c
        return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                         w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)
    n = 0
    for gi in giros:
        ax = np.asarray(gi["eje"], float); ax /= np.linalg.norm(ax)
        h = np.radians(gi["grados"]) / 2
        R = np.r_[ax * np.sin(h), np.cos(h)]; Ri = np.r_[-ax * np.sin(h), np.cos(h)]
        nodos = set(_desc(j, _idx(j, gi["raiz"])))
        for a in j.get("animations", []):
            for ch in a["channels"]:
                if ch["target"]["node"] in nodos and ch["target"]["path"] == "rotation":
                    sm = a["samplers"][ch["sampler"]]
                    Q = accesor(j, b, sm["output"]).astype(float).reshape(-1, 4)
                    Q2 = qmul(qmul(np.broadcast_to(R, Q.shape), Q), np.broadcast_to(Ri, Q.shape))
                    arr = np.ascontiguousarray(Q2, np.float32)
                    while len(out) % 4:
                        out.append(0)
                    j["bufferViews"].append({"buffer": 0, "byteOffset": len(out), "byteLength": arr.nbytes})
                    out.extend(arr.tobytes())
                    j["accessors"].append({"bufferView": len(j["bufferViews"]) - 1, "componentType": 5126,
                                           "count": len(arr), "type": "VEC4"})
                    sm["output"] = len(j["accessors"]) - 1
                    n += 1
    while len(out) % 4:
        out.append(0)
    j["buffers"] = [{"byteLength": len(out)}]
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * (-len(js) % 4)
    with open(dst, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(out), 0x004E4942)); f.write(out)
    return n
