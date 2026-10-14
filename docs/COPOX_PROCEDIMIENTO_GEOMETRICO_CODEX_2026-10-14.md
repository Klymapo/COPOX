# COPOX · Motor de geometría guiada por restricciones (propuesta v0.1)
**Fecha:** 2026-10-14 · **Estado:** propuesta / sin activación / sin modificación de modelos.
**Origen:** reconstrucción reproducible de Maniquí r3 por Codex en PR #34 y comparación con PLATEAU de v0.4 en PR #36.

## 1. Qué hizo distinto Codex (basado en código, no en conjeturas)

Archivos reales en `main`:
- `tools/maniqui/reconstruir_v03.py`: `least_squares` del elipsoide craneal; corte de malla `Cabeza` en regiones, resampleo por ángulo `theta`, `gaussian_filter1d(..., mode="wrap")`, loft parametrizado con NT=128, NR=32, triangulación y cálculo de normales; 4097 vértices y 8064 triángulos de nueva cúpula.
- `tools/maniqui/auditar_v03.py`: preservación de buffers originales y primitivas congeladas; triangulos faciales y auriculares, skin y 29 animaciones; bordes abiertos, degenerados, aristas >2 incidentes y suma de pesos.
- `tools/maniqui/evaluar_v03.py`: cuatro vistas reales, ROI de cabeza, IoU, cuatro poses clave y tres puntos por cada clip = 87 muestras por candidato.
- `docs/MANIQUI_V03_CONTINUACION_2026-10-14.md`: decisiones, fallos por variante, criterio de parada y evidencia.
- Reproducción independiente: `docs/MANIQUI_V03_R3_REPRODUCCION_ARGOS_2026-10-14.json` en PR #35: mismo SHA256 de r3.

**La combinación decisiva fue: una superficie nueva + restricciones de preservación + candidatos hermanos + auditoría con geometría real.** No bastó el shrinkwrap ni mover vértices.

### Valores medidos
- r1: 99 triángulos faciales y 14 de oreja protegidos perdidos; no elegible.
- r2: conserva facciones pero pierde 38 triángulos auriculares; no elegible.
- r3: conserva ambos conjuntos; 56 huesos y 29 clips, pero 128 aristas de la cúpula abiertas, unión no soldada y perfil 94.78% IoU respecto a v0.3. No aprobado artísticamente.
- v0.4 i1/i2/i3: 0 triángulos de Cara recortados, máximo 10.05/18.25/18.25 mm de desplazamiento craneal; IoU vs r3 superior a 99.96%. Persisten los mismos 128 bordes abiertos y las placas defectuosas. El análisis visual confirmó PLATEAU.

**No confundir:** IoU alto respecto a la baseline NO implica progreso; puede indicar que casi nada cambió. Tampoco todas las aristas de borde por índice GLB son agujeros; primero analizar duplicaciones por UV/material y conectividad geométrica.

## 2. Arquitectura: codec de geometría como cassette, NO otro orquestador

El motor existente `copox/engine.py` ya implementa prepare/mutate/execute/capture/audit/learn/promote, candidatos hermanos y plateau.
La configuración de trabajo NO va en `copox/cassettes/enabled/`. No activar loops periódicos ni promoción.

**Propuesta del ciclo:**

```
[baseline + SHA + convenciones y licencia]
   |
[diagnóstico: semántica/UV/loops reales + congelar rasgos + objetivo medible]
   |
[seleccionar familia ALG: ajuste elipsoidal | loft anatómico | bridge/weld | transfer pesos]
   |
[2-3 hermanos parametrizados, misma baseline]
   |
[PRE-FLIGHT BARATO: validez GLB, protección, topología focal, ROI de vista simplificada]
   +--- fail -> rechazar y registrar causa (sin Wave, 29 clips ni render completo)
   |
[DEEP solo elegibles: 4 vistas+detalle, animaciones, Godot, revisión]
   |
[unanimidad y aprobación humana -> promover en state branch; release aparte]
   +--- no aptos -> PLATEAU, baseline intacta, recomendar otra técnica
```

