extends SceneTree
## CHXP V2 · motor de render por lotes (Godot 4.7, renderer Compatibility, sin GPU).
## Uso: xvfb-run -a godot --path copox/godot --script res://chxp2/chxp2.gd -- trabajo.json
## El trabajo (JSON) trae una lista de "tomas". Cada toma: un GLB (cargado en runtime con GLTFDocument: sin importar ni
## .import, nada que se cuelgue), piezas visibles/ocultas por nombre de nodo, vistas, clip y tiempos. Por cada imagen
## escribe cuatro pasadas: color (luz ALTH, sombras, MSAA), normales, profundidad (16 bits en RG) y máscara por pieza;
## y un JSON por toma con medidas, piezas, materiales y triángulos. La composición (AO, hoja, GIF) la hace Python.

const FONDO := Color("#E3E2E9")
const Resortes := preload("res://alth_resortes.gd")

var trabajo: Dictionary
var vp: SubViewport
var cam: Camera3D
var mundo: Node3D
var luz_clave: DirectionalLight3D
var piso: MeshInstance3D
var silueta: Node3D = null
var _piso_mat: Material


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("CHXP2: falta trabajo.json"); quit(2); return
	var f := FileAccess.open(args[0], FileAccess.READ)
	if f == null:
		push_error("CHXP2: no abre " + args[0]); quit(2); return
	trabajo = JSON.parse_string(f.get_as_text())
	_escena()
	_correr.call_deferred()


func _escena() -> void:
	var tam: int = int(trabajo.get("tam", 1024))
	vp = SubViewport.new()
	vp.size = Vector2i(tam, tam)
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.transparent_bg = false
	vp.own_world_3d = true
	root.add_child(vp)
	mundo = Node3D.new()
	vp.add_child(mundo)
	# ── luz ALTH: clave cálida suave con sombra, relleno frío, contraluz; ambiente claro (estilo de las hojas) ──
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = FONDO
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#EEF1F8")
	env.ambient_light_energy = 0.50
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_exposure = 1.0
	var we := WorldEnvironment.new()
	we.environment = env
	mundo.add_child(we)
	luz_clave = _luz(Color("#FFEBD6"), 0.52, Vector3(-50, -35, 0), true)
	_luz(Color("#D6E2F5"), 0.12, Vector3(-20, 140, 0), false)
	_luz(Color("#FFF4E6"), 0.16, Vector3(-30, 170, 0), false)
	# ── piso con rejilla (cuadros de 0.05 u, línea fuerte cada 0.25 u) ──
	piso = MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(12, 12)
	piso.mesh = pm
	var sm := ShaderMaterial.new()
	sm.shader = load("res://chxp2/piso.gdshader")
	piso.material_override = sm
	_piso_mat = sm
	mundo.add_child(piso)
	cam = Camera3D.new()
	cam.fov = float(trabajo.get("fov", 22.0))
	cam.near = 0.01
	cam.far = 60.0
	vp.add_child(cam)


func _luz(c: Color, e: float, rot_grados: Vector3, sombra: bool) -> DirectionalLight3D:
	var l := DirectionalLight3D.new()
	l.light_color = c
	l.light_energy = e
	l.rotation_degrees = rot_grados
	l.shadow_enabled = sombra
	if sombra:
		l.shadow_blur = 1.5
		l.shadow_bias = 0.03
		l.shadow_normal_bias = 1.5
		l.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		l.directional_shadow_max_distance = 6.0
	mundo.add_child(l)
	return l


func _cargar(ruta: String) -> Node3D:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(ruta, st)
	if err != OK:
		push_error("CHXP2: no carga " + ruta + " err=" + str(err))
		return null
	var escena := doc.generate_scene(st) as Node3D
	if escena != null:
		Resortes.sombras(escena)
	return escena


func _mallas(n: Node, out: Array) -> void:
	if n is MeshInstance3D:
		out.append(n)
	for h in n.get_children():
		_mallas(h, out)


