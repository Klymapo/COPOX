---
name: surface-stitch
description: Reconstruye conexiones topológicas entre superficies 3D: detecta bordes reales, empareja contornos de igual longitud y crea una banda de triángulos con índices compartidos y atributos conservados.
---

# Surface Stitch · Unión craneofacial y otras costuras

## Activación
Usar cuando dos superficies tengan bordes abiertos compatibles y deban conectarse como una sola topología.

## Procedimiento
1. Leer `docs/COPOX_PROCEDIMIENTO_GEOMETRICO_CODEX_2026-10-14.md`. Obtener bordes orientados reales con `copox.geometry.kernel.boundary_loops`; tratar duplicaciones de UV por separado.
2. Comprobar que ambos contornos tienen igual cantidad de puntos y sentido consistente. El kernel actual **rechaza contornos de tamaño distinto**; no forzar con un emparejamiento de vértices incorrecto.
3. Si las piezas están separadas en primitivas del GLB, convertirlas en `MeshPart` con posiciones, caras, atributos compatibles e IDs de material. Ejecutar `copox.geometry.surface_stitch.stitch_parts`.
4. La nueva banda usa los IDs de vértices existentes. Se preservan UV, pesos y normales originales; el material de la banda se registra por cara. No inventar interpolación de morph targets ni de nuevos vértices.
5. Ejecutar pruebas de conectividad, manifold, winding, distancias, degenerados y autointersecciones si existe un auditor; devolver `RESEARCH_REQUIRED` cuando falte alguna comprobación crítica.
6. **No afirmar soldadura final de GLB**: separar primitivas por materiales durante exportación puede perder la conectividad indexada. Se requiere un exportador glTF/GLB validado, prueba de reimportación y poses en Godot antes de aprobar el resultado.
7. Presentar cuatro vistas reales, primer plano de unión, rig/animaciones preservados y pedir aprobación humana. Nunca fusionar automáticamente.

## Comprobación
`python -m unittest discover -s tests -p 'test_geometry_operations.py' -v`.

## Enlace con Visual Critic
Solicitar `operator=Surface Stitch` sólo si el diagnóstico mide bordes abiertos reales, dos loops de cardinalidad igual, winding correcto, atributos compatibles y distancia máxima segura. Confirmar el área afectada en **TODAS las referencias aportadas**. Un overlap visualmente limpio no es un cierre topológico; exigir pruebas sobre índices y reimportación GLB. La salida permanece experimental hasta comprobar export de materiales, rig, poses y Godot.

## G2-C · frente de avance desigual (implementado y probado)
Antes de coser: ejecutar `contour-extractor` y cotejar absolutamente TODAS las referencias mediante `visual-critic`. Para anillos válidos de longitud desigual, usar `copox.geometry.advancing_stitch.stitch_unequal_loops` o `surface_stitch.stitch_parts_unequal` y registrar índices/winding, distancias, material y skin por vértice. No utilizar el ejemplo Gemini sin corregir: `edges_unique_length` es longitud, no incidencia. No ejecutar `trimesh.load(force='mesh').export` como vía de preservación de GLB. `gltf-rig-guardian` debe demostrar un export completo antes de utilizar el resultado; `geometry-profiler` mide costes reales y rechaza afirmaciones no medidas. Hasta entonces, devolver geometría en memoria con `production_ready=false`. Real r3 preflight debe BLOQUEAR: la cara tiene bordes ramificados, no dos loops homologados.
