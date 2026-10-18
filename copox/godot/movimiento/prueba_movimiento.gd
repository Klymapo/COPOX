extends Node3D
## COPOX · banco de pruebas de movimiento (Godot 4.7.2, headless con xvfb).
##
## godot --path . res://movimiento/prueba_movimiento.tscn -- modelo=res://theo.glb modo=secuencia salida=/ruta/carpeta [fps=15 tam=384 yaw=-30]
## godot --path . res://movimiento/prueba_movimiento.tscn -- modo=clips clips=Wave,Think n=6 vistas=0,-35 salida=/ruta/carpeta
## godot --path . res://movimiento/prueba_movimiento.tscn -- modo=caras salida=/ruta/carpeta
##
## secuencia: el banco (AnimationTree) actuando una escena con fundidos, cara, parpadeo y mirada → frames para GIF.
## clips: n frames repartidos de cada clip (sin fundidos), una imagen por frame y vista.
## caras: cada expresión G*/V04*/Talk en primer plano.

## Escena de prueba: [segundo, gesto de cuerpo, cara, mirada x, mirada y]
const GUION := [
	[0.0, "Idle", "neutra", 0.0, 0.0],
	[1.5, "Wave", "G23_1_Saludo", 0.0, 0.0],
	[4.0, "Nod", "G23_3_RespuestaAmable", 0.0, -0.2],
	[5.5, "TalkGesture", "Talk-loop", 0.2, 0.0],
	[8.5, "Think", "G26_1_Concentrado", 0.5, 0.5],
	[11.5, "Shrug", "G24_4_Confundido", 0.0, 0.0],
	[13.5, "HeadShake", "G25_4_Desprecio", -0.3, 0.0],
	[15.5, "Laugh", "G23_5_RisaContenida", 0.0, 0.0],
	[17.5, "Point", "G26_2_Realizacion", 0.8, 0.0],
	[20.0, "Idle", "neutra", 0.0, 0.0],
]
var FIN_GUION := 22.0

var a := {}
var cam: Camera3D


func _ready() -> void:
	for s in OS.get_cmdline_user_args():
		var kv := s.split("=", true, 1)
		if kv.size() == 2: a[kv[0]] = kv[1]
	var tam := int(a.get("tam", "384"))
	get_window().size = Vector2i(tam, tam)
	_luces()
	var personaje: Node3D = load(a.get("modelo", "res://theo.glb")).instantiate()
	add_child(personaje)
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	add_child(cam)
	var salida: String = a.get("salida", "/tmp/mov")
	DirAccess.make_dir_recursive_absolute(salida)
	match a.get("modo", "secuencia"):
		"secuencia": await _secuencia(personaje, salida)
		"clips": await _clips(personaje, salida)
		"caras": await _caras(personaje, salida)
	get_tree().quit()


func _luces() -> void:
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color8(236, 236, 236)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(1, 1, 1)
	e.ambient_light_energy = float(a.get("amb", "0.55"))
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e
	add_child(env)
	var sol := DirectionalLight3D.new()
	sol.rotation_degrees = Vector3(-40, -30, 0)
	sol.light_energy = float(a.get("sol", "0.12"))
	sol.shadow_enabled = true
	add_child(sol)
	var rel := DirectionalLight3D.new()
	rel.rotation_degrees = Vector3(-10, 50, 0)
	rel.light_energy = 0.05
	add_child(rel)
	var piso := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(3, 3)
	piso.mesh = pm
	var mp := StandardMaterial3D.new()
	mp.albedo_color = Color8(214, 214, 214)
	piso.material_override = mp
	add_child(piso)


func _encuadre(yaw_deg: float, alto: float, cy: float, elev := 5.0) -> void:
	cam.size = alto
	var yaw := deg_to_rad(yaw_deg)
	var el := deg_to_rad(elev)
	var obj := Vector3(0, cy, 0)
	cam.position = obj + Vector3(sin(yaw) * cos(el), sin(el), cos(yaw) * cos(el)) * 3.0
	cam.look_at(obj, Vector3.UP)
	cam.current = true


func _foto(ruta: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(ruta)


func _secuencia(personaje: Node3D, salida: String) -> void:
	var banco := BancoMovimiento.new()
	banco.manual = true
	add_child(banco)
	banco.montar(personaje)
	print("CUERPO ", banco.estados_cuerpo())
	print("CARA ", banco.estados_cara())
	_encuadre(float(a.get("yaw", "-30")), float(a.get("alto", "1.0")), float(a.get("cy", "0.43")))
	FIN_GUION = float(a.get("fin", str(FIN_GUION)))
	var fps := float(a.get("fps", "15"))
	var dt := 1.0 / fps
	var paso := 0
	var t := 0.0
	var log := FileAccess.open(salida + "/guion.txt", FileAccess.WRITE)
	while t < FIN_GUION:
		while paso < GUION.size() and GUION[paso][0] <= t + 1e-6:
			var g = GUION[paso]
			banco.gesto(g[1], g[2])
			banco.mirada = Vector2(g[3], g[4])
			log.store_line("%.2f %s %s" % [t, g[1], g[2]])
			paso += 1
		banco.avanzar(dt)
		await _foto("%s/f_%04d.png" % [salida, int(round(t * fps))])
		log.store_line("%.2f cuerpo=%s cara=%s" % [t, banco.cuerpo_actual(), banco.cara_actual()])
		t += dt
	log.close()


func _clips(personaje: Node3D, salida: String) -> void:
	var ap: AnimationPlayer
	for n in personaje.find_children("*", "AnimationPlayer", true, false): ap = n
	var lista: PackedStringArray = a.get("clips", "").split(",", false)
	if lista.is_empty(): lista = ap.get_animation_list()
	var n := int(a.get("n", "6"))
	var vistas: PackedStringArray = a.get("vistas", "0,-35").split(",")
	var alto := float(a.get("alto", "1.0"))
	var cy := float(a.get("cy", "0.43"))
	for clip in lista:
		if not ap.has_animation(clip): clip = clip.trim_suffix("-loop")
		if not ap.has_animation(clip):
			print("FALTA ", clip)
			continue
		ap.play(clip)
		var L := ap.current_animation_length
		for i in n:
			ap.seek(L * i / max(n - 1, 1), true)
			ap.pause()
			for v in vistas:
				_encuadre(float(v), alto, cy)
				await _foto("%s/%s__v%s__%02d.png" % [salida, clip, v, i])


func _caras(personaje: Node3D, salida: String) -> void:
	var ap: AnimationPlayer
	for n in personaje.find_children("*", "AnimationPlayer", true, false): ap = n
	var ojos := OjosALTH.new()
	ojos.aplicar(personaje)
	_encuadre(float(a.get("yaw", "-20")), float(a.get("alto", "0.42")), float(a.get("cy", "0.63")), 3.0)
	if ap.has_animation("Idle"):
		ap.play("Idle"); ap.seek(0.0, true); ap.pause()
	await _foto("%s/cara__neutra.png" % salida)
	for clip in ap.get_animation_list():
		if not (clip.begins_with("G2") or clip.begins_with("V04")): continue
		ap.play(clip)
		ap.seek(ap.current_animation_length, true)
		ap.pause()
		await _foto("%s/cara__%s.png" % [salida, clip])
