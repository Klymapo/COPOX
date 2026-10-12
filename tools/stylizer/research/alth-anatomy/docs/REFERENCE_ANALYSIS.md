# Visual Reference Analysis

This document records what is being extracted from the supplied visual references. The references are used to infer **style language and proportions**, not to reproduce any specific character.

## Overall style target

The target is not a conventional Funko silhouette. It is closer to a **stylized chibi low-poly / soft-box character system** with:

- a large but less extreme head,
- a compact torso,
- longer, shaped legs,
- solid shoes,
- tapered prism arms rather than tubes,
- large readable hands,
- simplified anime-influenced eyes,
- small block nose,
- restrained mouth geometry,
- hair built from layered faceted masses,
- visible planar structure rather than globally smooth surfaces.

## Key proportional observations

### Head
- Large relative to the body, but significantly smaller than the first Funko-like base.
- Face remains broad and relatively flat.
- Lower face/jaw should be slightly narrower than the upper head.
- Front/back depth should eventually be controlled independently; the face should not sit at the centre of a perfectly symmetric cube.
- Hair is expected to recover exterior width/depth/height beyond the skull.

### Torso
- Compact.
- Shoulders/chest are visually more substantial than the earliest blockouts.
- Waist taper is present but restrained.
- Torso and pelvis should eventually read as one continuous silhouette, not stacked rounded boxes.

### Arms
- Stylized but anatomically directional.
- Upper arm and forearm have changing cross-sections.
- Shoulder transition is important and should not look like a separate ball joint.
- T-pose is used only for calibration/rigging preparation; final characters can use expressive poses.

### Hands
The hand references are especially important.

Observed language:
- palm is broad and comparatively flat,
- wrist is narrower than the finger-side palm,
- fingers are short-to-medium rectangular low-poly forms,
- middle finger longest,
- index/ring similar,
- pinky clearly shorter,
- thumb is short, thick and strongly angled,
- hand is large enough to remain legible from full-character distance.

Planned refinement:
- two simplified segments per finger rather than a single bar,
- slightly larger palm and fingers than v0.8.3.

### Legs
- Legs are longer than Funko proportions, but still chibi.
- Silhouette is not a straight column.
- Thigh, subtle knee, calf and ankle volumes should be readable without realistic musculature.
- Overall v0.8.3 length is close; future work should emphasize shape more than length.

### Shoes
- Major visual anchor of the style.
- Broad and solid.
- Low-to-moderate height.
- Pronounced rectangular toe box.
- Visible sole.
- Current direction is to extend the toe box primarily forward rather than increasing overall height.

## Facial language

### Eyes
- Large but not classic Funko black circles.
- Visible white/sclera.
- Dark iris/pupil form.
- Rounded rectangular/organic outer silhouette.
- Eyebrows are separate and highly important to expression.

### Nose
- Small extruded block/wedge.
- Low projection.

### Mouth
- Small relative to face.
- Simple curved line or compact opening.
- Should not dominate the facial design.

### Ears
- Simplified rounded blocks.
- Clearly visible, proportionally larger than realistic ears.

## Surface language

The reference family mixes soft-box volume with deliberate faceting.

Therefore:
- avoid high-segment smoothing everywhere,
- retain readable planes,
- use modest bevel segment counts,
- do not globally apply heavy voxel remesh/smoothing,
- preserve sharper shoe, clothing and hair planes,
- smooth transitions selectively at shoulders, hips, wrists and ankles.

## Modeling strategy derived from references

1. Lock global silhouette first.
2. Keep measurements parametric.
3. Use continuous profile meshes for limbs.
4. Increase hand readability.
5. Refine head front/back profile.
6. Fuse geometry by region, not entire-body global remesh.
7. Add hair as layered faceted masses.
8. Add clothing as controlled geometry over the stable base.
9. Rig only after the base silhouette is stable.

## Confidence / limitation

The reference-derived dimensions are estimates from images, not measurements from an original 3D model. Front/side/three-quarter and hand reference views improve consistency significantly, but hidden geometry and exact depth cannot be recovered perfectly from images alone. The workflow therefore uses repeated render/view calibration rather than treating the first inferred values as ground truth.
