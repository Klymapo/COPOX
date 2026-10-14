# COPOX · Auditoría visual contra TODAS las vistas y referencias
Fecha: 2026-10-14 · Propuesta experimental. No activa loops ni aprueba modelos.

## Objetivo central
Ningún agente debe declarar que un modelo/rig/movimiento/escena "se parece" o "no tiene bultos" a partir de una vista favorable. Se revisa **cada referencia suministrada**, incluida cada imagen secundaria, frontal/3-4/perfil derecho/izquierdo/espalda/superior si están presentes, y cada pose/fotograma de vídeos.

Dos conceptos separados:
- **Cobertura verificable:** todas las referencias y vistas/poses declaradas tienen pareja de render y aparecen en un reporte; archivos faltantes bloquean.
- **Juicio visual:** una persona o revisor visual examina anatomía, identidad, curvatura, articulaciones, vestuario, etc. Puede detectar defectos sin referencia exacta, pero no declarar discrepancia artística específica sin sustento. El script no suplanta visión humana.

## Contrato JSON

Ejemplo ilustrativo (rutas ficticias, **no ejecutar** hasta proporcionar imágenes reales):

```json
{
  "asset_id": "alastor-propuesta",
  "required_views": ["front", "three_quarter", "side", "back", "top"],
  "provided_reference_files": [
    "assets/references/alastor_front.png",
    "assets/references/alastor_front_otra.png",
    "assets/references/alastor_34.png",
    "assets/references/alastor_side.png",
    "assets/references/alastor_back.png",
    "assets/references/alastor_top.png"
  ],
  "references": [
    {"id":"frente-principal","view":"front","image":"assets/references/alastor_front.png","camera_alignment":"approximate"},
    {"id":"frente-adicional","view":"front","image":"assets/references/alastor_front_otra.png","camera_alignment":"approximate"},
    {"id":"tres-cuartos","view":"three_quarter","image":"assets/references/alastor_34.png","camera_alignment":"approximate"},
    {"id":"perfil","view":"side","image":"assets/references/alastor_side.png","camera_alignment":"approximate"},
    {"id":"espalda","view":"back","image":"assets/references/alastor_back.png","camera_alignment":"approximate"},
    {"id":"superior","view":"top","image":"assets/references/alastor_top.png","camera_alignment":"approximate"}
  ],
  "candidate": {"id":"candidate-1","views":[
    {"view":"front","image":"run/frontal.png"},
    {"view":"three_quarter","image":"run/tres_cuartos.png"},
    {"view":"side","image":"run/perfil.png"},
    {"view":"back","image":"run/espalda.png"},
    {"view":"top","image":"run/superior.png"}
  ]}
}
```

- `provided_reference_files` es el inventario de **todos los archivos visuales aportados**. La diferencia contra `references[].image` es un bloqueo, incluso si cuatro vistas sí coinciden.
- `view` es una etiqueta canónica libre pero consistente (`front`, `three_quarter`, `side`, `back`, `left_side`, `top`, `bottom`, etc.).
- `pose` es opcional y por defecto `rest`; para animaciones usar `walk_contact`, `sit_impact`, etc. Cada referencia en otra pose exige un render específico de esa pose.
- `camera_alignment` es `exact`, `approximate` o `unknown`. No reclamar cámara exacta por una observación visual. Datos de FOV, escala, perspectiva, orientación y distancia pueden adjuntarse en el manifiesto y los reportes.
- `image` y `mask` son archivos reales relativos a `--root`. `mask` es opcional y debe ser binaria 0/255. Un par con máscaras y cámara `exact` permite IoU y Chamfer de silueta; con cámaras distintas las métricas se omiten. No equiparar IoU alto a likeness.
- `manual_review` puede incluir `{"verdict":"PASS|ISSUE|UNDECIDED", "observations":["..."], "reviewer":"..."}`; registrar sólo una evaluación real, con cada defecto vinculado a `reference_id` y más de una vista cuando corresponda. No rellenar automáticamente.

Para vídeo, primero extraer fotogramas con tiempo/pose/ángulo trazables, registrar cada fotograma relevante en `provided_reference_files` y `references`. Conservar el vídeo de origen para consultar timing, no sustituirlo por tres imágenes y afirmar que se evaluó la secuencia entera.

## Ejecutar (sin IA generativa)
```bash
python -m copox.visual.critic docs/mi_manifest.json --root . --output .copox/evidence/visual
```

Salida: comparativas PNG referencia/candidato, `report.json` con una entrada por referencia, defectos/ausencias, vistas extra sin referencia, peor IoU de máscaras cuando se calcularon, `INCOMPLETE`/`REVIEW_REQUIRED`/`ISSUES_FOUND`/`READY_FOR_ADMIN`. Ninguno significa aprobación automática.

**Regla de decisión:** `INCOMPLETE` prohíbe concluir semejanza; `REVIEW_REQUIRED` requiere inspección de todos los pares; `ISSUES_FOUND` no se oculta con el promedio; `READY_FOR_ADMIN` significa sólo que toda referencia se revisó y no se marcó problema, falta aprobación expresa.

## Seis skills
- `.codex/skills/visual-critic/SKILL.md`: controlador de cobertura multivista y diagnóstico artístico.
- `rig-architect`: esqueleto, skinning y articulaciones con deformaciones comparadas.
- `motion-lab`: movimiento/biomecánica/foot contacts con comparación de vídeos y poses.
- `facial-acting`: facciones, boca, mirada y actuación sin perder morphs.
- `cloth-dynamics`: telas y gabardinas, pruebas de cuerpo/silla/animaciones.
- `scene-director`: cámara, iluminación, distribución y continuidad de escena Godot.

Las seis están reflejadas bajo `.claude/skills/`. Su documentación operativa **no** significa que los algoritmos de rig/cloth/escenas estén completamente implementados o certificados.

## Escenarios de prueba obligatorios
1. Dos fotos frontales y un 3/4, lateral y espalda: exactamente cinco comparaciones, sin perder la segunda frontal.
2. Inventario de 6 imágenes, sólo 5 referencias: `INCOMPLETE`.
3. Falta el render de un perfil: `INCOMPLETE`, aunque las otras vistas sean perfectas.
4. Una discrepancia de perfil: `ISSUES_FOUND`, incluso si todas las otras referencias registran PASS.
5. Una cámara aproximada: **nunca** calcular IoU alineado falso.
6. Nuevas poses/video frames: sin render del fotograma correspondiente, `INCOMPLETE`.
7. Faltan notas de revisión: `REVIEW_REQUIRED`, sin aprobación.
8. Un candidato tiene vista superior pero sin referencia equivalente: registrarla como sin referencia y mantener `REVIEW_REQUIRED`; no inventar una comparación.

## Límites actuales
La herramienta compara imágenes/máscaras y garantiza cobertura. **No detecta por sí sola** que una frente es demasiado convexa, ni evalúa texturas o expresiones de forma semántica. Esto debe revisarlo Visual Critic con inspección visual real y reportes por referencia. No inventar detección semántica, falsear un dictamen artístico ni publicar imágenes privadas sin permiso.

Próximos módulos para progresar: landmarks por vista con anotaciones humanas, curvatura sobre malla, consistencia de normales, medición regional, frames/key poses por video, conectores Godot/Blender y retarget de rig. Todos sin sustitución automática de activos.

## Registro de cambios
2026-10-14 · Argos: protocolo de cobertura total, generador de pares comparativos, máscaras métricas y seis skills portables en rama independiente basada en PR #37. Sin modificar GLBs ni fusionar.
