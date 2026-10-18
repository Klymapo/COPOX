# Adán V37 · manos ajustadas + base de agarre de objetos + pistola con gatillo (SIN APROBAR)

- **Pedidos de Admin (18 oct 2026):**
  - "Adelante con lo que falta" (sobrantes del visual-critic V36).
  - "¿Podemos ver un zoom hacia el trigger del arma? ¿Pasa el dedo por el gatillo? ¿Una animación de Adán apretándolo?"
  - "Podemos modificar el arma. Pero sí me gustaría tener bases para sostener algo así de complejo."
- **Resultado:** `ADAN_V37.glb`, SHA-256 en `copox-modelos/adan/SHA256SUMS`.
  - Receta: `GODOT_BIN=… docs/medicion/receta_adan_v37.py ADAN_V22_HABLA.glb ADAN_V37.glb` (V36 + este paso).
  - Pistola: `python -m copox.armas.armas_alth SALIDA` (los GLB de armas no se versionan; salen del código).

## Mano (sobrantes V36)

- Mano ×1.08 (huesos y radios): el puño de frente se veía chico contra la Hoja de vistas.
- `mano_geo.Diseno(canto_fijo=True)`: el ancho de la palma ya no aplasta el radio del canto (quita la costura del dorso del pulgar).
- `membrana_pulgar`: cápsula fundida entre pulgar e índice (la membrana que faltaba).
- SENKU `mano_silueta`: IoU total 0.851 (V36: 0.83) · dedos 0.784 · palma 0.922 · pulgar 0.789.
- Pendiente: puntas de los dedos todavía con picos en el puño.

## Base para sostener objetos (`copox/movimiento/agarre.py`)

**Contrato del objeto (GLB):**
- `AGARRE`: marco de la palma (+y del meñique al índice, +x hacia donde apuntarían los dedos estirados; origen = centro del mango).
- `CONTACTO_<Dedo>`: punto donde debe quedar la yema de ese dedo (puede colgar de una pieza móvil).
- Piezas móviles (p. ej. `GATILLO`) con `extras.recorrido_rad`.

**Solucionador `AgarreCierre`** (determinista, sin IA):
1. SDF del objeto (vóxeles de 0.6 mm).
2. Colocación en rejilla (a lo largo de los dedos, del mango y un giro sobre la palma). En cada candidato el objeto se apoya en la palma por bisección: la palma nunca lo atraviesa.
3. Cada dedo que rodea se cierra hasta tocar. Cuando una falange toca, se congelan esa articulación y las anteriores; las siguientes siguen cerrando, así el dedo envuelve. Piel blanda: hasta 2.5 mm.
4. Dedos con contacto (índice → gatillo): rejilla 2D más afinado acotado.
5. Pulgar: rejilla de oposición más cierre hasta contacto.
6. Acción: la pieza móvil recorre su ángulo y el dedo de contacto la sigue cuadro por cuadro.

El solucionador viejo (`Agarre`, Powell de 16 parámetros) queda en el archivo. Se descartó porque caía en mínimos locales: dedo medio a 18° y dedos rectos atravesando el arma.

**En el personaje** (`escribir_en_personaje`):
- Nodo `AGARRE_<NOMBRE>`, hijo de la mano.
- Clips `<Nombre>_Agarre-loop` y `<Nombre>_Accion`.
- Extras con los tiempos y ángulos de la pieza móvil.

**En Godot:**
- `ControladorAdan.equipar(ruta, "Pistola")`, `disparar()`, `desequipar()`.
- `BancoMovimiento`: capa de la mano derecha filtrada sólo a los huesos de los dedos, con `mano_derecha(clip)` y `mano_accion(clip)`.
- El gatillo se mueve en sincronía, sin tweens.

Resultado con la pistola:
- Penetración de la palma: 0.
- Yema del índice a 0.96 mm del gatillo.
- Medio, anular y meñique a 55/55/69°, 53/53/40° y 45/45/34° (proximal/intermedia/distal).

## Pistola (cambios)

- V2: gatillo y guardamonte 1 cm más cerca del mango; guardamonte más alto por dentro (el dedo chibi mide 2 cm de grueso).
- V3: empuñadura más delgada (±0.8 cm, antes ±1.6) y menos profunda (3.3 cm, antes 4.3). El frente queda igual.
  - Por qué: los dedos chibi miden la mitad que los reales y no podían rodear un mango de ~15 cm de perímetro.
- Clip `Pistola_Apuntar` (canal `orienta` de `locomocion`): el arma queda vertical al apuntar.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v37/`)

- `hoja_v37_disparo.png`: plano amplio, gatillo en reposo y apretado.
- `disparo_zoom.gif`: el índice dentro del guardamonte jalando el gatillo.
- `disparo_amplio.gif`: Adán apuntando y disparando.
- `zoom_lamina.png`: cuatro ángulos del agarre.
