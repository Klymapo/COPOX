extends SceneTree
## COPOX G2-C3 V3 · compara GLB V2 intacto contra V3 rapado local.
## Únicamente inspecciona importación real en Godot 4.7.2; no mueve huesos.

func _initialize() -> void:
    var files: Array[String] = ["res://baseline_v2.glb", "res://left_tuft_removed_v3.glb"]
    var models: Dictionary = {}
    var failed := false
    var base_animations: Array = []
    var base_surfaces: int = -1
    for path in files:
        var scene = ResourceLoader.load(path)
        if not (scene is PackedScene):
            push_error("No se importó " + path)
            failed = true
            continue
        var root: Node = scene.instantiate()
        get_root().add_child(root)
        var result := {"skeletons": [], "animations": [], "surface_count": 0,
                       "finite_bone_positions": true}
        _scan(root,result)
        var animations: Array = result["animations"]
        animations.sort()
        if result["skeletons"] != [56] or animations.size() != 29:
            push_error("Incompatibilidad 56 huesos/29 animaciones en " + path)
            failed = true
        if path == files[0]:
            base_animations=animations.duplicate()
            base_surfaces=result["surface_count"]
        elif animations != base_animations or result["surface_count"] != base_surfaces:
            push_error("Los clips o superficies cambiaron tras el rapado")
            failed = true
        if not result["finite_bone_positions"]:
            push_error("Pose de huesos no finita")
            failed = true
        models[path]=result
        root.queue_free()
    var output := {
      "status": "PASS_IMPORT_STRUCTURAL" if not failed else "FAIL_IMPORT_STRUCTURAL",
      "checks_passed": not failed,
      "engine": Engine.get_version_info(),
      "models": models,
      "limitations": ["No confirma deformacion facial funcional",
                      "No confirma watertight ni aprobacion artistica",
                      "No autoriza fusion, sustituir ni borrar originales"]
    }
    var file := FileAccess.open("res://result.json",FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(output, "  "))
        file.close()
    print("G2C3 V3 GODOT QA: ",JSON.stringify(output))
    quit(2 if failed else 0)

func _scan(node: Node, info: Dictionary) -> void:
    if node is Skeleton3D:
        var rig := node as Skeleton3D
        (info["skeletons"] as Array).append(rig.get_bone_count())
        for i in range(rig.get_bone_count()):
            if not rig.get_bone_global_pose(i).origin.is_finite():
                info["finite_bone_positions"]=false
    if node is AnimationPlayer:
        var player := node as AnimationPlayer
        for clip in player.get_animation_list():
            (info["animations"] as Array).append(str(clip))
    if node is MeshInstance3D:
        var instance := node as MeshInstance3D
        if instance.mesh:
            info["surface_count"] += instance.mesh.get_surface_count()
    for c in node.get_children():
        _scan(c,info)
