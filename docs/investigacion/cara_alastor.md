# Brief · Cara propia de Alastor (variante de rostro sobre la base congelada)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- Originales de Alastor (`refs/personajes/alastor/originales/`: 3/4, frente de la comparativa, ícono): ceño fruncido,
  cejas gruesas en ángulo (bajan hacia el centro), boca recta y corta, sin rubor; ojos grandes cafés iguales a la base.
- Ficha «Alastor Kleinteil» (Drive): serio, metódico («su método es de manual llevado al extremo»).
- Base congelada: los 46 morphs faciales del rig (ceja_ceno_L/R, parpado_enojo_L/R, comisura_abajo_L/R, boca_tensa,
  boca_estrecha…) y el color por vértice COLOR_0 de la cabeza (el rubor es G/B < 1 en las mejillas).

## Marcas visibles
- Cejas: bloques gruesos y oscuros, inclinados hacia la nariz. Boca: una línea recta. Mejillas sin rosa.

## Medidas (real → ALTH)
- No aplica medida real: se miden en el original las proporciones relativas (cejas ≈ 1.4× más gruesas que las de la
  base; boca ≈ 0.8× de ancho) y se validan visualmente (revisor + COMPARATIVA).

## Simplificación ALTH
- Se conserva todo el rig facial: la variante es la POSE DE REPOSO de su cara, los morphs siguen funcionando encima.

## Técnica
- Admin eligió B (19 oct): cara propia del personaje. En el GLB de Alastor (copia de la base congelada; la base no se
  toca) se HORNEAN pesos de morph en la posición de reposo de las piezas de la cabeza (ceño, párpado de enojo leve,
  comisuras abajo, boca tensa/estrecha), se engrosan los bloques de ceja (CEJA_BLOQUE) y se quita el rubor (COLOR_0 → 1).
- Receta: `docs/medicion/alastor.py` → `cara()`; parámetros en la ficha (`ropa.params.cara`).

## Revisiones CHXP
- `base_preservada` (los 46 morphs siguen), `normales`, revisión visual: identidad sobria (checklist facial).

## Plan de prueba
- Vistas frente/3/4 + clip Talk/Blink en GIF si Admin lo pide; máx. 3 iteraciones.

## Riesgos / dudas
- Horneado + morph encima puede exagerar el ceño en gestos de enojo (se revisa con Admin).
