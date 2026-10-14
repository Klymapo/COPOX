# Maniquí v0.3 — primer parche experimental sobre v0.2b
Fecha: 2026-10-14. Responsable de continuación: Argos (GPT-6). Estado: **NO APROBADO**.

## Fuente y trazabilidad
- Base real: `assets/maniqui/maniqui_v0_2.glb` (v0.2b de Elio en la última actualización de la bitácora). SHA-256 `79799db01303a13886136afe4b98216aa20d512ee6f5d3549984bf638cac0986`.
- Baseline y sus scripts reproducibles intactos, fusionados previamente mediante PR #33.
- Rama experimental exclusiva: `experimentos/maniqui-v03-reparacion-facial`, PR borrador #34. No fusionar sin aprobación de Admin.
- Script: `tools/maniqui/reparar_v03.py` (Python, numpy, sin Blender ni GPU).
- Diagnóstico: `tools/maniqui/diagnostico_v03.py`. Capturas: `tools/maniqui/render.py`, `pose.py`; comparación: `comparar_v03.py`.

## Problema documentado
El cráneo analítico era aceptablemente redondo, pero la cara heredada de Gamma seguía fragmentada junto a la línea de pelo, cejas y sienes. El análisis real detectó **4,604 aristas abiertas en Cabeza** (5,412 triángulos, 5,406 vértices). La pieza `Craneo` tenía 59 aristas de borde (1,053 triángulos, 557 vértices). Estos bordes de Cara también pueden incluir islas UV o geometría desconectada; no representan automáticamente 4,604 agujeros físicos separados.

## Experimento v0.3
Se añadieron 38 triángulos (22 vértices) sobre 19 aristas del borde craneal, utilizando anclajes de superficie cercanos bajo las cejas. No se borró, desplazó ni reemplazó ninguna facción original. Todo el cuerpo, manos, pies, animaciones y estructura de rig se conservó. Las normales nuevas se promedian y los pesos se heredan de Head.
- Cráneo: 557 → 579 vértices; 1,053 → 1,091 triángulos.
- 22 anclajes seleccionados; distancia media del anclaje ≈3.48 cm antes de mezcla.
- Rig: 56 huesos y 29 clips, idéntica lista de animaciones y skin.
- Candidato: `assets/maniqui/maniqui_v0_3.glb` en esta rama.
- Evidencia: `assets/maniqui/previews/maniqui_v0_3.png` (4 vistas), `maniqui_v0_3_wave.png` (Wave). Se programó comparativa sincronizada `maniqui_v0_2b_vs_v0_3.png` y detalle `_cabezas.png`.

## Evaluación visual y límites
**Sin aprobación.** La captura real muestra una ligera continuidad superior, pero siguen visibles grietas, islas antiguas y geometría angulosa alrededor de cejas, ojos y sienes, tanto de frente como de lado. No se soldó la malla nueva a Cara: es una cobertura de prueba sobre el borde de Cráneo. Por tanto **NO** se certifican estanqueidad, corrección facial completa, Likeness, suavidad ni deformación en Godot.

**Siguiente paso recomendado:** clasificar en la cara las islas por conectividad espacial y material/UV, distinguir rasgos legítimos de restos de pelo/lentes, y reconstruir una banda limpia unida a contornos reales del rostro (evitar usar la proximidad euclidiana como único criterio). Mantener ojos, nariz, orejas y boca protegidos; nueva comparación de cuatro vistas y prueba en Godot. No modificar Delta ni v0.2 antes de aprobación.

## Registro de cambios
- **2026-10-14** · Creada rama experimental y PR #34, sin fusión.
- **2026-10-14** · Diagnóstico no destructivo por pieza: bordes, pesos, clips y límites espaciales.
- **2026-10-14** · Implementado parche v0.3 conservador de línea frontal; GLB generado en CI, 4 vistas y Wave; **rechazado provisionalmente como versión aprobada** por defectos faciales residuales.
- **2026-10-14** · Automatizadas capturas comparativas v0.2b/v0.3 mediante GitHub Actions gratuito; baseline protegido.
