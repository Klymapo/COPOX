# STYLIZED — ALTH_META

Parametric Blender project for developing a reusable **stylized chibi low-poly character base** from measured proportions and iterative visual calibration.

## Current status

- Current model version: **ALTH_META v0.8.3 — Stylized Anatomy**
- Target height: **95 mm**
- Modeling environment: **Blender 4.x**
- Base pose: **T-pose**
- Current focus: proportions, silhouette, hands, limbs, face placement and clean stylized geometry before rigging/clothing/hair.

## Goal

The project started from a Funko-like blockout and is being migrated toward a more refined stylized chibi low-poly language: smaller/less cubic head, longer and shaped limbs, larger expressive hands, solid shoes, simplified anime-style facial features, and controlled faceting instead of fully smooth geometry.

The goal is **not to reproduce any specific character**, but to extract and formalize the dimensional language of the supplied visual references into a reusable base body.

## Repository structure

```text
scripts/     Blender generation scripts
docs/        measurements, decisions, version history and roadmap
data/        measurement registry / editable tracking data
```

## Latest dimensional direction

Key values currently being tested in v0.8.3:

- Head: 40 W × 31 D × 34.5 H mm
- Chest: 30 mm
- Waist: 25.5 mm
- Pelvis: 25.5 mm wide
- Arm: continuous shoulder → elbow → wrist geometry
- Hand palm: 6.8 mm long, 6.0 → 8.6 mm wide
- Leg: 24 mm, profiled hip → thigh → knee → calf → ankle
- Shoe: 16.5 × 11.8 × 9 mm

See `docs/MEASUREMENTS.md` for the complete current specification and `docs/CHANGELOG.md` for the evolution of the model.

## Workflow

1. Generate the parametric base in Blender.
2. Compare front / 3-4 / profile views with the chosen visual references.
3. Record dimensional changes.
4. Adjust silhouette before merging geometry.
5. Refine hands, shoes, head and facial geometry.
6. Merge cleanly by region.
7. Add hair and clothing systems.
8. Prepare the final reusable base for rigging.

## Planned milestones

- **v0.8.4** — shape refinement: head front/back depth control, larger hands with segmented fingers, improved calf/knee silhouette, longer toe box.
- **v0.9** — controlled geometry fusion by region.
- **v0.10** — first reusable hair masses + refined face.
- **v1.0** — stable base body ready for rigging and character-specific adaptation.

## Relación con otros repositorios

- **Este repositorio:** investigación paramétrica de anatomía y proporciones. La versión documentada de referencia es v0.8.3; los scripts `v0_8_4a` y `v0_8_4b` existen como iteraciones posteriores, sin asumir su aprobación.
- **ALTH-META / AlasTheo:** sistema de producción, referencias y auditoría de assets en [Klymapo/alth-meta](https://github.com/Klymapo/alth-meta).
- **stylizer:** aplicación/pipeline de generación 3D. Es un proyecto distinto y no se debe fusionar por coincidencia de nombre.

**Política:** no sustituir la base visual aprobada por un candidato sin revisión de referencias y capturas.