func _visible_real(n: Node3D) -> bool:
	var x: Node = n
	while x != null and x is Node3D:
		if not (x as Node3D).visible:
			return false
		x = x.get_parent()
	return true


func _aplicar_visibilidad(escena: Node, vis: Dictionary) -> void:
	for nombre in vis.keys():
		var n := escena.find_child(nombre, true, false)
		if n is Node3D:
			(n as Node3D).visible = bool(vis[nombre])


func _anim(escena: Node) -> AnimationPlayer:
	var aps := escena.find_children("*", "AnimationPlayer", true, false)
	return aps[0] if aps.size() > 0 else null


func _posar(ap: AnimationPlayer, clip: String, t: float) -> void:
	if ap == null or clip == "" or clip == "reposo":
		return
	var c := clip
	if not ap.has_animation(c):
		c = clip.trim_suffix("-loop")
	if not ap.has_animation(c):
		push_warning("CHXP2: clip no existe " + clip)
		return
	ap.play(c)
	ap.seek(t * ap.current_animation_length, true)
	ap.pause()


func _simular(ap: AnimationPlayer, clip: String, t0: float, t1: float) -> void:
	# avanza la animación de t0 a t1 (fracción del clip) cuadro a cuadro a 60 fps (Godot corre con --fixed-fps 60):
	# los resortes del pelo simulan con el tiempo real del clip. Sin dibujar el viewport en los pasos intermedios.
	if t1 < t0:
		t1 += 1.0                                          # el GIF da la vuelta: seguir hacia adelante
	var c := clip if ap.has_animation(clip) else clip.trim_suffix("-loop")
	var largo := ap.get_animation(c).length if ap.has_animation(c) else 1.0
	var pasos := maxi(1, int(ceil((t1 - t0) * largo * 60.0)))
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	for k in pasos:
		var tt := t0 + (t1 - t0) * float(k + 1) / float(pasos)
		_posar(ap, clip, fmod(tt, 1.0) if tt < 1.0 or clip.ends_with("-loop") else minf(tt, 1.0))
		await process_frame
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS


func _caja(mallas: Array) -> AABB:
	var a := AABB()
	var hay := false
	for m in mallas:
		var mi := m as MeshInstance3D
		if mi.mesh == null or not _visible_real(mi):
			continue
		var b := mi.global_transform * mi.get_aabb()
		if mi.skeleton != NodePath() and mi.skin != null:
			b = _caja_piel(mi)
		a = b if not hay else a.merge(b)
		hay = true
	return a


func _caja_piel(mi: MeshInstance3D) -> AABB:
	# malla con piel: la AABB de la malla está en pose de reposo; usar los huesos posados como aproximación segura
	var sk := mi.get_node_or_null(mi.skeleton) as Skeleton3D
	var b := mi.global_transform * mi.get_aabb()
	if sk == null:
		return b
	for i in sk.get_bone_count():
		var p: Vector3 = sk.global_transform * sk.get_bone_global_pose(i).origin
		b = b.expand(p)
	return b


func _encuadrar(caja: AABB, yaw: float, elev: float, margen: float) -> void:
	var centro := caja.get_center()
	var radio := caja.size.length() * 0.5 * margen
	var dist := radio / tan(deg_to_rad(cam.fov * 0.5))
	var dir := Vector3(sin(deg_to_rad(yaw)) * cos(deg_to_rad(elev)), sin(deg_to_rad(elev)),
		cos(deg_to_rad(yaw)) * cos(deg_to_rad(elev)))
	cam.global_position = centro + dir * dist
	cam.look_at(centro, Vector3.UP if abs(elev) < 89.0 else Vector3.FORWARD)


func _pasada_material(tipo: String, idx: int) -> Material:
	var sm := ShaderMaterial.new()
	sm.shader = load("res://chxp2/pasada.gdshader")
	sm.set_shader_parameter("modo", {"normal": 1, "profundidad": 2, "mascara": 3}[tipo])
	sm.set_shader_parameter("id_color", _color_id(idx))
	sm.set_shader_parameter("cerca", cam.near)
	sm.set_shader_parameter("lejos", float(trabajo.get("lejos_prof", 8.0)))
	return sm


