extends Node3D
## COPOX · escena final de prueba de movimiento: caminar → correr → saltar → dash → detenerse → señalar →
## puñetazos → sacar pistola y apuntar. Cámara que sigue. Frames a una carpeta (para GIF).
## godot --path . res://movimiento/prueba_controlador.tscn -- salida=/ruta fps=15 tam=420

const GUION := [
	[0.0, "idle"], [1.0, "caminar"], [3.5, "correr"], [5.5, "saltar"], [6.6, "correr"], [7.4, "dash"],
	[8.0, "parar"], [8.8, "senalar", "G26_2_Realizacion"], [10.4, "golpe_R", "G25_2_Desafiante"],
	[11.1, "golpe_L"], [11.8, "golpe_R"], [12.8, "pistola", "G26_1_Concentrado"], [15.0, "fin"],
]

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
	var sol := DirectionalLight3D.new(); sol.rotation_degrees = Vector3(-50, -30, 0); sol.light_energy = 0.12; sol.shadow_enabled = true; add_child(sol)
	# piso con cuadrícula (para ver si los pies patinan)
	for i in range(-6, 30):
		for k in range(-6, 6):
			var m := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(0.25, 0.25); m.mesh = pm
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color8(214, 214, 214) if (i + k) % 2 == 0 else Color8(196, 196, 200)
			m.material_override = mat; m.position = Vector3(k * 0.25, 0, i * 0.25); add_child(m)
	var adan: Node3D = load(a.get("modelo", "res://theo.glb")).instantiate(); add_child(adan)
	var banco := BancoMovimiento.new(); banco.manual = true; add_child(banco); banco.montar(adan)
	var ctl := ControladorAdan.new(); add_child(ctl); ctl.montar(adan, banco)
	var cam := Camera3D.new(); cam.fov = 40; add_child(cam); cam.current = true
	var salida: String = a.get("salida", "/tmp/ctl")
	DirAccess.make_dir_recursive_absolute(salida)
	var fps := float(a.get("fps", "15")); var dt := 1.0 / fps
	var t := 0.0; var paso := 0; var cuadro := 0
	var log := FileAccess.open(salida + "/guion.txt", FileAccess.WRITE)
	while t < GUION[-1][0]:
		while paso < GUION.size() and GUION[paso][0] <= t + 1e-6:
			var g = GUION[paso]
			match g[1]:
				"caminar": ctl.mover(Vector3(0, 0, 1), false)
				"correr": ctl.mover(Vector3(0, 0, 1), true)
				"saltar": ctl.saltar()
				"dash": ctl.dash()
				"parar": ctl.mover(Vector3.ZERO)
				"senalar": ctl.senalar()
				"golpe_R": ctl.golpe("R")
				"golpe_L": ctl.golpe("L")
				"pistola": ctl.equipar("res://armas/PISTOLA_ALTH_PROVISIONAL.glb"); ctl.apuntar()
			if g.size() > 2: banco.cara(g[2])
			log.store_line("%.2f %s" % [t, g[1]])
			paso += 1
		ctl.avanzar(dt)
		var p := adan.global_position
		cam.position = p + Vector3(-1.55, 0.75, 0.9)
		cam.look_at(p + Vector3(0, 0.40, 0.15), Vector3.UP)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/f_%04d.png" % [salida, cuadro])
		log.store_line("%.2f z=%.3f estado=%s" % [t, p.z, banco.cuerpo_actual()])
		cuadro += 1; t += dt
	log.close()
	get_tree().quit()
