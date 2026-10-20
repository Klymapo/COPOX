# Brief · Gafas de pasta gruesa (Alastor)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- Chanel, *Optical size guide* (https://www.chanel.com/sa-en/eyewear/optical-size-guide/): ancho de lente 46–56 mm,
  puente (ej. 19 mm), varilla (ej. 140 mm); se leen en la varilla izquierda.
- Eye-est, fichas de armazones de acetato (p. ej. https://eye-est.com/products/garrett-leight-evan): acetato grueso,
  montura completa.
- Proyecto: originales de Alastor (`refs/personajes/alastor/originales/`): armazón negro rectangular grueso, puente
  bajo, varillas a las orejas;
  ficha «lentes de armazón grueso / gafas de pasta gruesa».

## Marcas visibles
- Dos aros rectangulares redondeados que enmarcan ojos grandes (cubren de la ceja al pómulo), puente corto, bisagras
  salientes en las sienes, varillas rectas hasta la oreja.

## Medidas (real → ALTH)
- Lo real (lente 50 mm, puente 19 mm) no escala a la cabeza chibi: manda el original (frente): cada aro ≈ el ancho del
  ojo + 25 %, alto ≈ 1.1× el ojo; grosor de pasta ≈ 0.0035 u; separación del rostro ≈ 0.004 u.

## Simplificación ALTH
- Aros como marcos de sección cuadrada redondeada (pocos lados), sin cristal (los ojos son el foco del estilo).

## Técnica
- Pieza rígida (`copox/medicion/gafas.py`): dos marcos + puente + 2 varillas; posición de los ojos medida en la
  malla (piezas de ojo de la base); pesos 100 % `Head`; nodo `ACC_GAFAS` intercambiable (KHR_node_visibility).

## Revisiones CHXP
- `sin_flotantes` (la pieza va unida en sí misma), `normales`, `paleta_alth` (negro cálido), revisión visual: no tapa
  la pupila ni atraviesa la ceja.

## Plan de prueba
- Con la ficha de Alastor; vistas frente/perfil/3/4; máx. 3 iteraciones.

## Riesgos / dudas
- Párpados/cejas animadas pueden tocar el aro en gestos extremos (se revisa en Blink/Talk).
