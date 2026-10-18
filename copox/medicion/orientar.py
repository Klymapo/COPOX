"""Corrige piezas con las caras invertidas (normales hacia adentro).

Por primitiva (sin materiales doubleSided ni los excluidos) calcula el volumen
con signo respecto a su centro: si es negativo, la pieza está volteada; se
invierte el orden de cada triángulo y se niegan sus normales (y las normales
de los morphs, si las hay). Escribe un derivado compactado.

Uso: python -m copox.medicion.orientar entrada.glb salida.glb
"""
from __future__ import annotations

import json
import os
import struct
import sys
import tempfile

import numpy as np

from .compactar import compactar
from .gltf import leer_glb, accesor

EXCLUIR = ("BOCA_INTERIOR_NEGRO",)  # la cavidad de la boca mira hacia adentro a propósito


def diagnostico(j, b, excluir=EXCLUIR):
    out = []
    for ni, n in enumerate(j["nodes"]):
        if "mesh" not in n:
            continue
        for pi, p in enumerate(j["meshes"][n["mesh"]]["primitives"]):
            if "indices" not in p:
                continue
            mat = j["materials"][p["material"]] if "material" in p else {}
            F = accesor(j, b, p["indices"]).reshape(-1, 3).astype(np.int64)
            if len(F) == 0:
                continue
            P = accesor(j, b, p["attributes"]["POSITION"]).astype(float)
            Q = P - P[np.unique(F)].mean(0)
            vol = float(np.einsum("ij,ij->i", Q[F[:, 0]], np.cross(Q[F[:, 1]], Q[F[:, 2]])).sum() / 6)
            out.append({"mesh": n["mesh"], "prim": pi, "material": mat.get("name", ""), "triangulos": len(F),
                        "volumen": vol, "invertida": vol < 0 and not mat.get("doubleSided") and mat.get("name", "") not in excluir})
    return out


def orientar(src: str, dst: str, excluir=EXCLUIR) -> dict:
    j, b = leer_glb(src)
    out = bytearray(b)

    def add(arr, comp, typ, target):
        arr = np.ascontiguousarray(arr)
        while len(out) % 4:
            out.append(0)
        j["bufferViews"].append({"buffer": 0, "byteOffset": len(out), "byteLength": arr.nbytes, "target": target})
        out.extend(arr.tobytes())
        a = {"bufferView": len(j["bufferViews"]) - 1, "componentType": comp, "count": int(arr.size // {"SCALAR": 1, "VEC3": 3}[typ]), "type": typ}
        if typ == "VEC3":
            a["min"] = arr.reshape(-1, 3).min(0).tolist(); a["max"] = arr.reshape(-1, 3).max(0).tolist()
        j["accessors"].append(a)
        return len(j["accessors"]) - 1

    diag = diagnostico(j, b, excluir)
    hechos = {}
    for d in diag:
        if not d["invertida"]:
            continue
        p = j["meshes"][d["mesh"]]["primitives"][d["prim"]]
        F = accesor(j, b, p["indices"]).reshape(-1, 3)
        F2 = F[:, [0, 2, 1]].astype(np.uint32).reshape(-1)
        p["indices"] = add(F2, 5125, "SCALAR", 34963)
        for at in [p["attributes"]] + p.get("targets", []):
            if "NORMAL" in at:
                k = at["NORMAL"]
                if k not in hechos:
                    hechos[k] = add(-accesor(j, b, k).astype(np.float32), 5126, "VEC3", 34962)
                at["NORMAL"] = hechos[k]
    while len(out) % 4:
        out.append(0)
    j["buffers"] = [{"byteLength": len(out)}]
    j["asset"].setdefault("extras", {})["copox_orientar"] = [f"{d['mesh']}/{d['prim']}" for d in diag if d["invertida"]]
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * (-len(js) % 4)
    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A)); fh.write(js)
        fh.write(struct.pack("<II", len(out), 0x004E4942)); fh.write(out)
        tmp = fh.name
    compactar(tmp, dst)
    os.unlink(tmp)
    return {"volteadas": [d for d in diag if d["invertida"]], "revisadas": len(diag)}


if __name__ == "__main__":
    r = orientar(sys.argv[1], sys.argv[2])
    print(len(r["volteadas"]), "de", r["revisadas"], "primitivas volteadas")
