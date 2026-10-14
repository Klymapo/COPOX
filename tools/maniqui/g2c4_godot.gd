extends SceneTree
## Captura real de geometría exportada. No altera materiales del modelo.
var camera: Camera3D
var skeleton: Skeleton3D
var player: AnimationPlayer
var meshes: Array = []
var results: Dictionary = {}
var current_model: Node
var views = [
 ["frontal",0.0,0.0,Vector3(0,.74,0),.58],
 ["perfil_izquierdo",90.0,0.0,Vector3(0,.74,0),.58],
 ["perfil_derecho",270.0,0.0,Vector3(0,.74,0),.58],
 ["posterior",180.0,0.0,Vector3(0,.74,0),.58],
 ["tres_cuartos_izquierdo",45.0,0.0,Vector3(0,.74,0),.58],
 ["tres_cuartos_derecho",315.0,0.0,Vector3(0,.74,0),.58],
 ["posterior_derecho",225.0,0.0,Vector3(0,.74,0),.58],
 ["inferior_mandibula",0.0,-75.0,Vector3(0,.555,0),.56],
 ["detalle_oreja_derecha",250.0,0.0,Vector3(.185,.665,-.06),.28],
 ["detalle_ojos",0.0,0.0,Vector3(0,.693,.19),.37],
 ["detalle_ojo_izquierdo",25.0,0.0,Vector3(-.085,.688,.19),.19],
 ["detalle_ojo_derecho",335.0,0.0,Vector3(.085,.688,.19),.19],
 ["detalle_union_cuello",315.0,-40.0,Vector3(0,.54,.025),.43]]
func _initialize():
    call_deferred("run")
func scan(n: Node):
    if n is Skeleton3D: skeleton=n
    if n is AnimationPlayer: player=n
    if n is MeshInstance3D: meshes.append(n)
    for ch in n.get_children():scan(ch)
func capture(file:String,v:Array):
    var yaw=deg_to_rad(float(v[1]))
    var pitch=deg_to_rad(float(v[2]))
    var center: Vector3=v[3]
    camera.size=float(v[4])
    camera.position=center+Vector3(-sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))*2.0
    camera.look_at(center,Vector3.UP)
    for i in range(2):await process_frame
    await RenderingServer.frame_post_draw
    var error=root.get_texture().get_image().save_png(file)
    if error!=OK:push_error("Capture failed: "+file)
func bone_snapshot() -> Array:
    var snap=[]
    if skeleton:
        skeleton.force_update_all_bone_transforms()
        for k in range(skeleton.get_bone_count()):
            var p=skeleton.get_bone_global_pose(k)
            snap.append([p.origin.x,p.origin.y,p.origin.z,p.basis.x.x,p.basis.x.y,p.basis.x.z,p.basis.y.x,p.basis.y.y,p.basis.y.z,p.basis.z.x,p.basis.z.y,p.basis.z.z])
    return snap
func pose(clip:String,time:float):
    skeleton.reset_bone_poses()
    player.stop()
    if player.get_animation(clip).get_track_count()==0:
        skeleton.force_update_all_bone_transforms()
        return
    player.play(clip)
    player.seek(time,true)
    player.advance(0)
    skeleton.force_update_all_bone_transforms()
