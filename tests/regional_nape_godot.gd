extends SceneTree
## COPOX · validar un cassette regional, sin abrir ni modificar AlasTheo.
func _initialize() -> void:
    var paths: Array[String] = ["res://baseline.glb", "res://nuca.glb"]
    var models: Dictionary = {}
    var reference_clips: Array = []
    var reference_surfaces: int = -1
    var failed := false
    for path in paths:
        var packed = ResourceLoader.load(path)
        if not (packed is PackedScene):
            push_error("No se pudo importar " + path)
            failed = true
            continue
        var root: Node = packed.instantiate()
        get_root().add_child(root)
        var d: Dictionary = {"skeletons":[],"animations":[],"surface_count":0,
                             "finite_bone_positions":true}
        _scan(root,d)
        var clip_names: Array = d["animations"]
        clip_names.sort()
        if d["skeletons"] != [56] or clip_names.size() != 29:
            push_error("Variación del rig o nombres de clips en " + path)
            failed = true
        if path == paths[0]:
            reference_clips = clip_names.duplicate()
            reference_surfaces = d["surface_count"]
        elif clip_names != reference_clips or d["surface_count"] != reference_surfaces:
            push_error("Diferencias de clips o superficies entre baseline y nuca")
            failed = true
        if not d["finite_bone_positions"]:
            failed = true
        models[path] = d
        root.queue_free()
    var output := {
        "engine": Engine.get_version_info(),
        "status": "PASS_IMPORT_STRUCTURAL" if not failed else "FAIL_IMPORT_STRUCTURAL",
        "checks_passed": not failed,
        "models": models,
        "scope": "nuca",
        "limitations": [
            "Importación no garantiza animación facial funcional",
            "No prueba auto-intersecciones ni unión con Cara",
            "Sin evaluación artística de nuca",
            "No autoriza sustitución de modelo ni fusión"
        ]
    }
    var file := FileAccess.open("res://result.json",FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(output,"  "))
        file.close()
    print("COPOX REGIONAL GODOT: ",JSON.stringify(output))
    quit(2 if failed else 0)


func _scan(node: Node, info: Dictionary) -> void:
    if node is Skeleton3D:
        var rig := node as Skeleton3D
        (info["skeletons"] as Array).append(rig.get_bone_count())
        for i in range(rig.get_bone_count()):
            if not rig.get_bone_global_pose(i).origin.is_finite():
                info["finite_bone_positions"]=false
    if node is AnimationPlayer:
        var animation_player := node as AnimationPlayer
        for clip in animation_player.get_animation_list():
            (info["animations"] as Array).append(str(clip))
    if node is MeshInstance3D:
        var inst := node as MeshInstance3D
        if inst.mesh:
            info["surface_count"] += inst.mesh.get_surface_count()
    for child in node.get_children():
        _scan(child,info)
