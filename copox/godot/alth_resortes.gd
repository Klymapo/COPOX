class_name AlthResortes
## Pelo (y otras piezas) con resortes: lee la metadata "extras" → "resortes" que dejan las recetas en el GLB
## (copox/medicion/pelo_huesos.py) y arma un SpringBoneSimulator3D (Godot 4.4+) por pieza, con una esfera de
## colisión en la cabeza para que los mechones no atraviesen el cráneo. Uso en el juego:
##     AlthResortes.aplicar(personaje)      # después de instanciar el GLB
## Ojo (medido): un SpringBoneSimulator3D creado antes del primer cuadro del árbol no simula; llamar con el árbol ya
## corriendo. CHXP V2 lo usa igual, con --fixed-fps 60 (delta fijo) para que los GIF sean deterministas.
## (El modo MANUAL + Skeleton3D.advance() no corre este modificador en 4.7: no usarlo.)

static func aplicar(escena: Node, manual := false) -> Array:
	var sims := []
	for n in escena.find_children("*", "Node3D", true, false):
		if not n.has_meta("extras"):
			continue
		var ex = n.get_meta("extras")
		if typeof(ex) != TYPE_DICTIONARY or not ex.has("resortes"):
			continue
		var cfg: Dictionary = ex["resortes"]
		var sk := _esqueleto(n)
		if sk == null:
			push_warning("AlthResortes: sin Skeleton3D para " + n.name)
			continue
		var sim := SpringBoneSimulator3D.new()
		sim.name = "Resortes_" + String(n.name)
		sk.add_child(sim)                                      # primero dentro del esqueleto: así resuelve los nombres
		var cadenas: Array = cfg["cadenas"]
		sim.setting_count = cadenas.size()
		for i in cadenas.size():
			var c: Array = cadenas[i]
			sim.set_root_bone_name(i, c[0])
			sim.set_end_bone_name(i, c[c.size() - 1])
			sim.set_stiffness(i, float(cfg.get("rigidez", 4.0)))
			sim.set_drag(i, float(cfg.get("arrastre", 0.6)))
			sim.set_gravity(i, float(cfg.get("gravedad", 0.1)))
			sim.set_gravity_direction(i, Vector3.DOWN)
			sim.set_radius(i, float(cfg.get("radio", 0.006)))
		if cfg.has("colision"):
			var col: Dictionary = cfg["colision"]
			var esf := SpringBoneCollisionSphere3D.new()
			esf.bone_name = col.get("hueso", "Head")
			var c3: Array = col["centro"]
			esf.position_offset = Vector3(c3[0], c3[1], c3[2])
			esf.radius = float(col["radio"])
			sim.add_child(esf)
		if manual:
			sk.modifier_callback_mode_process = Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_MANUAL
		sims.append(sim)
	return sims


static func _esqueleto(n: Node) -> Skeleton3D:
	if n is MeshInstance3D and (n as MeshInstance3D).skeleton != NodePath():
		var s = (n as MeshInstance3D).get_node_or_null((n as MeshInstance3D).skeleton)
		if s is Skeleton3D:
			return s
	var x := n.get_parent()
	while x != null:
		if x is Skeleton3D:
			return x
		x = x.get_parent()
	return null
