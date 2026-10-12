# ALTH_META — Modeling Standard v1 (candidate)

This document freezes the dimensions that are sufficiently converged to start modeling characters on a shared 95 mm base. It also marks the areas that are **not** yet ready for final topology.

Source of measurements: current `scripts/alth_meta_v0_8_4b.py` and the iterative visual calibration performed against the supplied character references. No extra dimensions are introduced here.

## Status legend

- **GREEN / locked**: safe to use as the shared modeling baseline now.
- **YELLOW / candidate**: use for blockout, but do not close final topology around it yet.
- **RED / open**: needs another design/topology pass before freezing.

## Conclusion

There is enough information to start modeling characters now.

What is **not** yet final is mostly topology and transition geometry, not the macro proportions.

## Global

| Parameter | Value | Status |
|---|---:|---|
| Total height | 95.0 mm | GREEN |

## Head

| Parameter | Value | Status |
|---|---:|---|
| Width | 40.0 mm | GREEN |
| Height | 34.5 mm | GREEN |
| Nominal depth | 29.8 mm | YELLOW |
| Jaw width | 36.2 mm | GREEN |
| Jaw depth | 28.8 mm | GREEN |
| Eye-level front plane | Y -14.65 mm | YELLOW |
| Eye-level rear plane | Y +15.15 mm | YELLOW |

The head width/height/jaw proportions can be frozen for modeling. The exact rear skull/nape contour should remain editable until the head/neck transition is finalized.

## Face

| Element | Value | Status |
|---|---:|---|
| Eye | 8.4 W × 9.7 H × 1.2 D mm | GREEN |
| Eye centers | X ±6.15 mm; Z 78.5 mm | GREEN |
| Eye edge-to-edge separation | 3.9 mm | GREEN |
| Iris | 3.9 W × 6.5 H × 0.75 D mm | GREEN |
| Brow | 9.2 W × 1.9 H × 0.85 D mm | GREEN |
| Nose | 3.8 W × 2.7 H × 1.8 D mm | GREEN |
| Mouth | 7.5 mm wide; 0.42 mm stroke | YELLOW |
| Ear | 6.5 W × 8.4 H × 3.8 D mm | YELLOW |

## Torso

| Parameter | Value | Status |
|---|---:|---|
| Chest width | 30.5 mm | GREEN |
| Waist width | 25.0 mm | GREEN |
| Hip width | 25.2 mm | GREEN |
| Chest depth | 17.8 mm | GREEN |
| Waist depth | 16.4 mm | GREEN |
| Hip depth | 16.8 mm | GREEN |
| Torso height | 19.3 mm | GREEN |

## Pelvis

| Parameter | Value | Status |
|---|---:|---|
| Width | 25.0 mm | YELLOW |
| Depth | 17.0 mm | YELLOW |
| Height | 5.8 mm | YELLOW |

The pelvis measurements are useful for blockout, but the final torso-pelvis fusion remains open.

## Arms

| Section | Width / visual height | Depth | Status |
|---|---:|---:|---|
| Shoulder | 10.2 mm | 8.6 mm | GREEN |
| Biceps | 9.3 mm | 7.9 mm | GREEN |
| Elbow | 8.0 mm | 7.0 mm | GREEN |
| Forearm | 8.8 mm | 7.3 mm | GREEN |
| Wrist | 7.0 mm | 6.2 mm | GREEN |
| Upper-arm length | 11.0 mm | — | GREEN |
| Forearm length | 10.0 mm | — | GREEN |

Shoulder centers: **X ±15.5 mm** — GREEN.

## Hands

| Element | Length | Width | Depth | Status |
|---|---:|---:|---:|---|
| Palm | 7.5 mm | 6.2 → 9.4 mm | 3.5 → 4.0 mm | GREEN macro / YELLOW topology |
| Index | 5.5 mm | 1.9 mm | 1.9 mm | YELLOW |
| Middle | 6.0 mm | 2.0 mm | 1.9 mm | YELLOW |
| Ring | 5.5 mm | 1.9 mm | 1.9 mm | YELLOW |
| Pinky | 4.7 mm | 1.7 mm | 1.9 mm | YELLOW |
| Thumb | 5.1 mm | 2.1 mm | variable profile | YELLOW |

Palm size can be frozen. Finger lengths are good for blockout, but phalange segmentation, curvature, deformation loops and final hand topology should remain open.

## Legs

| Section | Width | Depth | Status |
|---|---:|---:|---|
| Hip | 11.0 mm | 8.9 mm | GREEN |
| Thigh | 10.6 mm | 8.5 mm | GREEN |
| Knee | 9.1 mm | 7.6 mm | GREEN |
| Calf | 9.7 mm | 8.1 mm | GREEN |
| Ankle | 7.9 mm | 7.1 mm | GREEN |
| Total leg length | 24.0 mm | — | GREEN |

Hip/leg centers: **X ±8.15 mm** — GREEN.

## Shoes

| Parameter | Value | Status |
|---|---:|---|
| Length | 18.0 mm | GREEN |
| Width | 11.9 mm | GREEN |
| Height | 9.0 mm | GREEN |
| Sole thickness | 1.8 mm | GREEN |
| Current Y center | -4.2 mm | YELLOW placement |
| Approx. toe projection from ankle axis | 13.2 mm | YELLOW placement |
| Approx. heel projection from ankle axis | 4.8 mm | YELLOW placement |

The shoe dimensions can be frozen. Exact forward/back placement may vary by character and footwear design.

## Vertical layout in current candidate

| Landmark | Z |
|---|---:|
| Ground | 0.0 |
| Shoe | 0.0 → 9.0 |
| Leg | 8.3 → 32.3 |
| Pelvis | 31.0 → 36.8 |
| Torso | 35.8 → 55.1 |
| Neck | 55.1 → 59.1 |
| Head | 60.5 → 95.0 |

**Important:** the head/neck connection is not final. Do not use these Z values as justification for final fused topology until that transition is corrected and visually validated.

## Production decision

### Freeze now

- global 95 mm scale,
- head width/height and jaw proportion,
- torso macro dimensions,
- arm lengths and arm section profiles,
- palm macro size,
- leg length and section profiles,
- shoe dimensions,
- neutral eye/iris size and spacing.

### Keep editable

- exact head depth and rear skull/nape contour,
- pelvis fusion,
- mouth and ear character variation,
- exact shoe Y placement,
- individual finger topology.

### Do not finalize yet

- head/neck fusion,
- shoulder/torso fusion,
- hip/pelvis fusion,
- final hand/phalange topology,
- regional deformation loops for rigging,
- hair, clothing and prop standards.
