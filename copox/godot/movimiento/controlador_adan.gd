## COPOX · controlador de movimiento para Adán (y derivados con su rig).
## Usa BancoMovimiento (cuerpo + cara + parpadeo + mirada) y mueve el nodo del personaje sin física,
## a las velocidades medidas de los clips (pies sin patinar):
##   caminar 0.259 u/s · correr 0.834 u/s (Adán mide 0.848 u; escala el nodo y las velocidades escalan igual).
## En el juego: llama mover(direccion, corriendo) cada cuadro desde tu input; saltar(), dash(), golpe("R"/"L"),
## senalar(), equipar(ruta_glb) y desequipar(). Si tu personaje usa CharacterBody3D, toma `velocidad_deseada`
## y pásala a velocity antes de move_and_slide() en lugar de dejar que este nodo mueva la posición.
class_name ControladorAdan
extends Node

const VEL_CAMINAR := 0.259
const VEL_CORRER := 0.834
const DASH_DIST := 0.42          ## u recorridas en el dash
const DASH_T := 0.55
const SALTO_AVANCE := 0.6        ## fracción de la velocidad que se conserva en el aire

var personaje: Node3D
var banco: BancoMovimiento
var mueve_nodo := true
var velocidad_deseada := Vector3.ZERO
var escala := 1.0

var _estado := "Idle"
var _t_accion := 0.0
var _accion := ""
var _dir := Vector3.ZERO
var _corriendo := false
var _arma: Node3D
var _sk: Skeleton3D


func montar(p: Node3D, b: BancoMovimiento) -> void:
	personaje = p
	banco = b
	escala = p.scale.x
	for n in p.find_children("*", "Skeleton3D", true, false):
		_sk = n
	_montar_manos()


# --- manos intercambiables (V40+): mallas MANO_<ESTADO>_<L|R>; el nodo MANOS dice qué mano lleva cada clip -------
var _manos := {}                  ## "L"/"R" -> {estado: MeshInstance3D}
var _mapa_manos := {}             ## extras de MANOS: variantes, defecto, por_clip
var _forzada := {}                ## "L"/"R" -> estado forzado ("" = según el clip)


func _montar_manos() -> void:
	_manos = {"L": {}, "R": {}}
	for m in personaje.find_children("MANO_*", "MeshInstance3D", true, false):
		var partes := String(m.name).split("_")           # MANO, ESTADO, L|R
		if partes.size() == 3 and partes[2] in _manos:
			_manos[partes[2]][partes[1].to_lower()] = m
	var nodo := personaje.find_child("MANOS", true, false)
	_mapa_manos = nodo.get_meta("extras", {}) if nodo else {}
	_forzada = {"L": "", "R": ""}
	_actualizar_manos()


## Fija la mano de un lado ("L"/"R") a un estado ("abierta", "puno", "senalar", …). "" vuelve a la del clip.
func forzar_mano(lado: String, estado: String) -> void:
	_forzada[lado] = estado
	_actualizar_manos()


func mano_actual(lado: String) -> String:
	for e in _manos.get(lado, {}):
		if _manos[lado][e].visible:
			return e
	return ""


func _estado_mano(lado: String) -> String:
	if _forzada.get(lado, "") != "":
		return _forzada[lado]
	var defecto: String = _mapa_manos.get("defecto", "abierta")
	var clip := banco.cuerpo_actual() if banco else ""
	var tramos: Array = _mapa_manos.get("por_clip", {}).get(clip, {}).get(lado, [])
	if tramos.is_empty():
		return defecto
	var t := banco.posicion_cuerpo()
	var e: String = tramos[0][1]
	for tr in tramos:
		if t >= float(tr[0]):
			e = tr[1]
	return e


func _actualizar_manos() -> void:
	for lado in _manos:
		if _manos[lado].is_empty():
			continue
		var e := _estado_mano(lado)
		if not e in _manos[lado]:
			e = _mapa_manos.get("defecto", "abierta")
		for k in _manos[lado]:
			_manos[lado][k].visible = (k == e)


func mover(direccion: Vector3, corriendo := false) -> void:
	_dir = Vector3(direccion.x, 0, direccion.z)
	if _dir.length() > 1.0:
		_dir = _dir.normalized()
	_corriendo = corriendo


func saltar() -> void:
	_accion = "Jump"; _t_accion = 1.0
	banco.gesto("Jump")


func dash() -> void:
	_accion = "Dash"; _t_accion = DASH_T
	banco.gesto("Dash")


func golpe(lado := "R") -> void:
	_accion = "Punch_" + lado; _t_accion = 0.6
	banco.gesto(_accion)


func senalar() -> void:
	_accion = "PointFwd"; _t_accion = 1.6
	banco.gesto("PointFwd")


## Apuntar con el arma (bucle). Se sale al moverse o con otra acción.
func apuntar() -> void:
	_accion = "Aim"; _t_accion = INF
	banco.gesto("Aim")


var _socket: Node3D
var _accion_mano := {}


