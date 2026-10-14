extends SceneTree
## COPOX · Godot 4.7.2 headless validation of generated GLBs.
## No game project / autoloads / assets are changed.

func _initialize() -> void:
    var paths: Array[String] = [
        "res://baseline.glb",
        "res://r4_rear_focus.glb",
        "res://r5_rear_focus_soft.glb",
    ]
    var outputs: Dictionary = {}
    var baseline_animations: Array = []
    var failed: bool = false
    for path in paths:
        var resource = ResourceLoader.load(path)
        if not (resource is PackedScene):
            push_error("GLB not imported as PackedScene: " + path)
            failed = true
            continue
        var model: Node = resource.instantiate()
        get_root().add_child(model)
        var detail: Dictionary = {
            "skeletons": [],
            "animation_names": [],
            "mesh_surfaces": 0,
            "finite_bone_poses": true,
            "scene_imported": true,
        }
        _collect(model, detail)
        var names: Array = detail["animation_names"]
        names.sort()
        detail["animation_count"] = names.size()
        var bones: Array = detail["skeletons"]
        if bones.size() != 1 or bones[0] != 56:
            push_error("Skeleton not preserved: " + path + " = " + str(bones))
            failed = true
        if names.size() < 29:
            push_error("Lost GLB animations: " + path + " = " + str(names.size()))
            failed = true
        if path == paths[0]:
            baseline_animations = names.duplicate()
        elif names != baseline_animations:
            push_error("Candidate animation names differ from baseline: " + path)
            failed = true
        if detail["mesh_surfaces"] < 2:
            push_error("Unexpected number of mesh surfaces after import: " + path)
            failed = true
        if not detail["finite_bone_poses"]:
            push_error("Non-finite bone pose: " + path)
            failed = true
        outputs[path] = detail
        model.queue_free()
    var result: Dictionary = {
        "engine": Engine.get_version_info(),
        "baseline": paths[0],
        "candidate_count": paths.size() - 1,
        "all_checks_passed": not failed,
        "models": outputs,
        "limitations": [
            "Import and skeleton/clip checks only, not artistic validation",
            "Not all intermediate animation frames simulated",
            "Not a physics/cloth/collision test",
            "Face mesh remains separate from reconstructed shell",
        ],
    }
    var file := FileAccess.open("res://godot_result.json", FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(result, "  "))
        file.close()
    print("[COPOX G2B GODOT] ", JSON.stringify(result))
    quit(2 if failed else 0)


func _collect(node: Node, detail: Dictionary) -> void:
    if node is Skeleton3D:
        var skeleton: Skeleton3D = node as Skeleton3D
        (detail["skeletons"] as Array).append(skeleton.get_bone_count())
        for i in range(skeleton.get_bone_count()):
            var t: Transform3D = skeleton.get_bone_global_pose(i)
            if not t.origin.is_finite():
                detail["finite_bone_poses"] = false
    if node is AnimationPlayer:
        var player: AnimationPlayer = node as AnimationPlayer
        for clip in player.get_animation_list():
            (detail["animation_names"] as Array).append(str(clip))
    if node is MeshInstance3D:
        var mesh_instance: MeshInstance3D = node as MeshInstance3D
        if mesh_instance.mesh:
            detail["mesh_surfaces"] += mesh_instance.mesh.get_surface_count()
    for child in node.get_children():
        _collect(child, detail)
