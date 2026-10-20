# Brief · Abrigo largo de detective (Alastor Kleinteil)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- Gentleman's Gazette, *The Anatomy of a Suit Jacket* (https://www.gentlemansgazette.com/the-anatomy-suit-jacket/):
  solapa de muesca (notch) vs. pico (peak), ancho de solapa 6–10 cm (3½ in ≈ 9 cm lo usual), gorge a la altura del hombro,
  punto de abotonado (button stance), aberturas (vents), botones de manga, bolsillos con cartera.
- Bluprint, *Know the parts of a jacket* (https://www.mybluprint.com/post/know-parts-jacket/) y patente US2186918A
  *Overcoat* (https://patents.google.com/patent/US2186918A/en): abrigo = cuerpo + faldones hasta la rodilla, cuello,
  solapas, mangas con puño.
- Proyecto (Admin: «básate en los renders originales»): `refs/personajes/alastor/originales/` (3/4 de cuerpo
  completo, frente de la comparativa, ícono) y ficha «Alastor Kleinteil» (Drive): «abrigo largo café oscuro, corbata
  con nudo Windsor, zapatos boleados».

## Marcas visibles (originales)
- Abierto al frente: se ven camisa blanca, corbata negra, cinturón café con hebilla dorada y pantalón oscuro con vuelta ancha.
- Solapas anchas en V desde el cuello hasta el pecho (≈ a la altura de la axila), de un tono apenas más oscuro.
- Faldones en A hasta media espinilla, más anchos abajo; atrás cerrado y liso.
- Mangas rectas y anchas que terminan antes de la muñeca: asoma el puño blanco de la camisa (~1 cm de la hoja).
- Detalles (bolsillos con cartera inclinados, botones pequeños, presillas de manga): secundarios.

## Medidas (real → ALTH)
- Las medidas reales (solapa 9 cm, largo a la rodilla) sólo orientan: en chibi manda la hoja. Con SENKU (frente):
  faldón hasta la rodilla/media espinilla (≈ 0.12 u), ancho del faldón abajo ≈ 1.3× la cadera; solapa ancha ≈ 0.02 u;
  puño de camisa visible ≈ 0.01 u. Sin hoja de vistas del original: se valida visualmente (COMPARATIVA + revisor).

## Simplificación ALTH
- Volúmenes lisos (técnica del short / `ropa_tubos`), sin pliegues; solapas como placas con grosor; sin costuras.
- Bolsillos y botones: fuera en la primera versión (se agregan si Admin los pide).

## Técnica
- Camisa + pantalón + corbata del conjunto `traje_chaleco` sin chaleco (`CHA.usar = False`).
- Abrigo = tubo de la camisa inflado (cuerpo y mangas) ∪ faldón superelíptico que se abre hacia abajo; abertura
  frontal por función de ancho w(y); solapas `ropa_capas.placa`; tela `lana_cerrada`; pesos de piel visible.
- Cinturón: banda sobre camisa/pantalón en la cintura, hebilla como caja (color de paleta dorado).

## Revisiones CHXP
- `capas_visibles` (camisa/pantalón no se asoman por el abrigo), `senku_regiones`, `normales`, `sin_flotantes`,
  `paleta_alth`, triángulos, COMPARATIVA + revisor visual.

## Plan de prueba
- Base congelada; ficha `personajes/alastor.json`; `python -m copox.avatar … --rapido`; máx. 3 iteraciones.

## Riesgos / dudas
- Faldón largo + Sit/Run: atraviesa piernas al sentarse (se mide; sin simulación de tela en v1).
- Faldón y piernas comparten pesos: el faldón sigue a la pelvis y en parte a los muslos.
