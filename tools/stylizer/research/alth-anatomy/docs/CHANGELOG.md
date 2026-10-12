# ALTH_META — Development History

## v0.5.3 — Funko-like Soft Box

Initial blockout family used as the starting point for the project.

Key characteristics:
- 95 mm nominal target, but actual Z layout extended beyond it.
- Large 55 × 43 × 48 mm head.
- Cylindrical arms and legs.
- Separate shoulder, elbow, hip and ankle spheres.
- 12-segment bevels and heavily rounded forms.
- Short arms and legs.

Problems discovered:
- `altura_total` and the actual top Z did not agree.
- Declared leg length and generated leg length differed.
- Feet did not actually reach Z=0.
- Several dimensions were duplicated as both measurements and layout coordinates, allowing contradictions.

## v0.6.0 — Dimensional consistency

Purpose: turn the blockout into a mathematically coherent parametric model.

Changes:
- Height fixed to a real 95 mm.
- Feet anchored at Z=0.
- Leg lengths derived consistently.
- Reduced duplicate sources of truth.
- Hombers derived from torso width instead of fully arbitrary coordinates.
- Reduced excessive bevel values.

## v0.7.x — First attempts at geometry fusion

Experimented with:
- joining body components,
- voxel remesh,
- Laplacian smoothing.

Result:
- head looked promising,
- arms became sausage-like,
- ankles/shoes became too soft,
- global smoothing damaged hard low-poly language.

Decision:
Do not globally remesh the entire character. Preserve hard forms and eventually fuse by region only.

## v0.8.0 — New stylized target base

Major redesign. The project stopped treating the target as a conventional Funko and moved toward a reusable stylized chibi low-poly body.

Key changes:
- compact head,
- longer legs,
- tapered prism limbs instead of cylinders,
- separate fingers,
- larger shoes,
- anime-influenced facial placement,
- T-pose as the calibration pose.

Initial target values included roughly:
- head 40 × 36 × 33 mm,
- chest 25 mm,
- leg ~27 mm,
- shoe ~15 mm.

## v0.8.1 — Calibration Pass

Visual testing showed the first stylized base was too thin and mannequin-like.

Changes:
- torso widened,
- arms and forearms thickened,
- palms/fingers enlarged,
- legs thickened,
- shoes widened,
- joint overlaps increased,
- eyes made less rectangular.

## v0.8.2 — Silhouette Calibration

Main findings from front, three-quarter, side and low-angle tests:
- head still too deep,
- visible neck too long,
- torso too hourglass-shaped,
- hands still too small,
- legs still column-like.

Changes:
- head depth reduced,
- neck mostly buried,
- torso straightened,
- legs thickened and shortened,
- palms enlarged,
- eye whites rebuilt as genuinely rounded extruded shapes,
- irises rebuilt as ellipses.

## v0.8.3 — Stylized Anatomy

Current retained baseline.

Major architectural change:
- each arm is generated as **one continuous profiled mesh** from shoulder to wrist,
- each leg is generated as **one continuous profiled mesh** from hip to ankle.

Arm profile:
- shoulder,
- deltoid,
- upper arm,
- elbow,
- forearm,
- wrist.

Leg profile:
- hip,
- thigh,
- knee,
- calf,
- ankle.

Current major targets:
- Head: 40 × 31 × 34.5 mm
- Chest: 30 mm
- Waist: 25.5 mm
- Leg length: 24 mm
- Palm: 6.8 mm long, 6.0 → 8.6 mm wide
- Shoe: 16.5 × 11.8 × 9 mm

## v0.8.4a — Silhouette Refinement A — candidate

Small reviewable step. **v0.8.3 remains the retained baseline until this candidate is visually approved.**

Changes under test:
- head now has independent front/back Y control instead of symmetric depth,
- lower face/jaw narrowed to 36.5 mm,
- face plane kept comparatively flat while more skull volume is carried backward,
- pelvis height reduced from 7.5 to 6.2 mm and overlapped more strongly with torso,
- torso side profile made more continuous,
- palm enlarged from 6.8 to 7.5 mm long and 8.6 to 9.4 mm at the finger base,
- fingers enlarged slightly for stronger silhouette,
- leg length unchanged at 24 mm but knee/calf/ankle widths refined,
- shoe length increased from 16.5 to 18 mm, with most extra length directed toward the toe,
- ears slightly enlarged,
- eye width increased slightly to 8.5 mm.

Not included yet:
- two-segment fingers,
- geometry fusion,
- hair,
- clothing,
- rigging.

## v0.8.4b — next candidate

Only after v0.8.4a visual review. Likely focus:
- two-segment fingers,
- more natural palm/thumb silhouette,
- minor head/torso corrections from front and 3/4 captures.

## v0.9 — Planned Regional Fusion

Planned controlled fusion:
- torso + pelvis,
- each complete arm,
- each complete leg,
- palm + fingers.

Avoid full-body global voxel smoothing.

## v0.10 — Planned Character Language

- first reusable hair masses,
- refined face geometry,
- eyebrow/eye expression system,
- cleaner ears/nose/mouth treatment.

## v1.0 — Planned Stable Base

Goal:
- stable reusable body,
- consistent measurements,
- clean regional topology,
- ready for rigging,
- ready for character-specific clothing, hair and props.
