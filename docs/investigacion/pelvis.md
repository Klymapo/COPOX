# Brief · Pelvis anatómica para el cuerpo base (Adán V50)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- Proko, *Anatomy of the Pelvis* (https://proko.com/course-lesson/anatomy-of-the-pelvis/notes): cubeta inclinada,
  cresta ilíaca, espinas ilíacas anteriores (EIAS), línea inguinal EIAS→pubis, hoyuelos sacros (EIPS), pubis al centro
  vertical del cuerpo; pelvis masculina más alta y vertical.
- Voka 3D Anatomy, *Pelvis topography* (https://voka.io/?p=708): relación pelvis–fémur (trocánter mayor al lado).
- Referencias del proyecto: `refs/personajes/joven-rubio-4-vistas.jpg` (Theo), `refs/personajes/adan/`.

## Marcas visibles
- Borde superior (cresta ilíaca): al frente apenas un cambio de plano a la altura de la cintura baja.
- EIAS: dos puntos suaves al frente; de ahí baja la **línea inguinal** al pubis → la "V" de la ingle.
- Atrás: dos hoyuelos sacros y la masa del glúteo con su pliegue inferior; separación central suave.
- Lado: plano del trocánter donde entra el muslo.

## Medidas (real → ALTH)
- Ancho de cadera en la hoja de Theo y en Adán: SENKU (silueta de cuerpo) ya coincide en frente (IoU 0.85 vestido);
  no se cambia el ancho, se cambia la **forma**. Inclinación de la cubeta: 10–15° hacia adelante (Proko: inclinación
  anterior, masculina más vertical).

## Simplificación ALTH
- Sin detalle óseo; solo volúmenes: cubeta + V inguinal + glúteos. Mismo suavizado y facetado del torso.
- La V inguinal sustituye el aro de la pierna que se veía sin short (pendiente desde V49).

## Técnica
- Pieza implícita (como `_Pelvis` de V49) con: cubeta = superelipse inclinada; V inguinal = surco suave (resta suave
  de dos cuñas desde EIAS al pubis); glúteos = dos elipsoides en unión suave con pliegue inferior; trocánter = plano
  lateral. Unión suave con torso y piernas (sin costura); pesos Hips con mezcla a UpperLeg en el pliegue.

## Revisiones CHXP
- SENKU cuerpo (frente/perfil/espalda) ≥ valor de V49 (no empeora).
- Sin aro visible: la diferencia de normales a lo largo del borde muslo–pelvis sin short no excede la del torso.
- Poses Walk/Run/Sit: sin agujeros ni penetraciones pelvis–muslo (cuenta de triángulos invertidos en pose).
- base_preservada (clips, huesos, morphs), integridad, pesos, normales.

## Plan de prueba
- `docs/medicion/receta_adan_v50.py` (V49 → V50). CHXP V3 con y sin short, clips Walk/Run/Sit. Máx. 3 iteraciones.

## Riesgos / dudas
- El short y el pantalón se ajustan sobre la pelvis: se rehacen encima de V50.
