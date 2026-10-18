## COPOX · ALTH-META: capas de animación para personajes con el rig de Adán.
## Cuerpo (máquina de estados) + cara (máquina de estados, solo morphs) + parpadeo (one-shot) + mirada (OjosALTH).
##
## Uso:
##   var banco := BancoMovimiento.new()
##   banco.montar($Adan)                  # nodo raíz del GLB importado
##   banco.gesto("Wave", "G23_1_Saludo")  # gesto de cuerpo + expresión
##   banco.cara("Talk-loop")              # solo cambia la cara
##   banco.mirada = Vector2(0.3, 0.1)
## Por defecto se reproduce sola (_process). Con manual = true se avanza con avanzar(dt).
class_name BancoMovimiento
extends Node

## Clips de cuerpo que vuelven solos al reposo al terminar.
const REPOSO := "Idle"
const FUNDIDO_CUERPO := 0.3
const FUNDIDO_CARA := 0.2

var manual := false
var parpadeo_auto := true          ## parpadea cada 2–5 s
var tree: AnimationTree
var ap: AnimationPlayer
var ojos: OjosALTH
var mirada := Vector2.ZERO:
	set(v):
		mirada = v
		if ojos: ojos.mirada = v

var _cuerpo: AnimationNodeStateMachinePlayback
var _cara: AnimationNodeStateMachinePlayback
var _estados_cuerpo: PackedStringArray = []
var _estados_cara: PackedStringArray = []
var _prox_parpadeo := 2.0
var _rng := RandomNumberGenerator.new()


func montar(personaje: Node, semilla := 7) -> void:
	_rng.seed = semilla
	for n in personaje.find_children("*", "AnimationPlayer", true, false):
		ap = n
	assert(ap != null, "El personaje no trae AnimationPlayer")
	ap.stop()
	var lista := ap.get_animation_list()
	# Pistas de morphs (cara) y de parpado, tomadas de cualquier clip que las tenga.
	var pistas_cara := {}
	var pistas_parpado := {}
	for nombre in lista:
		var an := ap.get_animation(nombre)
		for t in an.get_track_count():
			if an.track_get_type(t) == Animation.TYPE_BLEND_SHAPE:
				var p := an.track_get_path(t)
				pistas_cara[p] = true
				if String(p).contains("parpado"):
					pistas_parpado[p] = true
	_crear_cara_neutra(pistas_cara.keys())

	var raiz := AnimationNodeBlendTree.new()
	# Cuerpo: todos los clips con huesos del cuerpo; las *Face del GLB están vacías y se omiten.
	var sm_cuerpo := AnimationNodeStateMachine.new()
	for nombre in lista:
		if _es_cuerpo(ap.get_animation(nombre), nombre):
			_estados_cuerpo.append(nombre)
	_poblar(sm_cuerpo, _estados_cuerpo, FUNDIDO_CUERPO)
	# Cara: expresiones G*, habla, ojos V04* y la neutra.
	var sm_cara := AnimationNodeStateMachine.new()
	_estados_cara.append("neutra")
	for nombre in lista:
		if nombre.begins_with("G2") or nombre.begins_with("V04") or nombre == "Talk":
			_estados_cara.append(nombre)
	_poblar(sm_cara, _estados_cara, FUNDIDO_CARA)

	var capa := AnimationNodeBlend2.new()
	capa.filter_enabled = true
	for p in pistas_cara: capa.set_filter_path(p, true)
	var parp := AnimationNodeOneShot.new()
	parp.filter_enabled = true
	for p in pistas_parpado: parp.set_filter_path(p, true)
	parp.fadein_time = 0.03
	parp.fadeout_time = 0.05
	parp.mix_mode = AnimationNodeOneShot.MIX_MODE_BLEND
	var blink := AnimationNodeAnimation.new()
	blink.animation = "Blink"

	raiz.add_node("cuerpo", sm_cuerpo, Vector2(0, 0))
	raiz.add_node("cara", sm_cara, Vector2(0, 200))
	raiz.add_node("capa_cara", capa, Vector2(300, 0))
	raiz.add_node("blink", blink, Vector2(300, 200))
	raiz.add_node("parpadeo", parp, Vector2(600, 0))
	raiz.connect_node("capa_cara", 0, "cuerpo")
	raiz.connect_node("capa_cara", 1, "cara")
	raiz.connect_node("parpadeo", 0, "capa_cara")
	raiz.connect_node("parpadeo", 1, "blink")
	raiz.connect_node("output", 0, "parpadeo")

	tree = AnimationTree.new()
	tree.name = "BancoMovimientoTree"
	personaje.add_child(tree)
	tree.root_node = tree.get_path_to(ap.get_node(ap.root_node))
	tree.anim_player = tree.get_path_to(ap)
	tree.tree_root = raiz
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	tree.active = true
	tree.set("parameters/capa_cara/blend_amount", 1.0)
	_cuerpo = tree.get("parameters/cuerpo/playback")
	_cara = tree.get("parameters/cara/playback")
	_cuerpo.start(REPOSO if REPOSO in _estados_cuerpo else _estados_cuerpo[0])
	_cara.start("neutra")

	ojos = OjosALTH.new()
	ojos.aplicar(personaje)
	ojos.mirada = mirada


