# G2-C2 · Alastor sin lentes · retiro del accesorio y diagnóstico de residuos

Fecha: 2026-10-14. Estado: **EXPERIMENTAL · rostro original intacto · evaluación de restos pendiente**. No fusionar.

## Cambio artístico exigido
El objetivo visual del Maniquí/Alastor es **SIN LENTES**: sin montura, cristales, puente ni patillas. No confundir las patillas de los lentes con pelo, sienes o anatomía auricular. Ojos, párpados, pestañas, cejas, nariz y orejas permanecen protegidos.

## Procedencia del accesorio
El generador histórico `tools/maniqui/maniqui.py` ya había clasificado los polígonos de lentes por textura/posición y creado una pieza independiente `Lentes` dentro de `assets/maniqui/ropa_alastor_v0.glb`, separada de `Cabeza` y `Craneo` del maniquí base.

Se encontró exactamente **una primitiva etiquetada `Lentes`**, `mesh=0, primitive=1` del GLB de ropa. Comparte material `GammaHead` con otras piezas; **nunca identificar accesorios sólo por nombre de material**, ya que podría eliminar el rostro. El maniquí r3 no tiene una primitiva explícita llamada `Lentes`, pero sí puede conservar detalles de geometría antigua sin etiqueta mezclados con el rostro.

## Motor implementado
- `copox/geometry/eyewear_guard.py`: encuentra accesorios etiquetados mediante identidad de primitiva. Devuelve copia del árbol glTF sin la pieza, conserva buffer, skin, nodos, materiales, y animaciones históricos. También clasifica proximidad de triángulos del rostro a la ubicación de la montura mediante `cKDTree`, **sin autorizar borrado**.
- `tools/maniqui/g2c2_no_glasses.py`: parte de r3 original SHA256 `3aec25dd...` y `ropa_alastor_v0.glb`; produce un **GLB de ropa hermano** `assets/maniqui/ropa_alastor_g2c2_sin_lentes.glb` en artifact GitHub Actions, nunca reemplazando el original. Copia preservada de skins y 29 definiciones de animación del archivo de ropa; conserva las posiciones binarios originales; sólo retira la referencia al accesorio.
- `tools/maniqui/g2c2_eyewear_residue.py`: identifica triángulos faciales cercanos a vértices históricos de la montura a umbrales 3, 6 y 10 mm; distingue áreas **congeladas** (ojos, cejas, nariz, orejas) de áreas sin protección que requieren estudio, sin cortar. Genera cuatro vistas reales con mapa de sospechas rojo, protección turquesa y resto gris.
- `tests/test_g2c2_eyewear_guard.py`: pruebas para distinguir ojos de lentes, protección por facciones, prohibición de retirar fragmentos por mera proximidad, no-mutación de inputs y preservación de datos.
- Skills `.codex/skills/` y `.claude/skills/` actualizadas: `contour-extractor`, `gltf-rig-guardian`, `visual-critic`, `anatomic-cut`. Las cuatro exigen no reintroducir lentes.

## Capturas reales, no imágenes ilustrativas
- [Cuatro vistas antes (con lentes) / después (sin lentes)](G2C2_LENTES_4V_COMPARATIVA.png). La montura oscura desaparece completamente al excluir la primitiva correspondiente.
- [Cuatro vistas de proximidad de residuos](G2C2_RESIDUOS_LENTES_4V.png) y [JSON de triage](G2C2_RESIDUE_REPORT.json).

La ausencia de la montura negra **no certifica todavía** que las estructuras grises alrededor de ojos no contengan restos de lentes antiguos. Algunas pueden ser párpados o fragmentos del rostro. Visual Critic debe contrastar TODAS las referencias del personaje correcto. Esta diferencia se registra explícitamente como `REVIEW_REQUIRED` y ninguna de las dos operaciones de diagnóstico recorta un solo triángulo de `Cabeza`.

## Dependencias para volver a G2-C2 Surface Stitch
Una vez que sepa qué triángulos representan anatomía, separar el contorno anatómico de Cara sin lentes; verificar winding, conectividad, sin autointersección y compatibilidad UV/skin; utilizar `stitch-advancing-front` únicamente en dos bucles reales y el guardián de GLB antes de evaluar poses en Godot. El cráneo de r3 posee 128 aristas abiertas, pero Cara todavía no presenta un contorno homólogo simple; retirar lentes por sí solo NO lo soluciona.

**No modificar r3, no reemplazar originales, no fusionar PR, no certificar likeness ni animaciones faciales.** El GLB hermano de ropa sin lentes es un paquete de prueba, no nueva base del juego.