## Arma con nodo AGARRE (ver copox/armas/armas_alth.py). Se pega a la mano derecha.
## Si el personaje trae el nodo AGARRE_<NOMBRE> (resuelto por copox/movimiento/agarre.py: dedos rodeando el mango,
## índice en el gatillo), el arma va exactamente ahí y la mano toma la pose de ese agarre. Si no, marco aproximado.
func equipar(ruta: String, nombre_agarre := "") -> void:
	desequipar()
	var escena: PackedScene = load(ruta)
	_arma = escena.instantiate()
	if nombre_agarre != "":
		_socket = personaje.find_child("AGARRE_" + nombre_agarre.to_upper(), true, false)
		if _socket:
			_socket.add_child(_arma)
			_arma.transform = Transform3D.IDENTITY
			_accion_mano = _socket.get_meta("extras", {})
			banco.mano_derecha(_accion_mano.get("clip_agarre", ""))
			return
		push_warning("ControladorAdan: el personaje no trae AGARRE_%s; uso el marco aproximado" % nombre_agarre.to_upper())
	var agarre: Node3D = _arma.find_child("AGARRE", true, false)
	var ba := BoneAttachment3D.new()
	ba.bone_name = "RightHand"
	_sk.add_child(ba)
	# marco de agarre en la pose de reposo del esqueleto (constante respecto al hueso de la mano)
	var g := func(n): return _sk.get_bone_global_rest(_sk.find_bone(n)).origin
	var W: Vector3 = g.call("RightHand"); var Ip: Vector3 = g.call("RightIndexProximal")
	var Lp: Vector3 = g.call("RightLittleProximal"); var Fa: Vector3 = g.call("RightLowerArm")
	var y := (Ip - Lp).normalized()
	var x := (W - Fa); x = (x - y * x.dot(y)).normalized()
	var z := x.cross(y).normalized()
	var palma := W.lerp((Ip + Lp) * 0.5, 0.75)
	var G := Transform3D(Basis(x, y, z), palma + (x * 0.012) - (z * 0.008))
	var mano := _sk.get_bone_global_rest(_sk.find_bone("RightHand"))
	ba.add_child(_arma)
	_arma.transform = mano.affine_inverse() * G * agarre.transform.affine_inverse()


func desequipar() -> void:
	if _arma:
		if _socket and _arma.get_parent() == _socket:
			_arma.queue_free()
		else:
			_arma.get_parent().queue_free()
		_arma = null
	_socket = null
	_accion_mano = {}
	if banco: banco.mano_derecha("")


## Acción del arma equipada con agarre (p. ej. apretar el gatillo): la mano hace su clip *_Accion y la pieza móvil
## (GATILLO) sigue la misma curva de tiempos/ángulos que se resolvió junto con el dedo.
func disparar() -> void:
	if _accion_mano.is_empty() or _arma == null:
		return
	banco.mano_accion(_accion_mano.get("clip_accion", ""))
	_pieza_accion = _arma.find_child(_accion_mano.get("accion_nodo", "GATILLO"), true, false)
	_t_accion_mano = 0.0


var _pieza_accion: Node3D
var _t_accion_mano := -1.0


## Avanza la pieza móvil del arma con la curva de la acción (mismo reloj que el banco: sin tweens, reproducible).
func _avanzar_accion_mano(dt: float) -> void:
	if _t_accion_mano < 0.0 or _pieza_accion == null:
		return
	_t_accion_mano += dt
	var ts: Array = _accion_mano.get("accion_tiempos", [])
	var angs: Array = _accion_mano.get("accion_angulos", [])
	var ang := 0.0
	if _t_accion_mano >= float(ts[-1]):
		_t_accion_mano = -1.0
	else:
		for i in range(1, ts.size()):
			if _t_accion_mano <= float(ts[i]):
				var u := (_t_accion_mano - float(ts[i - 1])) / maxf(float(ts[i]) - float(ts[i - 1]), 1e-6)
				ang = lerpf(float(angs[i - 1]), float(angs[i]), u)
				break
	_pieza_accion.rotation.z = -ang


func avanzar(dt: float) -> void:
	var vel := Vector3.ZERO
	if _accion != "":
		_t_accion -= dt
		var adelante := personaje.global_transform.basis.z      # el modelo mira hacia +z
		match _accion:
			"Dash":
				var u := clampf(1.0 - _t_accion / DASH_T, 0, 1)
				vel = adelante * DASH_DIST * escala * 2.0 * (1.0 - u) / DASH_T   # se frena al final
			"Jump":
				vel = _dir * (VEL_CORRER if _corriendo else VEL_CAMINAR) * escala * SALTO_AVANCE
		if _accion == "Aim" and _dir.length() > 0.05:
			_t_accion = 0.0
		if _t_accion <= 0.0:
			_accion = ""
			_estado = ""
	if _accion == "":
		var obj := "Idle"
		var v := 0.0
		if _dir.length() > 0.05:
			obj = "Run" if _corriendo else "Walk"
			v = VEL_CORRER if _corriendo else VEL_CAMINAR
			_girar_hacia(_dir, dt)
		vel = personaje.global_transform.basis.z * v * escala
		if obj != _estado:
			_estado = obj
			banco.gesto(obj)
	velocidad_deseada = vel
	if mueve_nodo:
		personaje.global_position += vel * dt
	banco.avanzar(dt)
	_avanzar_accion_mano(dt)
	_actualizar_manos()


func _girar_hacia(d: Vector3, dt: float) -> void:
	var actual := personaje.global_transform.basis.z
	var ang := atan2(d.x, d.z)
	var ang0 := atan2(actual.x, actual.z)
	var diff := wrapf(ang - ang0, -PI, PI)
	personaje.rotate_y(clampf(diff, -8.0 * dt, 8.0 * dt))
