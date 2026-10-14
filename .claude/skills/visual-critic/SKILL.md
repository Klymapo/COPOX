---
name: visual-critic
description: Audita las irregularidades visuales de assets, personajes, rigs, animaciones y escenas comparando obligatoriamente TODAS las vistas, poses y referencias proporcionadas, sin ocultar discrepancias mediante promedios.
---

# Visual Critic · revisión cruzada de todas las referencias

## Activación
Toda evaluación de semejanza, curvatura, bultos, hundimientos, proporciones, gestos, ropa, iluminación, composición o poses donde haya capturas/referencias del usuario.

## Contrato inviolable
- **Usar la totalidad de las referencias proporcionadas**: principal, secundarias, vistas frontal, 3/4, ambos perfiles, trasera, superior/inferior, expresiones, poses, vídeos, dibujos y fotogramas. No seleccionar sólo las más favorables.
- Inventariar cada referencia con ID, procedencia, vista, pose, fecha/fotograma, cámara/aproximación y rasgos relevantes. No inferir que dos vistas tienen la misma cámara sin pruebas.
- Renderizar el candidato desde TODAS las vistas solicitadas y desde cada vista/pose identificable de referencia. Capturar también frente, tres-cuartos, perfil y espalda para modelos de personaje cuando sean pertinentes.
- Comparar **cada referencia por separado** con la captura del ángulo y pose correspondientes. Una diferencia en una sola referencia no desaparece porque otras tres coincidan.
- Si faltan vistas, archivos, equivalencias de cámara, referencias o fotogramas indispensables, emitir **INCOMPLETE**; no decir 'sin bultos' ni 'likeness aprobado'.
- Para inconsistencias entre referencias, documentar ambas, indicar cuáles son autoritativas según brief de Admin y solicitar decisión sin inventar proporciones.

## Herramienta comprobable
`python -m copox.visual.critic manifest.json --root . --output ruta/de/evidencia`
El JSON declara `required_views`, `references` y `candidate.views` (vista + pose + imagen, máscara opcional). El script produce un par comparativo por referencia y un `report.json` con cobertura completa y, con máscaras binarias y cámaras exactas, IoU y Chamfer por pareja. Sin máscara/cámara alineada, IoU no se calcula; comparación visual sigue siendo obligatoria.

## Diagnóstico experto
1. Leer `CLAUDE.md`, brief, las referencias aportadas y `docs/COPOX_VISUAL_REFERENCIAS_TOTALES.md`.
2. Revisar silueta completa y detalles en todas las vistas. Para cada defecto, localizar región/posición y registrar referencias que lo apoyan, así como vistas que lo contradicen. No basta detectar una curvatura: demostrar por qué contradice alguna referencia.
3. Buscar bultos por anomalías de curvatura/normales, huecos, intersecciones, asimetrías, fragmentos flotantes, proporciones, manos, pies, articulaciones, ropa y gestos. Comprobar la supuesta irregularidad en múltiples proyecciones.
4. Para movimiento: comparar momentos clave y movimientos según cada video/fotograma aportado, antes de puntuar timing, contactos y actuación.
5. Mantener por referencia `PASS`, `ISSUE` o `UNDECIDED`, observaciones verificables y evidencia visual; nunca inventar una revisión humana no realizada.
6. No concluir sólo con IoU ni promedios. Informar peor discrepancia, referencias no cubiertas y diferencias relevantes sin diluirlas.
7. Veredicto técnico: `INCOMPLETE`, `REVIEW_REQUIRED`, `ISSUES_FOUND` o `READY_FOR_ADMIN`. Incluso READY_FOR_ADMIN **no equivale a aprobación**.
8. Entregar plano de corrección accionable para Scully/Anatomic Cut/Stitch/Rig/Motion/Facial/Cloth/Scene y detenerse para aprobación de Admin; no fusionar.

## Regla de procedencia
No mezclar fotografías del usuario con PNG generados y afirmar que son el mismo ángulo. Registrar cámara/calibración; material sin permiso permanece privado. Renders reales, no imágenes inventadas para evaluar un GLB.

## Enlace ejecutable al motor geométrico (propuesta)
Para cada anomalía, **primero** obtener `report.json` con `anomaly_cross_view_matrix` (todos los IDs cubiertos). Medir geometría real de esa región; usar `copox.visual.mesh_diagnostics.analyze_plane_region` sólo cuando exista un **plano objetivo declarado a partir de referencia/brief**, no inventarlo. Para fragmentos/costuras usar análisis topológico del GLB y registrar `measurement_provenance` con SHA-256, método, ejes y unidades.
Ejecutar: `python -m copox.visual.critic MANIFEST --root . --output EVIDENCE --geometry-diagnostics GEOMETRY.json`. Se crean `report.json` y `geometry_plan.json`. También se puede ejecutar `python -m copox.visual.geometry_planner --visual-report EVIDENCE/report.json --geometry-diagnostics GEOMETRY.json --output EVIDENCE/geometry_plan.json`.
El plan propone **Scully** si hay protuberancia medida en superficie continua, **Anatomic Cut** si hay fragmentos y máscara de facciones segura, o **Surface Stitch** si existen dos contornos con conectividad y atributos compatibles.
No ejecutar planes cuando hay referencias faltantes, contradicciones, mediciones sin trazabilidad o morph/UV/skin no soportados. El plan **nunca** promociona ni edita GLB por sí solo: pasa a prueba sintética/experimental y reauditoría visual exhaustiva.

## Protocolo G2-C de correspondencia de contornos
Enlazar `contour-extractor` para obtener un **contorno facial ARTÍSTICAMENTE identificado** a partir de todas las vistas correctas del mismo personaje; las vistas contextuales de personajes distintos no sustituyen landmarks. No declarar topología correcta sólo porque una costura cierre 0 loops. Tras `stitch-advancing-front`, comparar todos los rendes por ángulo y gestos/poses correspondientes; obligar a `gltf-rig-guardian` a verificar pesos UV materiales y Godot, y `geometry-profiler` a evaluar rendimiento sin sustituir validez geométrica. Autointersección no medida o export glTF sin certificar → bloquear.

## G2-C2 · Criterio del cliente: sin lentes
Evaluar **la ausencia de montura, cristales, puente y patillas de gafas** en frontal, tres cuartos y ambos perfiles, y si hay referencias de espalda también. Diferenciar accesorio removido de geometría residual fusionada con la cara. El objetivo es retirar lentes, NO ojos/cejas/párpados ni pestañas. En `anomaly_cross_view_matrix` incluir `eyewear_frame_residue` y `glasses_temple_residue` si aún son visibles; cualquier duda en referencias o en la identidad del personaje mantiene el resultado en `REVIEW_REQUIRED`, sin promoción.
