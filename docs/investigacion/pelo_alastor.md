# Brief · Pelo castaño ondulado con mechón al frente (Alastor)

Fecha: 2026-10-19 (rev. 2, tras dos REHACER del revisor visual) · Brief válido: sí · Skill: investigar-referencias

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


## Revisión 2 (19 oct 2026, noche) · cambio de técnica — PARA APROBACIÓN DE ADMIN
**Por qué:** V01 y V02 (receta del pelo de Theo con parámetros romos) dieron REHACER: la técnica de mechones barridos
produce astillas y puntas en la coronilla, un «casco» con corte recto en la espalda y un rizo que se lee plano/suelto.
Eso no se arregla con parámetros (3 + 3 iteraciones).

**Técnica nueva — masas esculpidas:**
1. **5–7 masas redondeadas** (no mechones): cada una es un volumen implícito suave (superelipsoide/«gota» deformada por una
   curva guía) → marching cubes → simplificado a pocas caras grandes (facetas del estilo) → sombreado plano. Medidas y
   posiciones tomadas a mano de la vista 3/4 y del ícono (no hay hoja de 3 vistas del original):
   - **copete**: masa alta sobre la frente que sube y barre hacia SU izquierda; la más grande;
   - **lado izquierdo** (de él): masa que abulta hacia afuera sobre la oreja; **lado derecho**: más corta y pegada;
   - **coronilla**: masa que cae hacia atrás desde el copete;
   - **nuca**: 1–2 masas en escalón (no casco ni corte recto), terminan sobre el cuello del abrigo;
   - **rizo en «C»**: masa en forma de gancho que NACE del copete (unión suave, sin hueco), cae sobre la frente a su derecha
     y se despega en relieve (≈ 6–8 mm de la piel), visible en frente, 3/4 y perfil.
2. **Frente despejada**: ninguna masa cruza la frente por debajo de la línea del pelo (salvo el rizo).
3. **Base del cráneo** (la de V48.3) sólo como relleno interior para la cobertura (compuerta ≥ 0.995), oculta bajo las masas.
4. **Movimiento**: un hueso con resorte por masa grande (copete, lados, coronilla, nuca) con rigidez alta (el pelo es
   «de bloque», se mece poco); el rizo con resorte propio más suelto. Mismo `alth_resortes.gd`.
5. Color `marron_calido/5` (#4A3220); si en render se ve frío, `cabello_castano` (#72432B) — lo decide Admin viendo ambos.

**Revisiones:** cobertura_pelo, pelo_resortes, sin_flotantes (el rizo unido al copete), normales + revisor visual contra
`alastor-tres-cuartos.jpg` e `alastor-icono.png` (meta: APROBABLE o UNA_CORRECCIÓN). Máx. 3 iteraciones.

**Otros cambios de la misma ronda (no son técnica nueva):**
- Cara: quitar `parpado_enojo` (tapaba el iris; el ceño lo ponen las cejas), más `comisura_abajo` para boca recta.
- «Bigote»: NO es geometría: es la **sombra proyectada del aro inferior de las gafas** sobre la cara (se ve igual en el
  render crudo de Godot). Propuesta: las gafas no proyectan sombra (`extras.sin_sombra` → `cast_shadow = OFF` en CHXP y
  al importar en el juego) — decisión de Admin.
- Gafas: varilla continua hasta la oreja también en perfil; montura un poco más gruesa.
- Hebilla rectangular grande; solapas un tono más oscuro (`negro_calido/4` → `negro_calido/5`) para que se lean.
