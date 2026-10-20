# Brief · Pelo castaño ondulado con mechón al frente (Alastor)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- Polycount, hilos de pelo estilizado/low-poly por bloques (https://polycount.com/discussion/comment/1206868 y
  https://polycount.com/discussion/comment/2546008): el pelo de juego se construye con pocos mechones grandes
  (clumps) que siguen la forma del cráneo; la silueta manda sobre el detalle.
- BlenderNation, *How to model low poly hair* (https://www.blendernation.com/2014/08/17/how-to-model-low-poly-hair/,
  tutorial de Blender Passion): bloques por capas desde la nuca hacia la frente.
- Proyecto: originales de Alastor (3/4, frente, ícono): bloques facetados grandes, volumen hacia su izquierda, un
  rizo en «C» sobre la frente; ficha «cabello castaño rizado»; técnica aprobada de momento del pelo de Theo
  (arco SENKU + bloques + resortes, `docs/medicion/pelo_theo.py`).

## Marcas visibles
- Bloques facetados grandes (como Theo, pero romos), más volumen hacia su izquierda, un rizo en «C» que cae sobre la
  frente a su derecha, laterales cortos sobre la oreja; sin vista de espalda (se infiere: bloques hasta la nuca).

## Medidas (real → ALTH)
- No hay hoja de 3 vistas del original: sin arco SENKU; volumen paramétrico (como el pelo antes del arco) y comparación
  visual con la vista 3/4 y el frente (COMPARATIVA + revisor visual).

## Simplificación ALTH
- Mechones anchos y romos (no afilados como Theo), puntas redondeadas; el rizo se resuelve con un mechón que baja y
  se despega de la frente.

## Técnica
- La receta del pelo de Theo parametrizada (`docs/medicion/pelo_personaje.py`): misma base del cráneo y mismos
  mechones de cobertura; trazos propios de Alastor; color de paleta café; resortes por mechón.

## Revisiones CHXP
- `cobertura_pelo` ≥ 0.995, `pelo_resortes`, revisión visual contra los originales.

## Plan de prueba
- Máx. 3 iteraciones; GIF Walk/Run para ver el movimiento.

## Riesgos / dudas
- Sin espalda ni perfil del original: la nuca se inventa con la regla de cobertura (Admin la revisa).