func estados_cuerpo() -> PackedStringArray: return _estados_cuerpo
func estados_cara() -> PackedStringArray: return _estados_cara


## Cambia el gesto de cuerpo (y opcionalmente la cara). Los clips sin -loop vuelven a Idle al acabar.
func gesto(cuerpo: String, cara_nombre := "") -> void:
	if cuerpo in _estados_cuerpo:
		_cuerpo.travel(cuerpo)
	else:
		push_warning("BancoMovimiento: no existe el gesto de cuerpo '%s'" % cuerpo)
	if cara_nombre != "":
		cara(cara_nombre)


func cara(nombre: String) -> void:
	if nombre == "":
		nombre = "neutra"
	if nombre == "Talk-loop":
		nombre = "Talk"
	if nombre in _estados_cara:
		_cara.travel(nombre)
	else:
		push_warning("BancoMovimiento: no existe la cara '%s'" % nombre)


func parpadear() -> void:
	tree.set("parameters/parpadeo/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)


func cuerpo_actual() -> String: return String(_cuerpo.get_current_node())
func cara_actual() -> String: return String(_cara.get_current_node())


func avanzar(dt: float) -> void:
	# Gesto de una sola vez terminado → reposo
	var actual := String(_cuerpo.get_current_node())
	if actual != "" and actual != REPOSO and ap.has_animation(actual):
		var an := ap.get_animation(actual)
		if an.loop_mode == Animation.LOOP_NONE and _cuerpo.get_current_play_position() >= an.length - FUNDIDO_CUERPO:
			_cuerpo.travel(REPOSO)
	if parpadeo_auto:
		_prox_parpadeo -= dt
		if _prox_parpadeo <= 0.0:
			parpadear()
			_prox_parpadeo = _rng.randf_range(2.0, 5.0)
	tree.advance(dt)


func _process(dt: float) -> void:
	if tree and not manual:
		avanzar(dt)


func _poblar(sm: AnimationNodeStateMachine, nombres: PackedStringArray, fundido: float) -> void:
	var i := 0
	for n in nombres:
		var nodo := AnimationNodeAnimation.new()
		nodo.animation = "banco/cara_neutra" if n == "neutra" else n
		sm.add_node(n, nodo, Vector2(200 * (i % 6), 120 * (i / 6)))
		i += 1
	for a in nombres:
		for b in nombres:
			if a == b: continue
			var tr := AnimationNodeStateMachineTransition.new()
			tr.xfade_time = fundido
			tr.switch_mode = AnimationNodeStateMachineTransition.SWITCH_MODE_IMMEDIATE
			sm.add_transition(a, b, tr)


func _es_cuerpo(an: Animation, nombre: String) -> bool:
	# G*/V04*/Talk/Blink son cara; P*/M* son poses de autor de 0.3 s (se prueban con modo=clips, no en el árbol).
	if nombre.begins_with("G2") or nombre.begins_with("V04") or nombre in ["Talk", "Blink"]:
		return false
	if nombre.ends_with("Face"):   # en Adán V22 las *Face solo traen Root sin moverse (vacías)
		return false
	if nombre.length() > 2 and nombre[0] in ["P", "M"] and nombre[1].is_valid_int():
		return false
	var huesos := 0
	for t in an.get_track_count():
		var ty := an.track_get_type(t)
		if ty == Animation.TYPE_ROTATION_3D or ty == Animation.TYPE_POSITION_3D:
			var sub := an.track_get_path(t).get_concatenated_subnames()
			if sub != "" and sub != "Root":
				huesos += 1
	return huesos > 0


func _crear_cara_neutra(pistas: Array) -> void:
	var an := Animation.new()
	an.length = 0.1
	an.loop_mode = Animation.LOOP_LINEAR
	for p in pistas:
		var t := an.add_track(Animation.TYPE_BLEND_SHAPE)
		an.track_set_path(t, p)
		an.blend_shape_track_insert_key(t, 0.0, 0.0)
	var lib := AnimationLibrary.new()
	lib.add_animation("cara_neutra", an)
	if ap.has_animation_library("banco"):
		ap.remove_animation_library("banco")
	ap.add_animation_library("banco", lib)
