extends Node3D
# Uso: godot --path . -- modelo=res://theo.glb salida=/ruta/out.png yaw=35 elev=5 alto=0.5 cy=0.62 clip=Idle-loop t=0 tam=512 [mirada=x:y]
func _ready():
	var a := {}
	for s in OS.get_cmdline_user_args():
		var kv = s.split("=", true, 1)
		if kv.size() == 2: a[kv[0]] = kv[1]
	var ruta = a.get("modelo", "res://theo.glb")
	var escena = load(ruta).instantiate()
	add_child(escena)
	var tam = int(a.get("tam", "512"))
	get_window().size = Vector2i(tam, tam)
	var env = WorldEnvironment.new(); var e = Environment.new()
	e.background_mode = Environment.BG_COLOR; e.background_color = Color8(236,236,236)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(1,1,1); e.ambient_light_energy = float(a.get("amb", "0.55"))
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e; add_child(env)
	var sol = DirectionalLight3D.new(); sol.rotation_degrees = Vector3(-40, -30, 0); sol.light_energy = float(a.get("sol", "0.12")); sol.shadow_enabled = true; add_child(sol)
	var rel = DirectionalLight3D.new(); rel.rotation_degrees = Vector3(-10, 50, 0); rel.light_energy = 0.05; add_child(rel)
	var cam = Camera3D.new(); cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = float(a.get("alto", "1.0"))
	var yaw = deg_to_rad(float(a.get("yaw", "0"))); var el = deg_to_rad(float(a.get("elev", "5")))
	var cy = float(a.get("cy", "0.43"))
	var obj = Vector3(0, cy, 0)
	cam.position = obj + Vector3(sin(yaw)*cos(el), sin(el), cos(yaw)*cos(el)) * 3.0
	add_child(cam); cam.look_at(obj, Vector3.UP); cam.current = true
	var ap: AnimationPlayer = null
	for n in escena.find_children("*", "AnimationPlayer", true, false): ap = n
	if ap: print("ANIMS ", Array(ap.get_animation_list()).filter(func(x): return "dle" in x))
	for mi in escena.find_children("*", "MeshInstance3D", true, false):
		for si in mi.get_surface_override_material_count():
			var mat = mi.mesh.surface_get_material(si)
			if mat is StandardMaterial3D and si < 1: print("MAT0 vc_albedo=", mat.vertex_color_use_as_albedo, " cull=", mat.cull_mode)
	var clip = a.get("clip", "Idle-loop")
	if ap and not ap.has_animation(clip): clip = clip.trim_suffix("-loop")   # Godot quita el sufijo -loop al importar
	if ap and ap.has_animation(clip):
		ap.play(clip); ap.seek(float(a.get("t", "0")) * ap.current_animation_length, true); ap.pause()
	if a.has("mirada"):
		var ojos = load("res://ojos/ojos_alth.gd").new()
		print("OJOS shader en ", ojos.aplicar(escena), " superficies")
		var mv = a["mirada"].split(":")
		ojos.mirada = Vector2(float(mv[0]), float(mv[1]))
	for m in a.get("morph", "").split(",", false):
		var kv = m.split(":")
		for mi in escena.find_children("*", "MeshInstance3D", true, false):
			var i = mi.find_blend_shape_by_name(kv[0])
			if i >= 0: mi.set_blend_shape_value(i, float(kv[1]))
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img = get_viewport().get_texture().get_image()
	img.save_png(a.get("salida", "/tmp/visor.png"))
	get_tree().quit()
