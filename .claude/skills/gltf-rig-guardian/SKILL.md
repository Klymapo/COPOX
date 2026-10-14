---
name: gltf-rig-guardian
description: Audita preservación de glTF/GLB, skeletons, atributos por vértice, materiales, UV, morphs y canales animados; ejecuta saneamiento no destructivo y pruebas en Godot.
---

# COPOX · GLTF Rig Guardian

## Activación
Antes y después de cualquier stitch, retopología, normal recalculation, UV bake, exportación y prueba en Godot.

## Invariantes
1. Nunca sobrescribir modelos fuente ni baselines aprobados. Registrar SHA-256 y origen.
2. Contar y preservar joints, inverseBindMatrices, nombres y pistas de animaciones válidas; comparar transformaciones, pesos normalizados, UV, materiales, texturas y morph targets. `JOINTS_0/WEIGHTS_0` juntos y finitos.
3. **La definición de 29 clips no prueba 29 movimientos:** Godot puede completar pistas estáticas; contar claves variables y comprobar pose en el tiempo. Los 15 canales faciales heredados sobre malla vacía deben marcarse NO FUNCIONALES.
4. No usar `trimesh.Trimesh(...).export()` para prometer preservación de rig de un GLB: el objeto geométrico aislado no conserva la escena animada glTF original.
5. Mantener materiales por cara / atributos de vértices originales. G2-C en `surface_stitch.py` conserva dichos arrays en RAM, **no tiene exportador GLB aprobado** aún; bloquear cualquier sustitución hasta tener serializador y reimportación.
6. Si los GLB antiguos tienen accesores/primitivas vacías, utilizar `tools/maniqui/gltf_sanitize.py` en una **copia**; archivar canales huérfanos, no declararlos restaurados.
7. Godot oficial headless + artefacto visual: contar 56 bones, importar los modelos, validar animaciones variables, mover joints, verificar malla/deformación y cuatro vistas reales. Sin alterar GameState/autoloads del juego.
8. GATE separado: `IMPORT_OK`, `ANIMATION_TRACKS_OK`, `DEFORMATION_OK`, `ATTRIBUTES_OK`, `VISUAL_CRITIC_OK`. Todos deben superar antes de recomendar a Admin.

## Evidencia
Reporte de diferencias fuente/candidato, SHA de cada GLB, capturas 4 vistas + poses/expresiones, pruebas Godot y decisión explícita de Admin. No fusionar ni elegir automáticamente.