func run():
    camera=Camera3D.new()
    root.add_child(camera)
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL
    camera.current=true
    var env=WorldEnvironment.new()
    env.environment=Environment.new()
    env.environment.background_mode=Environment.BG_COLOR
    env.environment.background_color=Color(.88,.87,.85)
    env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.environment.ambient_light_color=Color.WHITE
    env.environment.ambient_light_energy=.5
    root.add_child(env)
    var sun=DirectionalLight3D.new()
    root.add_child(sun)
    sun.rotation_degrees=Vector3(-35,-35,0)
    sun.light_energy=.7
    var fill=DirectionalLight3D.new()
    root.add_child(fill)
    fill.rotation_degrees=Vector3(25,145,0)
    fill.light_energy=.45
    var source_paths=JSON.parse_string(FileAccess.get_file_as_string("res://sources.json"))
    var edited=JSON.parse_string(FileAccess.get_file_as_string("res://edited_triangles.json"))
    var reference_samples: Dictionary={}
    var reference_baked: Dictionary={}
    for label in ["V3","A","A2","B","B2","C"]:
        DirAccess.make_dir_recursive_absolute("res://captures_v3/"+label)
        var doc=GLTFDocument.new()
        var raw_state=GLTFState.new()
        var raw_error=doc.append_from_file(source_paths[label],raw_state)
        var state=GLTFState.new()
        var error=doc.append_from_file("res://"+label+"_compat.glb",state)
        if error!=OK:
            results[label]={"compat_append_error":error,"raw_append_error":raw_error}
            continue
        current_model=doc.generate_scene(state)
        root.add_child(current_model)
        skeleton=null;player=null;meshes=[]
        scan(current_model)
        player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
        player.stop()
        skeleton.reset_bone_poses()
        var report={"raw_append_error":raw_error,"compat_append_error":error,"bones":skeleton.get_bone_count(),"surfaces":0,"clips":[],"samples":[],"all_bone_samples_match_V3":true,"all_baked_vertices_finite":true,"all_baked_body_samples_match_V3":true,"all_baked_body_normals_match_V3":true,"baked_vertex_samples":0,"blend_shape_count":0}
        for m in meshes:
            report.surfaces+=m.mesh.get_surface_count()
            report.blend_shape_count+=m.mesh.get_blend_shape_count()
        for v in views:await capture("res://captures_v3/"+label+"/"+v[0]+".png",v)
        for clip in player.get_animation_list():
            var anim=player.get_animation(clip)
            var entry={"name":clip,"tracks":anim.get_track_count(),"length":anim.length,"bone_motion_observed":false}
            var first_snap=[]
            for fraction in [0.0,.25,.5,.75,1.0]:
                var tm=anim.length*fraction
                pose(clip,tm)
                var snap=bone_snapshot()
                if first_snap.is_empty():first_snap=snap
                if anim.get_track_count()>0 and snap!=first_snap:entry.bone_motion_observed=true
                var key=clip+":"+str(fraction)
                if label=="V3":reference_samples[key]=snap
                elif snap!=reference_samples[key]:report.all_bone_samples_match_V3=false
                var body_pos_hashes=[]
                var body_normal_hashes=[]
                for m in meshes:
                    var baked=m.bake_mesh_from_current_skeleton_pose()
                    if baked:
                        for surface in range(baked.get_surface_count()):
                            var arrays=baked.surface_get_arrays(surface)
                            var vertices=arrays[Mesh.ARRAY_VERTEX]
                            if surface>=2:
                                body_pos_hashes.append(hash(vertices.to_byte_array()))
                                body_normal_hashes.append(hash(arrays[Mesh.ARRAY_NORMAL].to_byte_array()))
                            report.baked_vertex_samples+=vertices.size()
                            for point in vertices:
                                if not point.is_finite():report.all_baked_vertices_finite=false
                if label=="V3":reference_baked[key]=[body_pos_hashes,body_normal_hashes]
                else:
                    if body_pos_hashes!=reference_baked[key][0]:report.all_baked_body_samples_match_V3=false
                    if body_normal_hashes!=reference_baked[key][1]:report.all_baked_body_normals_match_V3=false
                report.samples.append({"clip":clip,"time":tm,"bone_sample_matches_baseline":label=="V3" or snap==reference_samples[key]})
            report.clips.append(entry)
        for pair in [["Nod",.55],["HeadShake",.7],["Wave",.6],["Sit-pose",.033333335]]:
            if not player.has_animation(pair[0]):continue
            pose(pair[0],pair[1])
            for v in [views[0],views[2],views[3]]:
                var vp=v.duplicate()
                vp[3]=Vector3(0,.5,0);vp[4]=1.1
                await capture("res://captures_v3/"+label+"/pose_"+pair[0]+"_"+v[0]+".png",vp)
        player.stop();skeleton.reset_bone_poses()
        if label!="V3":
            # Only edited triangles: raw exported vertex positions, no drawing.
            current_model.visible=false
            var arr=[];arr.resize(Mesh.ARRAY_MAX)
            var positions=PackedVector3Array()
            for xyz in edited[label]:positions.append(Vector3(xyz[0],xyz[1],xyz[2]))
            arr[Mesh.ARRAY_VERTEX]=positions
            var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arr)
            var mat=StandardMaterial3D.new();mat.albedo_color=Color(.85,.06,.025);mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mat.cull_mode=BaseMaterial3D.CULL_DISABLED
            mesh.surface_set_material(0,mat)
            var instance=MeshInstance3D.new();instance.mesh=mesh;root.add_child(instance)
            for v in [views[0],views[1],views[2],views[7]]:await capture("res://captures_v3/"+label+"/editados_"+v[0]+".png",v)
            instance.queue_free()
        results[label]=report
        current_model.queue_free()
        await process_frame
        print("QA COMPLETE ",label)
    var output={"engine":Engine.get_version_info(),"renderer":"OpenGL compatibility / Mesa llvmpipe / Xvfb; real GLB geometry", "models":results,"limitations":["compat copies remove invalid empty primitives and 15 orphan facial channels; originals preserved","finite sampled animation vertices do not certify continuous collision-free motion","no artistic approval implied"]}
    var file=FileAccess.open("res://godot_report_v3.json",FileAccess.WRITE)
    file.store_string(JSON.stringify(output,"  "))
    quit()
