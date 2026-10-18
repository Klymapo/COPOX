extends Node3D
## COPOX · prueba del sistema de agarre: Adán sostiene la pistola con el agarre resuelto (AGARRE_PISTOLA) y aprieta
## el gatillo con ControladorAdan.disparar(). Usa el mismo banco/controlador que el juego.
## godot --path . res://armas/prueba_disparo.tscn -- salida=/carpeta [cuerpo=Aim foco=RightIndexDistal alto=0.08 yaw=-110 elev=-25 tam=420]
## Escribe f_000.png … (antes, durante y después del disparo).

func _ready() -> void:
	var a := {}
	for s in OS.get_cmdline_user_args():
		var kv := s.split("=", true, 1)
		if kv.size() == 2: a[kv[0]] = kv[1]
	var tam := int(a.get("tam", "420"))
	get_window().size = Vector2i(tam, tam)
	var env := WorldEnvironment.new(); var e := Environment.new()
	e.background_mode = Environment.BG_COLOR; e.background_color = Color8(236, 236, 236)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(1, 1, 1); e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e; add_child(env)
	var sol := DirectionalLight3D.new(); sol.rotation_degrees = Vector3(-40, -30, 0); sol.light_energy = 0.12; sol.shadow_enabled = not a.has("sinsombra"); add_child(sol)
	var adan: Node3D = load(a.get("modelo", "res://theo.glb")).instantiate(); add_child(adan)
	var banco := BancoMovimiento.new(); banco.manual = true; add_child(banco); banco.montar(adan); banco.parpadeo_auto = false
	var sk: Skeleton3D
	for n in adan.find_children("*", "Skeleton3D", true, false): sk = n
	var ctl := ControladorAdan.new(); add_child(ctl); ctl.montar(adan, banco); ctl.mueve_nodo = false
	if not a.has("sinarma"): ctl.equipar(a.get("arma", "res://armas/PISTOLA_ALTH_PROVISIONAL.glb"), "Pistola")
	if a.has("sinmano"): banco.tree.set("parameters/capa_mano_r/blend_amount", 0.0)
	if a.has("solo_socket"):
		var so: Node3D = adan.find_child("AGARRE_PISTOLA", true, false)
		so.add_child(load("res://armas/PISTOLA_ALTH_PROVISIONAL.glb").instantiate())
	if a.has("solo_mano"): banco.mano_derecha("Pistola_Agarre")
	banco.gesto(a.get("cuerpo", "Aim"))
	var cam := Camera3D.new(); cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size = float(a.get("alto", "0.08"))
	add_child(cam); cam.current = true
	var yaw := deg_to_rad(float(a.get("yaw", "-110"))); var el := deg_to_rad(float(a.get("elev", "-25")))
	var dt := 1.0 / 30.0
	await get_tree().process_frame        # el AnimationTree necesita estar listo en el árbol antes de avanzar
	for i in 20:                          # entra a la pose
		ctl.avanzar(dt)
		await get_tree().process_frame
	if a.has("debug"):
		print("DBG mano_r ", banco._mano_r.get_current_node(), " blend ", banco.tree.get("parameters/capa_mano_r/blend_amount"), " estados ", banco._estados_mano_r)
		print("DBG filtro ", (banco.tree.tree_root as AnimationNodeBlendTree).get_node("capa_mano_r").filter_enabled)
		print("DBG pose idx ", sk.get_bone_pose_rotation(sk.find_bone("RightIndexProximal")), " arm ", sk.get_bone_pose_rotation(sk.find_bone("RightUpperArm")))
	var k := 0
	for i in 24:
		if i == 4: ctl.disparar()
		ctl.avanzar(dt)
		var obj: Vector3 = sk.global_transform * sk.get_bone_global_pose(sk.find_bone(a.get("foco", "RightIndexDistal"))).origin
		cam.position = obj + Vector3(sin(yaw) * cos(el), sin(el), cos(yaw) * cos(el)) * 3.0
		cam.look_at(obj, Vector3.UP)
		await RenderingServer.frame_post_draw
		if a.has("manos"): print("MANOS %d %s L=%s R=%s" % [k, banco.cuerpo_actual(), ctl.mano_actual("L"), ctl.mano_actual("R")])
		get_viewport().get_texture().get_image().save_png(a.get("salida", "/tmp") + "/f_%03d.png" % k)
		k += 1
	get_tree().quit()
