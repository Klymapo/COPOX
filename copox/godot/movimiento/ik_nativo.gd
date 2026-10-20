## COPOX · ALTH-META: IK nativo de Godot 4.6+ (TwoBoneIK3D / LookAtModifier3D) sobre el rig de Adán (20 oct 2026).
## Ruta AAA §6.1: pies anclados al piso, manos a objetos y cabeza que sigue un objetivo, sin IK escrito a mano.
##
## Uso:
##   var ik := IKNativoALTH.new()
##   personaje.add_child(ik)
##   ik.montar(personaje)                  # raíz del GLB importado (busca su Skeleton3D)
##   ik.piso = 0.0                         # altura del suelo (mundo); los pies no bajan de aquí
##   ik.mirar_a(Vector3(0, 0.6, 1))        # la cabeza sigue un punto (con límites de ángulo)
##   ik.mano("L", objeto.global_position)  # mano izquierda a un objeto (influencia 1); ik.soltar_mano("L")
## Los objetivos son Marker3D hijos de la raíz (Meta_PieL/R, Meta_ManoL/R, Meta_Mirada): se pueden animar.
class_name IKNativoALTH
extends Node

const HUESOS := {
	"PieL": ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot"], "PieR": ["RightUpperLeg", "RightLowerLeg", "RightFoot"],
	"ManoL": ["LeftUpperArm", "LeftLowerArm", "LeftHand"], "ManoR": ["RightUpperArm", "RightLowerArm", "RightHand"],
}

var skel: Skeleton3D
var raiz: Node3D
var piernas: TwoBoneIK3D
var brazos: TwoBoneIK3D
var cabeza: LookAtModifier3D
var metas := {}
var piso := 0.0                 ## altura del suelo en mundo
var tobillo := 0.03             ## alto del tobillo sobre la suela (u de Adán)
var anclar_pies := true
var _manos_activas := {"L": false, "R": false}


func montar(nodo: Node3D) -> bool:
	raiz = nodo
	skel = _buscar_esqueleto(nodo)
	if skel == null:
		push_error("IKNativoALTH: no hay Skeleton3D bajo " + str(nodo.name))
		return false
	for k in HUESOS:
		var m := Marker3D.new()
		m.name = "Meta_" + k
		raiz.add_child(m)
		metas[k] = m
	var mir := Marker3D.new(); mir.name = "Meta_Mirada"; raiz.add_child(mir); metas["Mirada"] = mir
	mir.position = Vector3(0, 0.6, 1.0)
	piernas = _dos_huesos("IK_Piernas", ["PieL", "PieR"])
	brazos = _dos_huesos("IK_Brazos", ["ManoL", "ManoR"])
	brazos.influence = 0.0
	cabeza = LookAtModifier3D.new()
	cabeza.name = "IK_Cabeza"
	cabeza.bone_name = "Head"
	cabeza.forward_axis = SkeletonModifier3D.BONE_AXIS_PLUS_Z if "BONE_AXIS_PLUS_Z" in SkeletonModifier3D else 4
	cabeza.use_angle_limitation = true
	cabeza.primary_limit_angle = deg_to_rad(70.0)
	cabeza.secondary_limit_angle = deg_to_rad(35.0)
	cabeza.duration = 0.25
	skel.add_child(cabeza)
	cabeza.target_node = cabeza.get_path_to(mir)
	_reubicar_metas()
	return true


func _dos_huesos(nombre: String, claves: Array) -> TwoBoneIK3D:
	var ik := TwoBoneIK3D.new()
	ik.name = nombre
	skel.add_child(ik)
	ik.setting_count = claves.size()
	for i in claves.size():
		var h: Array = HUESOS[claves[i]]
		ik.set_root_bone_name(i, h[0])
		ik.set_middle_bone_name(i, h[1])
		ik.set_end_bone_name(i, h[2])
		ik.set_target_node(i, ik.get_path_to(metas[claves[i]]))
		# polo (dónde dobla): rodillas al frente (+Z), codos atrás (−Z). Sin polo, una pierna/brazo recto (T-pose)
		# no tiene plano de flexión y el solver no se mueve.
		var polo := Marker3D.new()
		polo.name = "Polo_" + claves[i]
		raiz.add_child(polo)
		var medio := _pos_hueso(h[1])
		polo.global_position = medio + (Vector3(0, 0, 0.3) if claves[i].begins_with("Pie") else Vector3(0, -0.05, -0.3))
		metas["Polo_" + claves[i]] = polo
		ik.set_pole_node(i, ik.get_path_to(polo))
	return ik


func _buscar_esqueleto(n: Node) -> Skeleton3D:
	if n is Skeleton3D:
		return n
	for c in n.get_children():
		var s := _buscar_esqueleto(c)
		if s:
			return s
	return null


func _pos_hueso(nombre: String) -> Vector3:
	var i := skel.find_bone(nombre)
	return skel.global_transform * skel.get_bone_global_pose(i).origin if i >= 0 else Vector3.ZERO


func _reubicar_metas() -> void:
	for k in ["PieL", "PieR"]:
		metas[k].global_position = _pos_hueso(HUESOS[k][2])
	for k in ["ManoL", "ManoR"]:
		if not _manos_activas[k.substr(4)]:
			metas[k].global_position = _pos_hueso(HUESOS[k][2])


## Pies: siguen la animación pero nunca bajan del piso (contacto limpio en escaleras, rampas y aterrizajes).
func _process(_dt: float) -> void:
	if skel == null:
		return
	if anclar_pies:
		for k in ["PieL", "PieR"]:
			var p := _pos_hueso(HUESOS[k][2])
			p.y = maxf(p.y, piso + tobillo)
			metas[k].global_position = p


func mirar_a(punto: Vector3) -> void:
	metas["Mirada"].global_position = punto


func mano(lado: String, punto: Vector3) -> void:
	_manos_activas[lado] = true
	metas["Mano" + lado].global_position = punto
	brazos.influence = 1.0


func soltar_mano(lado: String) -> void:
	_manos_activas[lado] = false
	if not _manos_activas["L"] and not _manos_activas["R"]:
		brazos.influence = 0.0
