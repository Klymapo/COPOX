## COPOX · ALTH-META: cambia las placas de ojo de un personaje importado por el shader de mirada.
## Uso: var ojos = OjosALTH.new(); ojos.aplicar(personaje); ojos.mirada = Vector2(0.5, 0.2)
class_name OjosALTH
extends RefCounted

const SHADER := preload("res://ojos/ojo_mirada.gdshader")
const CARPETA := "res://ojos/"

var _materiales: Array[ShaderMaterial] = []
var mirada := Vector2.ZERO:
	set(v):
		mirada = v.clamp(Vector2(-1, -1), Vector2(1, 1))
		for m in _materiales:
			m.set_shader_parameter("mirada", mirada)


func aplicar(raiz: Node) -> int:
	_materiales.clear()
	for mi in raiz.find_children("*", "MeshInstance3D", true, false):
		var malla: Mesh = (mi as MeshInstance3D).mesh
		if malla == null:
			continue
		for s in malla.get_surface_count():
			var mat := malla.surface_get_material(s)
			if mat == null:
				continue
			var lado := ""
			if mat.resource_name.ends_with("eye_BAKE_L"):
				lado = "L"
			elif mat.resource_name.ends_with("eye_BAKE_R"):
				lado = "R"
			if lado == "":
				continue
			var sm := ShaderMaterial.new()
			sm.shader = SHADER
			sm.set_shader_parameter("tex_base", load(CARPETA + "ojo_%s_base.png" % lado))
			sm.set_shader_parameter("tex_iris", load(CARPETA + "ojo_%s_iris.png" % lado))
			sm.set_shader_parameter("tex_encima", load(CARPETA + "ojo_%s_encima.png" % lado))
			sm.set_shader_parameter("mirada", mirada)
			(mi as MeshInstance3D).set_surface_override_material(s, sm)
			_materiales.append(sm)
	return _materiales.size()
