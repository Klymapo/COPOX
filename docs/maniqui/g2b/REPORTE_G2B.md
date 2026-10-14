# COPOX · Maniquí G2-B · Cascarón continuo y auditoría real de Godot

**Fecha:** 2026-10-14. **Estado:** investigación cerrada, 5 candidatos **NO APROBADOS**, PR #41 borrador. Sin fusionar.

## Qué se intentó
El anterior G2 Cut Probe retiró 167 triángulos, conservó el rig y sin embargo aumentó huecos visibles. En G2-B se recuperó la estrategia matemática de Codex: **construir tejido nuevo** en lugar de solamente mover o quitar caras.

Nuevo módulo reusable `copox/geometry/craniofacial_loft.py`: selecciona el único rim válido del cráneo, reutiliza sus **índices originales de vértice**, genera anillos con transición radial paramétrica dependiente de ángulo anatómico (+Z frente, Y arriba) y opcionalmente cierra la parte inferior con triángulos en la misma primitiva. Los pesos, joint IDs, UV y demás atributos de cada anillo nuevo se trasladan del vértice original del rim. No modifica la fuente, sólo GLBs hermanos.

`tools/maniqui/g2b_shell_candidates.py` genera candidatos desde `assets/maniqui/maniqui_v0_3_r3.glb` SHA256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`, en vez de construir encima del G2 rechazado.

## Medidas verificadas con GLB reimportado

| Candidato | Triángulos añadidos a Craneo | Cambios en Cara | Evaluación visual |
|---|---:|---:|---|
| `r1_short` | 2,688 | 0 | Mejor cobertura local, sigue fragmentación |
| `r2_deep` | 3,712 | 0 | Nuca más continua, pero sobrecubre facciones |
| `r3_deep_cut` | 3,712 | Retira 167 | No restaura costura facial ni cejas |
| `r4_rear_focus` | 3,200 | 0 | Nuca mejor, pero manchas negras en frente, ojos/nariz |
| `r5_rear_focus_soft` | 3,200 | 0 | Problemas de intersección frontales similares a r4 |

Los cinco tienen: 56 huesos originales, 29 definiciones de clips originales, materiales y nodos conservados, `Craneo` extendido sin perder vértices/triángulos de cap y **0 bucles abiertos en la primitiva nueva** tras reimportar. El cierre de la primitiva NO significa soldadura a la `Cabeza` original, que sigue siendo otra primitiva, ni garantiza cero autointersecciones.

**[Lámina comparativa auténtica de 4 vistas × 6 filas](G2B_lamina_4v_candidatos.png)**. Veredicto `G2B_VISUAL_VERDICT.json`: **ningún candidato a promoción**. La silueta/continuidad de nuca mejora en variantes profundas, pero la forma facial empeora. No se usaron fotos de identidad confusa para decidir parecido artístico.

La suite `tests/test_g2b_craniofacial_loft.py` comprueba conectividad, winding, falta de degenerados, no-mutación de base y preservación de atributos. CI NumPy/SciPy/Pillow/Trimesh [run #38610356268](https://github.com/Klymapo/COPOX/actions/runs/38610356268), **SUCCESS**. Los cinco GLBs quedaron únicamente como artifacts de Actions (duración 30 días), no introducidos automáticamente a historial de assets aprobados.

## Hallazgo secundario de alto impacto: compatibilidad Godot

Se descargó **Godot 4.7.2 oficial, gratuito y headless** y se ensayó con r3, r4 y r5. La primera importación falló incluso en **r3 original**, por propiedades glTF heredadas:
- 16 accessors con `count=0`.
- 10 primitivas sin geometría real y 1 malla completa vacía.
- 15 canales de pesos faciales `weights` dirigidos a esa malla vacía.

Se incorporó `tools/maniqui/gltf_sanitize.py` para preparar **copias**, jamás tocar r3: elimina accesores/mallas/primitivas sin datos, archiva en `asset.extras` los 15 canales de morph huérfanos (sin mesh deformable) y mantiene el contenido binario original de vértices, canales óseos y datos de animación. Rechaza cualquier accesor vacío que siga referido desde geometría/skin/animación válida. Genera SHA-256 e informes JSON por archivo.

**Resultado real:** tras saneamiento, Godot 4.7.2 importó correctamente **baseline, r4 y r5**, cada uno con **56 bones, 29 clips nombrados y 24 surfaces**, poses óseas finitas. [Informe de Godot](godot/godot_result.json). **Advertencia importante:** 15 de los 29 clips fueron originalmente animaciones exclusivamente faciales para una malla vacía. Su nombre puede seguir importándose, pero no tienen movimiento facial útil; el conteo 29 NO significa que existan 29 animaciones funcionales. Los canales originales inválidos permanecen en el GLB histórico; el saneador conserva referencias archivadas a ellos y no los hace funcionales.

La solución de compatibilidad no reconstruye expresión, parpadeo ni morph targets; eso pertenece a Facial Acting. La validación de importación no equivale a jugar una escena de Godot ni probar colisiones, física o clips completos frame-by-frame.

## Siguiente estrategia tras el rechazo de G2-B
1. Abandonar la "falda completa" que invade ojos y nariz, aunque el cráneo aislado sea watertight.
2. Usar **Visual Critic** y únicamente las referencias del Alastor correcto para localizar regiones a cubrir por máscara anatómica, dibujar el perímetro de transición en todas las vistas y demostrar diferencias regionales.
3. Estudiar una **piel interior localizada**, con topología de cara recortada y reconstruida y dos contornos homologados; preservar facciones con protección por triángulo, UV y rig. No soldar vecinos cercanos indiscriminadamente.
4. Separar en el pipeline `FILE_IMPORT_OK`, `ANIMATION_TRACKS_OK`, `RIG_DEFORMATION_OK`, `ARTISTIC_LIKENESS_OK`. Un solo fracaso impide promover un candidato.
5. Reconstruir los 15 clips faciales sobre un rig real, con referencias de gestos y vídeos. No inventar movimiento útil sobre una malla inexistente.

**Archivos y evidencias:**
- `copox/geometry/craniofacial_loft.py`
- `tools/maniqui/g2b_shell_candidates.py`
- `tools/maniqui/gltf_sanitize.py`
- `tests/g2b_godot_validate.gd`
- `docs/maniqui/g2b/G2B_reporte.json`
- `docs/maniqui/g2b/G2B_VISUAL_VERDICT.json`
- `docs/maniqui/g2b/godot/`

**Seguridad:** no se borró ni reemplazó r3, no se ejecutó Godot sobre el juego AlasTheo, no hubo commits de GLB aprobados y no se fusionó PR #41 ni sus dependencias. La procedencia histórica mixta de r3 se mantiene y el laboratorio no constituye autorización legal para su redistribución final.
