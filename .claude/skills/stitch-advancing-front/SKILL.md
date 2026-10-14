---
name: stitch-advancing-front
description: Ejecuta la triangulación de frente codicioso sobre dos bucles de frontera verdaderos de longitud diferente; valida winding, gaps, degenerados y manifold y rechaza exportaciones no seguras.
---

# COPOX · Stitch Advancing Front G2-C

## Cuándo aplicar
Sólo después de `contour-extractor` y Visual Critic; nunca sobre la cara r3 fragmentada sin selección de contorno anatómico y evidencia de todas las vistas.

## Motor
`copox.geometry.advancing_stitch.stitch_unequal_loops`
`copox.geometry.surface_stitch.stitch_parts_unequal` conserva atributos por vértice y material por cara en RAM.

- Recibe loops orientados REALES con cardinalidades distintas; no necesita subdivisión ficticia para forzar 128=851.
- SciPy `cKDTree` elige par inicial; greedy consume exactamente una arista de un anillo por triángulo (N+M caras). No crear matriz densa NxM.
- El código valida máximo gap de TODAS las conexiones cruzadas, ratio de aristas, área no degenerada, winding, nonmanifold y ausencia de bucles restantes en topología indexada.
- El motor **NO garantiza ausencia de intersecciones en 3D** ni un parecido artístico correcto; la optimización de distancia local puede elegir una diagonal incorrecta desde el punto de vista anatómico.
- Nunca aplicar suavizado Taubin global a un rostro/rig sin máscaras de vértices protegidos y métrica de desviación contra cada vista.
- Los contornos tienen que compartir espacio global de índices. Piezas GLB con materiales distintos precisan un serializador que respete materiales por cara y `skin/UV/morph`; NO usar `trimesh.load(force='mesh')` como preservador del rig.
- Un informe que diga `loops_after=0` NO equivale a `production_ready`. Las autointersecciones y exportación aún deben probarse.

## Pruebas
`python -m unittest discover -s tests -p 'test_g2c_advancing_stitch.py' -v`
`python -m unittest discover -s tests -p 'test_g2c_surface_parts.py' -v`
No promover variantes mientras `self_intersections_checked=false`, `exported_glb_verified=false` o `artistic_references_approved=false`.

## Determinismo
Sin aleatoriedad; mismos arrays/parametrización -> mismo índice de triángulo. Medir tiempos antes de añadir Numba. Registros de parámetros, SHA, selección de contorno y razones de rechazo por candidato.

