"""Hornea oclusión ambiental POR VÉRTICE dentro de Blender (Cycles CPU, sin interfaz) → .npz.

  alth-python -m copox.cine.hornear_ao MODELO.glb SALIDA.npz [--muestras 64] [--distancia 0.05]

Por qué así: el GLB de COPOX lleva extras propios (resortes, KHR_node_visibility, piezas) que un export de Blender
perdería. Blender sólo CALCULA; aplicar_ao.py (numpy) lleva el resultado al COLOR_0 de un GLB NUEVO.
Salida: por nodo glTF → posiciones (ejes glTF, pose de reposo) y ao ∈ [0, 1] (1 = sin oclusión).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def hornear(glb, salida, muestras=64, distancia=0.05, ocultos_extra=None):
    import bpy
    from copox.cine.render_blender import _ocultos
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(muestras)
    ocultos = _ocultos(glb, ocultos_extra or {})
    for o in sc.objects:                                   # pose de reposo: sin acciones
        if o.animation_data:
            o.animation_data.action = None
        if o.name.split(".")[0] in ocultos or (o.parent and o.parent.name.split(".")[0] in ocultos):
            o.hide_render = True
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = float(distancia)
    datos = {}
    from copox.cine.render_blender import _json_glb
    jg = _json_glb(glb)
    nombres = {n.get("name") for n in jg.get("nodes", []) if "mesh" in n} | {m.get("name") for m in jg.get("meshes", [])}
    mallas = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and len(o.data.polygons)
              and not any(c.name.startswith("glTF_not_exported") for c in o.users_collection)
              and (o.name.split(".")[0] in nombres or o.data.name.split(".")[0] in nombres)]
    for o in mallas:
        me = o.data
        if not me.materials:
            me.materials.append(bpy.data.materials.new("AO_TMP"))
        attr = me.color_attributes.get("ALTH_AO") or me.color_attributes.new("ALTH_AO", "FLOAT_COLOR", "POINT")
        me.color_attributes.active_color = attr
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True); bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
        except RuntimeError as err:                         # una pieza rara no tumba el horneado del resto
            print(f"ao: {o.name} sin hornear ({err})", flush=True)
            continue
        ao = np.array([attr.data[i].color[0] for i in range(len(me.vertices))], np.float32)
        P = np.array([o.matrix_world @ v.co for v in me.vertices], np.float32)
        P = np.stack([P[:, 0], P[:, 2], -P[:, 1]], 1)       # Blender (Z arriba) → glTF (Y arriba)
        datos[o.name.split(".")[0] + "|pos"] = P
        datos[o.name.split(".")[0] + "|ao"] = ao
        print(f"ao: {o.name} {len(ao)} vértices, media {ao.mean():.3f}", flush=True)
    np.savez_compressed(salida, **datos)
    return {"mallas": len(mallas), "salida": salida}


def main(argv=None):
    argv = argv if argv is not None else (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    ap = argparse.ArgumentParser(description="Horneado de oclusión ambiental por vértice (Blender Cycles CPU)")
    ap.add_argument("glb"); ap.add_argument("salida")
    ap.add_argument("--muestras", type=int, default=64)
    ap.add_argument("--distancia", type=float, default=0.05)
    a = ap.parse_args(argv)
    print(hornear(a.glb, a.salida, a.muestras, a.distancia))


if __name__ == "__main__":
    main()
