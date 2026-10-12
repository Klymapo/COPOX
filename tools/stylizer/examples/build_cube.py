"""Genera una base GLB reproducible y neutral sin servicios externos.

Cubo de demostración, sin relación con medidas definitivas de Theo Alpha.
"""
import argparse
import json
import struct
from pathlib import Path

FACES = [
    ((0, 0, 1), [(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]),
    ((0, 0,-1), [(.5,-.5,-.5),(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5)]),
    ((1, 0, 0), [(.5,-.5,.5),(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5)]),
    ((-1,0, 0), [(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5),(-.5,.5,-.5)]),
    ((0, 1, 0), [(-.5,.5,.5),(.5,.5,.5),(.5,.5,-.5),(-.5,.5,-.5)]),
    ((0,-1, 0), [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)])
]


def build_cube(destination):
    destination = Path(destination)
    positions = [n for _, face in FACES for xyz in face for n in xyz]
    normals = [n for normal, _ in FACES for _ in range(4) for n in normal]
    triangles = [i for face in range(6) for i in (
        face*4, face*4+1, face*4+2, face*4, face*4+2, face*4+3)]
    pos = struct.pack("<" + "f"*len(positions), *positions)
    norm = struct.pack("<" + "f"*len(normals), *normals)
    idx = struct.pack("<" + "H"*len(triangles), *triangles)
    geometry = pos + norm + idx
    gltf = {
        "asset": {"version": "2.0", "generator": "AlasTheo Stylizer neutral example"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "ExperimentalCube"}],
        "meshes": [{"name": "DemoCube", "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0}]}],
        "materials": [{"name": "SampleBlue", "pbrMetallicRoughness": {
            "baseColorFactor": [.3,.65,.85,1], "metallicFactor": 0,
            "roughnessFactor": .85}, "doubleSided": True}],
        "buffers": [{"byteLength": len(geometry)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos), "byteLength": len(norm), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos)+len(norm),
             "byteLength": len(idx), "target": 34963}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 24, "type": "VEC3",
             "min": [-.5,-.5,-.5], "max": [.5,.5,.5]},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 36, "type": "SCALAR"}]
    }
    data = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    data += b" " * (-len(data)%4)
    geometry += bytes((-len(geometry))%4)
    total = 12+8+len(data)+8+len(geometry)
    result = (b"glTF" + struct.pack("<II",2,total) +
              struct.pack("<I4s",len(data),b"JSON") + data +
              struct.pack("<I4s",len(geometry),b"BIN"+bytes([0])) + geometry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un GLB neutro para pruebas")
    parser.add_argument("output", nargs="?", default="example_cube.glb")
    print(build_cube(parser.parse_args().output))
