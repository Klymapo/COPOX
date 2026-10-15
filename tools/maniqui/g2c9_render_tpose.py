"""Render G2-C9 GLBs in the unchanged skeleton bind/T pose."""
import bpy, math, os, sys
from mathutils import Vector
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0] if args else 'build/g2c9/captures_tpose');out.mkdir(parents=True,exist_ok=True)
requested=set(args[1:])
for ob in list(bpy.data.objects):
 bpy.data.objects.remove(ob,do_unlink=True)
models={'COLOR':'build/g2c8/COLOR_compat.glb','HUECOS':'build/g2c9/HUECOS_compat.glb','GLABELA':'build/g2c9/GLABELA_compat.glb'}
if requested:models={k:v for k,v in models.items() if k in requested}
views=[('frontal',(0,-1,0),(0,0,.49),1.12),('perfil_izquierdo',(-1,0,0),(0,0,.49),1.12),('perfil_derecho',(1,0,0),(0,0,.49),1.12),('posterior',(0,1,0),(0,0,.49),1.12),('tres_cuartos_derecho',(.707,-.707,0),(0,0,.49),1.12),('detalle_rostro',(0,-1,0),(0,-.12,.69),.43),('detalle_nariz',(0,-1,0),(0,-.20,.677),.20),('detalle_oreja',(.707,-.707,0),(.18,-.06,.69),.3)]
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.eevee.taa_render_samples=8
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=-.4;scene.view_settings.gamma=1
world=bpy.data.worlds.new('G2C9 QA neutral') if not bpy.data.worlds else bpy.data.worlds[0]
scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.78,.77,.75,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
cam_data=bpy.data.cameras.new('QA camera');cam=bpy.data.objects.new('QA camera',cam_data);scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.lens=50;cam.data.clip_start=.005;cam.data.clip_end=100

def point(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Z').to_euler()

def add_area(name,loc,power,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;point(o,target);return o
add_area('Key softbox',(-2.4,-2.8,2.8),95,2.1,(0,0,.65))
add_area('Fill softbox',(2.2,-1.0,1.8),55,1.8,(0,0,.66))
add_area('Rim softbox',(0,2.4,2.4),70,1.8,(0,0,.67))
scene.render.image_settings.file_format='PNG'
for label,path in models.items():
 # Remove prior imported characters, preserving camera and lights.
 for ob in list(scene.objects):
  if ob.type in {'MESH','ARMATURE','EMPTY','CURVE','SURFACE','FONT'}:bpy.data.objects.remove(ob,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
 # Blender auto-selects Sit-pose on import. Clear all imported actions/NLA,
 # then restore the skeleton's bind/T pose before rendering.
 for arm in [o for o in scene.objects if o.type=='ARMATURE']:
  arm.animation_data_clear()
  for pb in arm.pose.bones: pb.matrix_basis.identity()
 scene.frame_set(0)
 bpy.context.view_layer.update()
 # Capture the imported GLB at rest pose and identical camera/lighting settings.
 dest=out/label;dest.mkdir(exist_ok=True)
 for name,direction,target,scale in views:
  if name not in {'detalle_rostro','frontal','perfil_derecho'}:continue
  direction=Vector(direction).normalized();target=Vector(target)
  cam.location=target+direction*2.0;point(cam,target);cam.data.ortho_scale=scale
  scene.render.filepath=str(dest/(name+'.png'))
  bpy.ops.render.render(write_still=True)
 print('RENDERED',label,len(views),flush=True)
