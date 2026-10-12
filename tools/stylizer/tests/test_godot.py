import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from prepare_godot import prepare_asset


@unittest.skipUnless(os.environ.get("BLENDER_TEST_PYTHON"), "Prueba de Blender opcional: configura BLENDER_TEST_PYTHON con un Python que tenga bpy 4.5.")
class BlenderTests(unittest.TestCase):
    def test_real_blender_export_preserves_source_and_material(self):
        executable = os.environ["BLENDER_TEST_PYTHON"]
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.glb"
            script = """import bpy,sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(3,2,4))
obj=bpy.context.object
obj.scale=(1,0.75,2)
mat=bpy.data.materials.new('Red')
mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.8,0.03,0.02,1)
texture=bpy.data.images.new('TestTexture',width=8,height=8)
texture.generated_color=(0.8,0.03,0.02,1)
texture.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image=texture
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
obj.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=sys.argv[1],export_format='GLB')
"""
            subprocess.run([executable, "-c", script, str(source)], check=True, capture_output=True, timeout=90)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with patch("prepare_godot.blender_command", return_value=[executable]):
                result = prepare_asset(source, height=1.8, yaw=90, triangle_limit=500)
            self.assertEqual(digest, hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(result["report"]["material_count"], 1)
            self.assertGreater(result["report"]["texture_nodes"], 0)
            self.assertEqual(result["report"]["missing_images"], 0)
            self.assertLess(result["report"]["triangles_after"], result["report"]["triangles_before"])
            self.assertTrue(Path(result["model"]).is_file())
            with ZipFile(result["archive"]) as bundle:
                self.assertIn("model_prepared.blend", bundle.namelist())
                self.assertIn("GODOT_IMPORT.md", bundle.namelist())
            # Reimport the actual GLB and inspect exported transforms/height.
            check = """import bpy,sys,json
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[1])
points=[o.matrix_world@Vector(p) for o in bpy.context.scene.objects if o.type=='MESH' for p in o.bound_box]
images=[n.image for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
print('CHECK:'+json.dumps({'height':max(p.z for p in points)-min(p.z for p in points),'ground':min(p.z for p in points),'textures':[list(i.size) for i in images]}))
"""
            response = subprocess.run([executable, "-c", check, result["model"]], check=True, capture_output=True, text=True, timeout=90)
            data = json.loads(next(line[6:] for line in response.stdout.splitlines() if line.startswith("CHECK:")))
            self.assertAlmostEqual(data["height"], 1.8, delta=0.05)
            self.assertAlmostEqual(data["ground"], 0, delta=0.02)
            self.assertIn([8, 8], data["textures"])
