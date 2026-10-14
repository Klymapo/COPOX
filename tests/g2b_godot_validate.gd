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
            "animation_track_counts": {},
            "animation_dynamic_track_counts": {},
            "clips_without_tracks": [],
            "clips_without_variable_keys": [],
            "mesh_surfaces": 0,
            "finite_bone_poses": true,
            "scene_imported": true,
        }
        _collect(model, detail)
        var names: Array = detail["animation_names"]
        names.sort()
        detail["animation_count"] = names.size()
        detail["clips_with_tracks_count"] = names.size() - (detail["clips_without_tracks"] as Array).size()
        detail["dynamic_key_clips_count"] = names.size() - (detail["clips_without_variable_keys"] as Array).size()
        detail["track_existence_does_not_prove_functional_animation"] = true
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
        "import_tests_passed_not_animation_functionality": true,
        "facial_animation_restoration_completed": false,
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
            var clip_name: String = str(clip)
            (detail["animation_names"] as Array).append(clip_name)
            var clip_resource: Animation = player.get_animation(clip)
            var tracks: int = clip_resource.get_track_count() if clip_resource else 0
            detail["animation_track_counts"][clip_name] = tracks
            if tracks == 0:
                (detail["clips_without_tracks"] as Array).append(clip_name)
            var changing: int = 0
            if clip_resource:
                for track_index in range(tracks):
                    var keys: int = clip_resource.track_get_key_count(track_index)
                    if keys < 2:
                        continue
                    var first = clip_resource.track_get_key_value(track_index, 0)
                    var varies: bool = false
                    for key_index in range(1, keys):
                        if clip_resource.track_get_key_value(track_index, key_index) != first:
                            varies = true
                            break
                    if varies:
                        changing += 1
            detail["animation_dynamic_track_counts"][clip_name] = changing
            if changing == 0:
                (detail["clips_without_variable_keys"] as Array).append(clip_name)
    if node is MeshInstance3D:
        var mesh_instance: MeshInstance3D = node as MeshInstance3D
        if mesh_instance.mesh:
            detail["mesh_surfaces"] += mesh_instance.mesh.get_surface_count()
    for child in node.get_children():
        _collect(child, detail)
