# ALTH_META — Master Measurements

All dimensions are in **millimetres**. The current calibration target is a 95 mm stylized chibi low-poly base. Values are inferred and tuned from the supplied visual references; they are not official dimensions from any commercial figure line.

## Global

| Parameter | Current target |
|---|---:|
| Total height | 95.0 |
| Base pose | T-pose |
| Coordinate system | Z up, X left/right, -Y forward |

## Head

| Parameter | Target |
|---|---:|
| Width | 40.0 |
| Height | 34.5 |
| Depth | 31.0 |
| Jaw width | 37.5 |
| Jaw depth | 29.5 |
| Head bevel | 4.3 |
| Head bevel segments | 4 |

### Current direction
The head is intentionally less extreme than the original Funko-like blockout. The skull should stay compact; hair will later recover much of the exterior silhouette volume.

## Neck

| Parameter | Target |
|---|---:|
| Width | 9.5 |
| Depth | 8.5 |
| Geometric height | 4.5 |
| Visible neck | ~1.5–2.5 |

## Torso

| Parameter | Target |
|---|---:|
| Chest width | 30.0 |
| Waist width | 25.5 |
| Hip/torso-base width | 25.5 |
| Chest depth | 18.0 |
| Waist depth | 16.8 |
| Hip depth | 17.2 |
| Torso height | 19.0 |

The torso should read as a compact tapered soft-box, not an hourglass and not a rigid rectangle.

## Pelvis

| Parameter | Target |
|---|---:|
| Width | 25.5 |
| Depth | 17.5 |
| Height | 7.5 |

The pelvis is deliberately compact and overlaps the torso/legs to avoid a visible stacked-block look.

## Arms

Current arm geometry is generated as one continuous profiled mesh per side.

| Profile | Width/height | Depth |
|---|---:|---:|
| Shoulder | 9.8 | 8.4 |
| Deltoid | 9.6 | 8.2 |
| Upper arm / biceps | 9.2 | 7.8 |
| Elbow | 8.1 | 7.1 |
| Forearm | 8.6 | 7.2 |
| Wrist | 7.1 | 6.3 |

| Length | Target |
|---|---:|
| Upper arm | 11.0 |
| Forearm | 10.0 |
| Shoulder centre X | ±15.2 |

## Hands

### Palm

| Parameter | Target |
|---|---:|
| Palm length | 6.8 |
| Wrist-side width | 6.0 |
| Finger-side width | 8.6 |
| Wrist-side depth | 3.3 |
| Finger-side depth | 3.8 |

### Fingers

| Finger | Length | Width |
|---|---:|---:|
| Thumb | 4.7 | 2.0 |
| Index | 5.1 | 1.8 |
| Middle | 5.6 | 1.9 |
| Ring | 5.1 | 1.8 |
| Pinky | 4.3 | 1.65 |

Finger depth: **1.8 mm**.

Next planned hand refinement: increase palm/finger presence slightly and change each finger from one prism to two simplified phalange segments.

## Legs

Current leg geometry is generated as one continuous profiled mesh per side.

| Profile | Width | Depth |
|---|---:|---:|
| Hip | 11.2 | 9.0 |
| Thigh | 10.7 | 8.7 |
| Knee | 9.3 | 7.8 |
| Calf | 9.5 | 8.0 |
| Ankle | 8.4 | 7.4 |

| Parameter | Target |
|---|---:|
| Leg length | 24.0 |
| Hip centre X | ±8.2 |

The knee/calf changes should remain subtle; the target is stylized anatomy, not visible realistic musculature.

## Shoes

| Parameter | Target |
|---|---:|
| Length | 16.5 |
| Width | 11.8 |
| Height | 9.0 |
| Sole height | 1.8 |
| Outward angle | 4.5° |

Next planned refinement: increase toe-box projection toward ~18 mm total shoe length while keeping most of the added volume forward of the ankle.

## Face

### Eyes

| Parameter | Target |
|---|---:|
| Eye width | 8.1 |
| Eye height | 9.5 |
| Eye extrusion depth | 1.2 |
| Corner radius | 2.2 |
| Eye centre X | ±6.1 |
| Eye centre Z | 78.5 |

### Iris

| Parameter | Target |
|---|---:|
| Width | 3.9 |
| Height | 6.5 |
| Depth | 0.75 |

### Eyebrow

| Parameter | Target |
|---|---:|
| Width | 9.2 |
| Height | 1.9 |
| Depth | 0.85 |
| Z | 84.0 |

### Nose

| Parameter | Target |
|---|---:|
| Width | 3.8 |
| Height | 2.7 |
| Projection/depth | 1.8 |
| Z | 72.8 |

### Mouth

| Parameter | Target |
|---|---:|
| Width | 7.5 |
| Line thickness | 0.42 |
| Z | 68.3 |

### Ears

| Parameter | Target |
|---|---:|
| Width | 6.0 |
| Height | 8.0 |
| Depth | 3.7 |
| Centre Z | 77.0 |

## Z layout — v0.8.3

| Region | Start Z | End Z |
|---|---:|---:|
| Shoes | 0.0 | 9.0 |
| Legs | 8.3 | 32.3 |
| Pelvis | 30.8 | 38.3 |
| Torso | 36.5 | 55.5 |
| Neck | 54.5 | 59.0 |
| Head | 60.5 | 95.0 |

Overlaps are intentional and are used to avoid visible gaps before controlled fusion.

## Planned v0.8.4 adjustments

- Reduce head depth slightly further only if profile/3-4 tests still look too cubic.
- Introduce asymmetric front/back head depth controls instead of symmetric depth around Y=0.
- Increase hand scale ~10–15%.
- Split fingers into two low-poly segments.
- Refine calf/knee silhouette without changing overall leg length.
- Extend shoe toe box primarily forward.
- Increase overlap/integration of torso and pelvis.
