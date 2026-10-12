"""Run inside Blender (or its optional bpy Python module). Static meshes only."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector


def triangles(objects):
    total = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total


def bounds(objects):
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    return (Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
            Vector(tuple(max(point[axis] for point in points) for axis in range(3))))


def remove_loose_vertices(objects):
    # glTF exports surfaces; unused vertices must not influence scale or grounding.
    for obj in objects:
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        bmesh.ops.delete(mesh, geom=[vertex for vertex in mesh.verts if not vertex.link_faces], context="VERTS")
        mesh.to_mesh(obj.data)
        mesh.free()
        obj.data.update()


def prepare(source, output, height, yaw, triangle_limit):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source), merge_vertices=True)
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects or not any(len(obj.data.polygons) for obj in objects):
        raise ValueError("El GLB no contiene una malla con caras.")
    if any(obj.type == "ARMATURE" or obj.animation_data for obj in bpy.context.scene.objects) or any(obj.data.shape_keys for obj in objects):
        raise ValueError("Este paso admite mallas estáticas. Un rig, animación o shape keys requieren preparación manual.")
    before = triangles(objects)
    remove_loose_vertices(objects)
    # Capture world transforms first so parent/child meshes stay aligned.
    world_matrices = {obj.name: obj.matrix_world.copy() for obj in objects}
    for obj in objects:
        obj.data = obj.data.copy()
        obj.data.transform(Matrix.Rotation(math.radians(yaw), 4, "Z") @ world_matrices[obj.name])
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        obj.data.update()
    bpy.context.view_layer.update()
    low, high = bounds(objects)
    if high.z - low.z <= 1e-8:
        raise ValueError("El modelo tiene altura nula.")
    scale = height / (high.z - low.z)
    center = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    transform = Matrix.Scale(scale, 4) @ Matrix.Translation(-center)
    for obj in objects:
        obj.data.transform(transform)
        obj.data.update()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.view_layer.update()
    warnings = []
    if triangle_limit and before > triangle_limit:
        ratio = triangle_limit / before
        for obj in objects:
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new("GodotSimplification", "DECIMATE")
            modifier.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        warnings.append("Se simplificó la malla: revisa silueta, UV y detalles. El límite es aproximado.")
        # Simplification can move extremities. Restore requested final dimensions.
        remove_loose_vertices(objects)
        bpy.context.view_layer.update()
        low, high = bounds(objects)
        if high.z - low.z <= 1e-8:
            raise ValueError("La reducción eliminó la altura del modelo; usa un límite mayor.")
        center = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
        correction = Matrix.Scale(height / (high.z - low.z), 4) @ Matrix.Translation(-center)
        for obj in objects:
            obj.data.transform(correction)
            obj.data.update()
    non_manifold = 0
    degenerate = 0
    for obj in objects:
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        non_manifold += sum(not edge.is_manifold for edge in mesh.edges)
        degenerate += sum(face.calc_area() < 1e-12 for face in mesh.faces)
        mesh.free()
    if non_manifold:
        warnings.append("Hay bordes abiertos o no manifold; revisa si son intencionados.")
    if degenerate:
        warnings.append("Hay caras con área casi nula.")
    without_uv = [obj.name for obj in objects if not obj.data.uv_layers]
    if without_uv:
        warnings.append("Algunas mallas no tienen UV; los materiales con color sólido pueden funcionar sin UV.")
    image_nodes = [node for obj in objects for material in obj.data.materials if material and material.use_nodes
                   for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]
    missing_images = sum(node.image is None or not node.image.size[0] for node in image_nodes)
    if missing_images:
        warnings.append("Hay materiales con imágenes ausentes; revisa sus texturas.")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(output / "model_godot.glb"), export_format="GLB",
                              use_selection=True, export_yup=True, export_materials="EXPORT",
                              export_animations=False, export_cameras=False, export_lights=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "model_prepared.blend"), check_existing=False)
    low, high = bounds(objects)
    report = {
        "blender_version": bpy.app.version_string, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "height_meters": height, "yaw_degrees": yaw, "triangles_before": before, "triangles_after": triangles(objects),
        "triangle_limit_requested": triangle_limit, "mesh_count": len(objects),
        "material_count": len({material.name for obj in objects for material in obj.data.materials if material}),
        "texture_nodes": len(image_nodes), "missing_images": missing_images,
        "meshes_without_uv": without_uv, "non_manifold_edges": non_manifold, "degenerate_faces": degenerate,
        "blender_bounds_meters": {"min": list(low), "max": list(high)},
        "export_up_axis": "Y", "warnings": warnings,
        "manual_checks": ["Frente y escala en Godot", "Silueta y parecido", "Materiales y UV", "Rig y animaciones si se necesitan"],
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--height", type=float, default=1.8)
    parser.add_argument("--yaw", type=float, default=0)
    parser.add_argument("--triangle-limit", type=int, default=0)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    prepare(args.input, args.output, args.height, args.yaw, args.triangle_limit)