func _color_id(i: int) -> Color:
	# máscara: rejilla de 5 niveles por canal (125 colores bien separados); 0 = sin pieza. Python decodifica por el
	# color más cercano (el renderer no deja los valores bajos exactos, así que nada de bits finos)
	var k := i + 1
	return Color((k % 5) / 4.0, ((k / 5) % 5) / 4.0, ((k / 25) % 5) / 4.0)


func _guardar(ruta: String) -> void:
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	img.save_png(ruta)


func _correr() -> void:
	var tomas: Array = trabajo.get("tomas", [])
	var salida: String = trabajo.get("salida", "user://chxp2")
	DirAccess.make_dir_recursive_absolute(salida)
	var resumen := []
	for ti in tomas.size():
		var toma: Dictionary = tomas[ti]
		var t0 := Time.get_ticks_msec()
		var escena := _cargar(toma["glb"])
		if escena == null:
			resumen.append({"toma": toma.get("nombre", str(ti)), "error": "no carga"})
			continue
		mundo.add_child(escena)
		_aplicar_visibilidad(escena, toma.get("visible", {}))
		var ap := _anim(escena)
		var mallas := []
		_mallas(escena, mallas)
		# silueta de Adán a escala al lado
		if toma.has("silueta") and String(toma["silueta"]) != "":
			silueta = _cargar(toma["silueta"])
			if silueta != null:
				mundo.add_child(silueta)
				_aplicar_visibilidad(silueta, toma.get("silueta_visible", {}))
				var ms := []
				_mallas(silueta, ms)
				var mat := StandardMaterial3D.new()
				mat.albedo_color = Color(0.32, 0.31, 0.36, 1)
				mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				for m in ms:
					(m as MeshInstance3D).material_override = mat
		await process_frame
		var caja0 := _caja(mallas)
		if silueta != null:
			var ancho := maxf(caja0.size.x, 0.2)
			silueta.position = Vector3(caja0.position.x - 0.13 - ancho * 0.05, 0, caja0.get_center().z - 0.08)
		var nombre: String = toma.get("nombre", "toma%02d" % ti)
		var info := {"nombre": nombre, "glb": toma["glb"], "imagenes": [], "piezas": []}
		# piezas: nombre de nodo, material, triángulos, color base
		var leyenda := {}
		for i in mallas.size():
			var mi := mallas[i] as MeshInstance3D
			var tris := 0
			var mats := []
			if mi.mesh != null:
				for s in mi.mesh.get_surface_count():
					var arr := mi.mesh.surface_get_arrays(s)
					var ind = arr[Mesh.ARRAY_INDEX]
					tris += (ind.size() / 3) if ind != null else (arr[Mesh.ARRAY_VERTEX].size() / 3)
					var mt := mi.get_active_material(s)
					var col := ""
					if mt is BaseMaterial3D:
						col = (mt as BaseMaterial3D).albedo_color.to_html(false)
					mats.append({"nombre": mt.resource_name if mt != null else "", "color": col})
			var pieza := {"id": i + 1, "nodo": String(mi.name), "padre": String(mi.get_parent().name),
				"visible": _visible_real(mi), "triangulos": tris, "materiales": mats}
			info["piezas"].append(pieza)
			leyenda[str(i + 1)] = String(mi.name)
		var vistas: Array = toma.get("vistas", [{"nombre": "frente", "yaw": 0, "elev": 8}])
		var tiempos: Array = toma.get("tiempos", [0.0])
		var pasadas: Array = toma.get("pasadas", ["color", "normal", "profundidad", "mascara"])
		var clip: String = toma.get("clip", "reposo")
		var ap_sil: AnimationPlayer = _anim(silueta) if silueta != null else null
		# pelo con resortes (huesos Pelo_*): simulación determinista, avanzando el esqueleto a mano entre cuadros
		var esqueletos := []
		if bool(toma.get("resortes", true)) and ap != null and clip != "reposo":
			for sim in Resortes.aplicar(escena, false):
				esqueletos.append(sim.get_parent())
		var t_prev := 0.0
		if esqueletos.size() > 0:
			info["resortes"] = esqueletos.size()
			await _simular(ap, clip, 0.0, 1.0)                  # una vuelta del clip para asentar el pelo
			await _simular(ap, clip, 0.0, float(tiempos[0]))
			t_prev = float(tiempos[0])
		for t in tiempos:
			if esqueletos.size() > 0:
				await _simular(ap, clip, t_prev, float(t))
				t_prev = float(t)
			else:
				_posar(ap, clip, float(t))
			_posar(ap_sil, clip, float(t))
			await process_frame
			var caja := _caja(mallas)
			if silueta != null:
				var cs := []
				_mallas(silueta, cs)
				caja = caja.merge(_caja(cs)) if toma.get("encuadre_con_silueta", true) else caja
			if toma.has("caja_fija"):                    # encuadre fijo (p. ej. la cabeza de Adán)
				var cf: Array = toma["caja_fija"]
				caja = AABB(Vector3(cf[0], cf[1], cf[2]), Vector3(cf[3] - cf[0], cf[4] - cf[1], cf[5] - cf[2]))
			elif toma.has("y_rango"):                      # encuadre de una región (p. ej. la cabeza)
				var yr: Array = toma["y_rango"]
				var y0 := maxf(caja.position.y, float(yr[0]))
				var y1 := minf(caja.end.y, float(yr[1]))
				caja = AABB(Vector3(caja.position.x, y0, caja.position.z), Vector3(caja.size.x, y1 - y0, caja.size.z))
			info["caja"] = {"pos": [caja.position.x, caja.position.y, caja.position.z],
				"tam": [caja.size.x, caja.size.y, caja.size.z]}
			for v in vistas:
				_encuadrar(caja, float(v.get("yaw", 0)), float(v.get("elev", 8)), float(toma.get("margen", 0.92)))
				piso.position.y = 0.0
				for p in pasadas:
					for i in mallas.size():
						var mi := mallas[i] as MeshInstance3D
						mi.material_override = null if p == "color" else _pasada_material(p, i)
					# el piso entra en color y en profundidad (para la sombra de contacto); fuera de normal y máscara
					piso.visible = p == "color" or p == "profundidad"
					piso.material_override = _piso_mat if p == "color" else _pasada_material(p, -1)
					if silueta != null:
						silueta.visible = p == "color"
					var archivo := "%s/%s_%s_t%03d_%s.png" % [salida, nombre, v.get("nombre", "v"), int(round(float(t) * 1000)), p]
					await _guardar(archivo)
					info["imagenes"].append({"vista": v.get("nombre", "v"), "t": t, "pasada": p, "archivo": archivo,
						"camara": {"pos": [cam.global_position.x, cam.global_position.y, cam.global_position.z],
							"fov": cam.fov}})
				for i in mallas.size():
					(mallas[i] as MeshInstance3D).material_override = null
				piso.visible = true
				piso.material_override = _piso_mat
				if silueta != null:
					silueta.visible = true
		info["leyenda_mascara"] = leyenda
		info["segundos"] = (Time.get_ticks_msec() - t0) / 1000.0
		var fj := FileAccess.open("%s/%s.json" % [salida, nombre], FileAccess.WRITE)
		fj.store_string(JSON.stringify(info, "  "))
		fj.close()
		resumen.append({"toma": nombre, "segundos": info["segundos"], "imagenes": info["imagenes"].size()})
		escena.queue_free()
		if silueta != null:
			silueta.queue_free()
			silueta = null
		await process_frame
	var fr := FileAccess.open("%s/_resumen.json" % salida, FileAccess.WRITE)
	fr.store_string(JSON.stringify(resumen, "  "))
	fr.close()
	print("CHXP2 OK ", resumen.size(), " tomas")
	quit(0)
