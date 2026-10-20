"""Render de cine ALTH dentro de Blender (Cycles CPU). Correr con:  alth-python -m copox.cine.render_blender ...

  alth-python -m copox.cine.render_blender ESCENA.json --salida DIR [--desde N --hasta M] [--modelos RUTA]

Hace, sin operadores de interfaz (sólo import/render, que funcionan en --background):
  1. escena de fábrica vacía → importa el GLB (importador glTF oficial).
  2. oculta los nodos con KHR_node_visibility visible=false (el importador lo ignora) y los de `visible` de la escena.
  3. asigna el clip al esqueleto (y a las shape keys si el GLB trae su pista facial con el mismo nombre).
  4. cámara por cuadros clave (escena.camara_en), luz «estudio_alth», piso y fondo.
  5. Cycles CPU con eliminación de ruido → PNG por cuadro en DIR/cuadros/0001.png …
Ejes: la escena usa los del GLB (Y arriba, frente +Z); Blender importa con Z arriba (x, y, z)glTF → (x, −z, y).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from copox.cine import escena as esc  # noqa: E402


def _json_glb(ruta):
    with open(ruta, "rb") as f:
        cab = f.read(20)
        n = struct.unpack_from("<I", cab, 12)[0]
        return json.loads(f.read(n))


def _ocultos(ruta, extra):
    j = _json_glb(ruta)
    o = {n.get("name") for n in j.get("nodes", []) if n.get("extensions", {}).get("KHR_node_visibility", {}).get("visible") is False}
    o |= {k for k, v in (extra or {}).items() if not v}
    o -= {k for k, v in (extra or {}).items() if v}
    return o


def _gl2bl(p):
    x, y, z = p
    return (x, -z, y)


def _hex(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)   # sRGB → lineal


def preparar(e, glb):
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    sc = bpy.context.scene
    ocultos = _ocultos(glb, e.get("visible"))

    def oculto(o):
        while o is not None:
            if o.name.split(".")[0] in ocultos:
                return True
            o = o.parent
        return False
    mallas = []
    for o in sc.objects:
        if oculto(o):
            o.hide_render = True; o.hide_viewport = True
        elif o.type == "MESH":
            mallas.append(o)
    # clip
    if e.get("clip"):
        clip = e["clip"]
        acts = {a.name: a for a in bpy.data.actions}
        for o in sc.objects:
            if o.type == "ARMATURE":
                a = acts.get(clip) or next((x for n, x in acts.items() if n.startswith(clip)), None)
                if a is None:
                    raise SystemExit(f"cine: el GLB no trae el clip {clip!r}; hay {sorted(acts)[:12]}…")
                o.animation_data_create(); o.animation_data.action = a
                try:                                                   # Blender 4.4+: acciones con ranuras
                    if getattr(a, "slots", None) and o.animation_data.action_slot is None:
                        o.animation_data.action_slot = a.slots[0]
                except AttributeError:
                    pass
        for o in mallas:
            k = o.data.shape_keys
            if k is not None:
                a = next((x for n, x in acts.items() if n.startswith(clip) and o.data.name in n), None)
                if a is not None:
                    k.animation_data_create(); k.animation_data.action = a
    # alto del personaje (para cámara relativa y piso)
    sc.frame_set(e["cuadros"][0])
    dg = bpy.context.evaluated_depsgraph_get()
    zs, xs, ys = [], [], []
    for o in mallas:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
    caja = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)) if zs else (-0.5, -0.5, 0, 0.5, 0.5, 1)
    alto = max(caja[5] - caja[2], 1e-6)
    # render
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = int(e["muestras"])
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = e["resolucion"]
    sc.render.resolution_percentage = 100
    sc.render.fps = int(e["fps"])
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "Standard"                # colores de paleta tal cual (sin AgX)
    except TypeError:
        pass
    # mundo / fondo
    w = bpy.data.worlds.new("ALTH_FONDO"); sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*_hex(e["fondo"]), 1.0)
    bg.inputs[1].default_value = 0.6
    # piso
    if e.get("piso"):
        me = bpy.data.meshes.new("ALTH_PISO")
        s = alto * 20
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        pis = bpy.data.objects.new("ALTH_PISO", me); sc.collection.objects.link(pis)
        m = bpy.data.materials.new("ALTH_PISO"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*_hex(e["fondo"]), 1.0)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        me.materials.append(m)
    # luz estudio ALTH: key cálida 45° arriba-izq, fill fría derecha, rim atrás
    cx, cy = (caja[0] + caja[3]) / 2, (caja[1] + caja[4]) / 2
    def luz(nombre, pos, energia, color, tam):
        d = bpy.data.lights.new(nombre, "AREA"); d.energy = energia * alto * alto; d.color = color; d.size = tam * alto
        o = bpy.data.objects.new(nombre, d); sc.collection.objects.link(o)
        o.location = (cx + pos[0] * alto, cy + pos[1] * alto, pos[2] * alto)
        dirv = Vector((cx, cy, alto * 0.5)) - o.location
        o.rotation_euler = dirv.to_track_quat("-Z", "Y").to_euler()
    luz("ALTH_KEY", (-1.6, -1.8, 2.2), 900, (1.0, 0.96, 0.9), 1.5)
    luz("ALTH_FILL", (1.9, -1.2, 1.2), 300, (0.9, 0.95, 1.0), 2.0)
    luz("ALTH_RIM", (0.6, 2.0, 1.8), 500, (1.0, 1.0, 1.0), 1.0)
    # cámara
    cd = bpy.data.cameras.new("ALTH_CAM")
    cam = bpy.data.objects.new("ALTH_CAM", cd); sc.collection.objects.link(cam); sc.camera = cam
    if e.get("dof"):
        cd.dof.use_dof = True; cd.dof.aperture_fstop = float(e["dof"])
    return {"cam": cam, "alto": alto, "centro": (cx, cy, caja[2]), "mallas": len(mallas), "ocultos": sorted(ocultos)}


def poner_camara(e, ctx, f):
    from mathutils import Vector
    pos, mira, lente = esc.camara_en(e, f)
    if e.get("camara_relativa"):
        a = ctx["alto"]; cx, cy, z0 = ctx["centro"]
        P = Vector(_gl2bl(pos)) * a + Vector((cx, cy, z0)); M = Vector(_gl2bl(mira)) * a + Vector((cx, cy, z0))
    else:
        P, M = Vector(_gl2bl(pos)), Vector(_gl2bl(mira))
    cam = ctx["cam"]
    cam.location = P
    cam.rotation_euler = (M - P).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = float(lente)
    if cam.data.dof.use_dof:
        cam.data.dof.focus_distance = (M - P).length


def main(argv=None):
    import bpy
    argv = argv if argv is not None else (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    ap = argparse.ArgumentParser(description="Render de cine ALTH (Blender Cycles CPU)")
    ap.add_argument("escena")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--desde", type=int)
    ap.add_argument("--hasta", type=int)
    ap.add_argument("--modelos", help="checkout de copox-modelos (para glb 'modelos:…')")
    a = ap.parse_args(argv)
    e = esc.cargar(a.escena)
    glb = esc.resolver_glb(e, RAIZ, a.modelos)
    ctx = preparar(e, glb)
    d = os.path.join(a.salida, "cuadros"); os.makedirs(d, exist_ok=True)
    f0, f1 = a.desde or e["cuadros"][0], a.hasta or e["cuadros"][1]
    sc = bpy.context.scene
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        poner_camara(e, ctx, f)
        sc.render.filepath = os.path.join(d, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"cine: cuadro {f} listo", flush=True)
    json.dump({"escena": e["nombre"], "cuadros": [f0, f1], "mallas": ctx["mallas"], "ocultos": ctx["ocultos"],
               "alto_blender": ctx["alto"]}, open(os.path.join(a.salida, f"parte_{f0:04d}.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