**Brecha del engine actual:** `copox/engine.py` ejecuta `mutate -> execute -> capture -> audit`; la captura ocurre antes de auditar. Necesita una fase `preflight` ANTES de `capture` (o, transitoriamente, un wrapper de cassette que genere `preflight.json` y omita la evaluación profunda al fallar). Cambiar el motor requiere prueba de regresión del smoke, perfiles, archivos y política de promociones.

## 3. Familias de algoritmos (reutilizables)

1. **SurfaceFit**: elipsoide/loft/superficies periódicas para grandes siluetas lisas (cabeza, torso, brazos). Ajuste robusto y restricciones de puntos anatómicos; no usarlo para nariz/párpados/dedos.
2. **ContourBridge**: reconocer bucles de borde de piel y cúpula, ordenar por arco y orientación, crear correspondencia con landmarks, crear quads/triángulos conectados y soldar donde corresponde. Es el siguiente candidato principal para nuca y patillas. En Blender existe `bmesh.ops.bridge_loops`; `libigl.boundary_loop_all` puede servir para diagnóstico. Una simple superposición por proximidad NO cuenta como soldadura.
3. **SelectiveTopologySurgery**: eliminar placas sólo después de identificar componente y región anatómica; proteger triángulos (no sólo vértices), cerrar agujeros reales y conservar normales/UV.
4. **GuidedProjection**: wrap por partes/material/normal, con límite de distancia y pesos; útil en ropa y objetos cuando la topología es compatible, NO sustituto universal de una malla nueva.
5. **RigTransfer**: pesos interpolados en una banda nueva y validados en poses. Preservar animaciones binarias no garantiza deformación de malla, ni recupera morph targets que desaparecieron.

**Crucial para glTF:** `Cabeza` y `Craneo` están en primitivas distintas. Aun si coinciden por posición, no comparten índices de vértice entre primitivas. Hay que diseñar la unión física: consolidar la superficie en una topología interna común y exportar correctamente respetando materiales/UV, o demostrar conexión geométrica y render coherente según el objetivo; `boundary_edges = 0` por redondeo de posiciones no prueba por sí solo un weld real exportado.

## 4. Gates para optimizar costo

**A. Diagnóstico barato (CPU, sin poses):**
- SHA del archivo fuente y archivo de salida nuevo; ejes, unidades, versión de glTF y licencia.
- glTF-Validator (oficial); conteo de partes, skin/animaciones/morph, NaN, materiales.
- Preservación exacta de triángulos protegidos, integridad de índices/pesos, regresiones fuera de foco.
- Métrica topológica enfocada: aristas abiertas antes/después **descontando seams UV**, no manifold, triángulos degenerados, continuidad de normales, autointersecciones cuando la auditoría sea fiable.
- Métrica mínima de cambio perceptible en ROI objetivo, y ganancia respecto a una referencia aprobada. **Evitar aceptar sólo por IoU global >95%.**

**B. Revisión visual rápida (barata):** frente+3/4+perfil de ROI, mapa de diferencia, cortes longitudinales. Rechazar cambios imperceptibles o nuevos bultos ANTES de 87 poses.

**C. Auditoría profunda (sólo finalistas):** 4 vistas, acercamientos, Wave/Sit/Nod/HeadShake, 29 clips × 3 muestras, pruebas estructurales/glTF-Validator; carga y animaciones en Godot antes de aprobación.

Se añade `copox/geometry/preflight_gate.py`, un gate funcional **sobre métricas ya medidas**, no un auditor que lea directamente GLB. Contrato de ejemplo `copox/geometry/maniqui_geometry_recipe.example.json`, NO habilitado. El gate veta pérdida de triángulos, fallas del rig, solapes en lugar de seam conectado, no reducción de borde si es objetivo, falta de cambio visible y regresiones. `DEEP_ELIGIBLE` NO autoriza promoción.

