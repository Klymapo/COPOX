extends Node3D
## COPOX · prueba de agarre de armas PROVISIONALES (florete y pistola) en la mano derecha de Adán.
## godot --path . res://armas/prueba_armas.tscn -- arma=res://armas/PISTOLA_ALTH_PROVISIONAL.glb cuerpo=Point t=0.5 mano=M36_3_Apuntar salida=/ruta.png yaw=-60 alto=0.6 cy=0.45
## Extras: foco=RightIndexIntermediate (cámara centrada en ese hueso) · indice=grados (flexión del índice, gatillo)
## El arma se coloca con su nodo AGARRE alineado al marco de agarre de la mano:
##   eje y = del meñique al índice (a lo largo de la empuñadura), eje x = hacia donde apunta el antebrazo,
##   centro = entre la palma y la punta del dedo medio doblado.

const MANO := ["Thumb", "Index", "Middle", "Ring", "Little"]

func _ready() -> void:
	var a := {}
	for s in OS.get_cmdline_user_args():
		var kv := s.split("=", true, 1)
		if kv.size() == 2: a[kv[0]] = kv[1]
	var tam := int(a.get("tam", "512"))
	get_window().size = Vector2i(tam, tam)
	var env := WorldEnvironment.new(); var e := Environment.new()
	e.background_mode = Environment.BG_COLOR; e.background_color = Color8(236, 236, 236)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(1, 1, 1); e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e; add_child(env)
	var sol := DirectionalLight3D.new(); sol.rotation_degrees = Vector3(-40, -30, 0); sol.light_energy = 0.12; sol.shadow_enabled = true; add_child(sol)
	var adan: Node3D = load(a.get("modelo", "res://theo.glb")).instantiate(); add_child(adan)
	var ap: AnimationPlayer
	for n in adan.find_children("*", "AnimationPlayer", true, false): ap = n
	var sk: Skeleton3D
	for n in adan.find_children("*", "Skeleton3D", true, false): sk = n
	var cuerpo: String = a.get("cuerpo", "Idle")
	ap.play(cuerpo); ap.seek(ap.current_animation_length * float(a.get("t", "0")), true); ap.pause()
	# dedos de la mano derecha desde el clip de mano (sin tocar la muñeca, que viene del cuerpo)
	var anim := ap.get_animation(a.get("mano", "M36_3_Apuntar"))
	for tr in anim.get_track_count():
		if anim.track_get_type(tr) != Animation.TYPE_ROTATION_3D: continue
		var hueso := String(anim.track_get_path(tr).get_concatenated_subnames())
		if not hueso.begins_with("Right") or hueso == "RightHand": continue
		var ok := false
		for m in MANO: ok = ok or hueso.contains(m)
		if not ok: continue
		var i := sk.find_bone(hueso)
		if i >= 0: sk.set_bone_pose_rotation(i, anim.rotation_track_interpolate(tr, anim.length))
	# agarre=ruta.json (copox/movimiento/agarre.py): rotaciones de dedos y arma→mano calculadas; reemplaza al marco viejo
	var agarre_json := {}
	if a.has("agarre"):
		agarre_json = JSON.parse_string(FileAccess.get_file_as_string(a["agarre"]))
		var rots: Dictionary = agarre_json["rotaciones"]
		if a.has("cuadro") and agarre_json.has("accion"):   # cuadro k de la acción (p. ej. apretar el gatillo)
			var cu: Dictionary = agarre_json["accion"]["cuadros"][int(a["cuadro"])]
			rots = cu["rotaciones"]
			a["gatillo"] = str(cu["angulo"])
		for h in rots:
			var bi := sk.find_bone(h)
			var q: Array = rots[h]
			if bi >= 0: sk.set_bone_pose_rotation(bi, Quaternion(q[0], q[1], q[2], q[3]))
	# indice=grados: flexión del índice (las tres falanges) para el gatillo; 0 = recto
	if a.has("indice"):
		var g := float(a["indice"])
		var reparto := {"RightIndexProximal": 0.45, "RightIndexIntermediate": 0.35, "RightIndexDistal": 0.20}
		for h in reparto:
			var bi := sk.find_bone(h)
			if bi >= 0: sk.set_bone_pose_rotation(bi, Quaternion(Vector3(0, 0, 1), deg_to_rad(g * reparto[h])))
	sk.force_update_all_bone_transforms()
	var gp := func(n): return sk.global_transform * sk.get_bone_global_pose(sk.find_bone(n)).origin
	var W: Vector3 = gp.call("RightHand"); var Ip: Vector3 = gp.call("RightIndexProximal")
	var Lp: Vector3 = gp.call("RightLittleProximal"); var Md: Vector3 = gp.call("RightMiddleDistal")
	var Fa: Vector3 = gp.call("RightLowerArm")
	var y := (Ip - Lp).normalized()
	var x := (W - Fa); x = (x - y * x.dot(y)).normalized()
	var z := x.cross(y).normalized()
	var palma := W.lerp((Ip + Lp) * 0.5, 0.75)
	var c := (palma + Md) * 0.5
	var G := Transform3D(Basis(x, y, z), c)
	var arma: Node3D = load(a.get("arma", "res://armas/PISTOLA_ALTH_PROVISIONAL.glb")).instantiate()
	if a.has("gatillo"):
		var gt: Node3D = arma.find_child("GATILLO", true, false)
		if gt: gt.rotation.z = -float(a["gatillo"])
	var agarre: Node3D = arma.find_child("AGARRE", true, false)
	var A := agarre.global_transform if agarre.is_inside_tree() else agarre.transform
	add_child(arma)
	arma.global_transform = G * A.affine_inverse()
	# el arma se queda pegada a la mano: BoneAttachment3D (así se usa en el juego)
	var ba := BoneAttachment3D.new(); ba.bone_name = "RightHand"; sk.add_child(ba)
	var rel := ba.global_transform.affine_inverse() * arma.global_transform
	if agarre_json.has("objeto_en_mano"):
		var M: Array = agarre_json["objeto_en_mano"]
		rel = Transform3D(Basis(Vector3(M[0][0], M[1][0], M[2][0]), Vector3(M[0][1], M[1][1], M[2][1]), Vector3(M[0][2], M[1][2], M[2][2])), Vector3(M[0][3], M[1][3], M[2][3]))
	arma.reparent(ba); arma.transform = rel
	var cam := Camera3D.new(); cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size = float(a.get("alto", "0.6"))
	var yaw := deg_to_rad(float(a.get("yaw", "-60"))); var el := deg_to_rad(float(a.get("elev", "10")))
	var obj := Vector3(float(a.get("cx", "0")), float(a.get("cy", "0.45")), float(a.get("cz", "0")))
	if a.has("foco"):   # centra la cámara en un hueso (p. ej. foco=RightIndexIntermediate para ver el gatillo)
		obj = gp.call(a["foco"])
	cam.position = obj + Vector3(sin(yaw) * cos(el), sin(el), cos(yaw) * cos(el)) * 3.0
	add_child(cam); cam.look_at(obj, Vector3.UP); cam.current = true
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(a.get("salida", "/tmp/armas.png"))
	get_tree().quit()
