"""Compacta un GLB: quita accesores, bufferViews e imágenes que ya nadie usa.

Las ediciones (proporciones, rostro) agregan datos nuevos al final del buffer y
dejan los viejos huérfanos; el archivo crece en cada versión. Esto lo reescribe
con solo lo referenciado. No cambia geometría, skin, morphs ni clips.

Uso: python -m copox.medicion.compactar entrada.glb salida.glb
"""
from __future__ import annotations

import json
import struct
import sys

from .gltf import leer_glb


def _accesores_usados(j: dict) -> set[int]:
    u = set()
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            u.update(p["attributes"].values())
            if "indices" in p:
                u.add(p["indices"])
            for t in p.get("targets", []):
                u.update(t.values())
    for s in j.get("skins", []):
        if "inverseBindMatrices" in s:
            u.add(s["inverseBindMatrices"])
    for a in j.get("animations", []):
        for sm in a["samplers"]:
            u.add(sm["input"]); u.add(sm["output"])
    return u


def compactar(src: str, dst: str) -> dict:
    j, b = leer_glb(src)
    for a in j.get("accessors", []):
        if "sparse" in a:
            raise NotImplementedError("accesores sparse no soportados")
    # imágenes: solo las que usa alguna textura
    img_usadas = sorted({t["source"] for t in j.get("textures", []) if "source" in t})
    mapa_img = {v: i for i, v in enumerate(img_usadas)}
    imgs_antes = len(j.get("images", []))
    if "images" in j:
        j["images"] = [j["images"][i] for i in img_usadas]
        for t in j.get("textures", []):
            if "source" in t:
                t["source"] = mapa_img[t["source"]]
    acc_antes, bv_antes = len(j.get("accessors", [])), len(j.get("bufferViews", []))
    usados = sorted(_accesores_usados(j))
    mapa_a = {v: i for i, v in enumerate(usados)}
    bv_usadas = sorted({j["accessors"][i]["bufferView"] for i in usados if "bufferView" in j["accessors"][i]}
                       | {im["bufferView"] for im in j.get("images", []) if "bufferView" in im})
    mapa_bv = {v: i for i, v in enumerate(bv_usadas)}
    out = bytearray()
    nuevas = []
    for v in bv_usadas:
        bv = dict(j["bufferViews"][v])
        o = bv.get("byteOffset", 0)
        while len(out) % 4:
            out.append(0)
        bv["byteOffset"] = len(out)
        bv["buffer"] = 0
        out.extend(b[o:o + bv["byteLength"]])
        nuevas.append(bv)
    while len(out) % 4:
        out.append(0)
    accs = []
    for i in usados:
        a = dict(j["accessors"][i])
        if "bufferView" in a:
            a["bufferView"] = mapa_bv[a["bufferView"]]
        accs.append(a)
    j["accessors"], j["bufferViews"] = accs, nuevas
    for im in j.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = mapa_bv[im["bufferView"]]
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            p["attributes"] = {k: mapa_a[v] for k, v in p["attributes"].items()}
            if "indices" in p:
                p["indices"] = mapa_a[p["indices"]]
            if "targets" in p:
                p["targets"] = [{k: mapa_a[v] for k, v in t.items()} for t in p["targets"]]
    for s in j.get("skins", []):
        if "inverseBindMatrices" in s:
            s["inverseBindMatrices"] = mapa_a[s["inverseBindMatrices"]]
    for a in j.get("animations", []):
        for sm in a["samplers"]:
            sm["input"], sm["output"] = mapa_a[sm["input"]], mapa_a[sm["output"]]
    j["buffers"] = [{"byteLength": len(out)}]
    js = json.dumps(j, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * (-len(js) % 4)
    with open(dst, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(out), 0x004E4942)); f.write(out)
    return {"bytes_antes": len(b), "bytes_despues": len(out), "accesores": [acc_antes, len(accs)],
            "bufferViews": [bv_antes, len(nuevas)], "imagenes": [imgs_antes, len(j.get("images", []))]}


if __name__ == "__main__":
    print(compactar(sys.argv[1], sys.argv[2]))
