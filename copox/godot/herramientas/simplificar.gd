## COPOX · simplifica una malla con meshoptimizer (el mismo que usa Godot para los LOD).
## godot --headless --path copox/godot --script res://herramientas/simplificar.gd -- entrada.json salida.json
## entrada: {"V": [[x,y,z]...], "T": [[a,b,c]...], "meta": tris}; salida: {"V": [...], "T": [...], "tris": n}
extends SceneTree

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var V := PackedVector3Array()
	for p in d["V"]:
		V.append(Vector3(p[0], p[1], p[2]))
	var I := PackedInt32Array()
	for t in d["T"]:
		I.append(int(t[0])); I.append(int(t[1])); I.append(int(t[2]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = V
	arr[Mesh.ARRAY_INDEX] = I
	var st := SurfaceTool.new()
	st.create_from_arrays(arr)
	st.generate_normals()
	var arr2 := st.commit_to_arrays()
	var im := ImporterMesh.new()
	im.add_surface(Mesh.PRIMITIVE_TRIANGLES, arr2)
	im.generate_lods(25.0, 60.0, [])
	var meta := int(d["meta"])
	var mejor: PackedInt32Array = arr2[Mesh.ARRAY_INDEX]
	var dif: int = absi(mejor.size() / 3 - meta)
	for k in im.get_surface_lod_count(0):
		var idx: PackedInt32Array = im.get_surface_lod_indices(0, k)
		var n: int = idx.size() / 3
		print("LOD ", k, " tris ", n)
		if absi(n - meta) < dif:
			dif = absi(n - meta); mejor = idx
	var Vs: PackedVector3Array = im.get_surface_arrays(0)[Mesh.ARRAY_VERTEX]
	var outV := []
	for p in Vs:
		outV.append([p.x, p.y, p.z])
	var outT := []
	for i in range(0, mejor.size(), 3):
		outT.append([mejor[i], mejor[i + 1], mejor[i + 2]])
	var f := FileAccess.open(args[1], FileAccess.WRITE)
	f.store_string(JSON.stringify({"V": outV, "T": outT, "tris": outT.size()}))
	f.close()
	quit()