Los umbrales de ejemplo (0.5% diferencia visible, 0.10 pp ganancia regional, 0.20 pp regresión máxima) son hipótesis iniciales que se calibrarán; no deben darse por universales.

## 5. Integración y transferibilidad

- **Maniquí/Alastor/Theo:** algoritmo de construcción por región, perfil de personaje, rig, morph y ropa.
- **Objetos y edificios:** SurfaceFit/loft, sin auditores de rig ni cara; métricas propias: superficie, escala, proporciones.
- **Prendas:** GuideProjection y pruebas de deformación/collision cloth.
- **UI y scripts:** mismo motor COPOX de candidatos/gates/reportes, pero NO usa el kernel de geometría; emplear cassettes UI/scripts existentes.

No crear un segundo engine y no asumir que todos los GLB comparten ejes/escala. Para ALTH suele usarse mm/Z-up durante Blender; el GLB maniquí es m/Y-up/+Z frente.

## 6. Limitaciones y seguridad

- Esta propuesta no modifica GLB y no demuestra todavía retopología soldada, licencia de modelo ni Godot.
- Cualquier paso que altere una región congelada, gestos/morph, 56 huesos o clips sin contrato explícito debe vetarse.
- Se requiere inspección de los términos de licencia aplicables al modelo de Gamma/Tencent si se redistribuyen derivados: licencia comunitaria no equivale a CC0/open source irrestricto.
- Ejecutar con Python/NumPy/SciPy/Pillow/Trimesh/Blender/libigl/gltf-validator según el cassette, y GitHub Actions con runners estándar públicos; no APIs IA pagadas ni mayores runners.
- Evidencia versionada temporalmente; evitar comprometer cientos de PNG o modelos repetidos a `main`. Archivar binarios y hashes donde corresponde; conservar lo rechazado sin sobrescribir.

## 7. Plan de implementación recomendado

**Hito G0 (hecho, propuesta):** documento + gate JSON + receta inactiva + pruebas unitarias.
**Hito G1:** diagnóstico `segment_components` + `boundary_loops` con deduplicación de posiciones sólo para ANÁLISIS; exportar mapas de islas, orejas, ojos, nuca y patillas.
**Hito G2:** mutador `bridge_anatomic_loops`: contornos por landmarks, resampleo, matching, triangulación, normales, pesos y UV; validar soldadura de la región objetivo.
**Hito G3:** extender `copox/engine.py` con preflight temprano compatible con smoke, sin auto-promoción. Benchmark de costo entre pipeline viejo y nuevo.
**Hito G4:** render y auditoría en Godot. Presentar comparación antes/después con decisión humana y aprobación separada.

**Primer benchmark obligatorio:** v0.3 r3 frente a v0.4 i1-i3; el gate debe rechazar variantes que sólo muevan casco y no mejoren la junta de nuca/patillas. Luego producir un primer candidato con menos bordes abiertos/placas conservando la cara.

## Fuentes consultadas
Código/reporte del repo Klymapo/COPOX (`PR #34`, `PR #36`).
- Especificación glTF 2.0: https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc
- glTF Validator: https://github.com/KhronosGroup/glTF-Validator
- Blender BMesh bridge_loops: https://docs.blender.org/api/current/bmesh.ops.html
- libigl boundary loops: https://libigl.github.io/libigl-python-bindings/api/igl/
- SciPy B-splines: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.make_splprep.html
- GitHub Actions estándares públicos: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Hunyuan 3D 2.1 Terms: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/hy3dshape/LICENSE

## Registro de cambios
- 2026-10-14 · Argos: auditoría profunda del pipeline Codex, mapeo al motor COPOX existente, propuesta de nuevas familias geométricas, preflight temprano y contrato inactivo. No fusionado, no activado, sin cambios a modelos.
