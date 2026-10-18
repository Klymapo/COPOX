# Adán V36 · mano nueva de una sola pieza, con membranas (SIN APROBAR)

- **Decisión de Admin (18 oct 2026):** "Geometría. Tratemos de llegar al parecido con las referencias visuales".
- **Resultado:** `ADAN_V36.glb`, SHA-256 `446eb2ea76193c6b9d9d52174f71c553cad5023205256b8fb0ac2e229851cad8`.
  - Receta: `GODOT_BIN=… docs/medicion/receta_adan_v36.py ADAN_V22_HABLA.glb ADAN_V36.glb` (V35 + este paso).
  - Reproducible bit a bit (verificado). Necesita Godot 4.7.2 para simplificar.

## Qué se hizo

- **Mano de una pieza por lado** (`copox/medicion/mano_geo.py`). Superficie implícita alrededor de los huesos en reposo:
  - Palma: caja redondeada que se angosta hacia la muñeca; del lado del pulgar el borde va en diagonal hacia el índice.
  - Dedos y pulgar: cápsulas cónicas por falange.
  - Eminencia tenar.
  - La palma se funde con los dedos (membranas en "U", nudillos redondeados); los dedos no se funden entre sí.
  - Marching cubes (scikit-image, BSD) + Taubin.
  - Simplificación con meshoptimizer vía Godot (`copox/godot/herramientas/simplificar.gd`): ~145 000 → ~2 300 triángulos por mano.
- **Pesos por cadena** (regla V27) con rampas más cortas en dedos cortos. Se suavizan solo palma, nudillos y base del pulgar, sin mezclar un dedo con otro.
- **Se quitan las 7 piezas viejas por lado** (palma, 4 dedos, base y punta del pulgar). Las versiones anteriores quedan intactas.
- **Rig ajustado a la mano con regla** (`proporciones`: mover, rotar, escala_eje; claves conjugadas donde gira el reposo):
  - Dedos más juntos (espaciado ×0.86) y más delgados.
  - Abanico: índice −3°, anular +1°, meñique +5°. Largos: índice ×1.04, anular ×0.94, meñique ×0.92.
  - Pulgar: base 6 mm·u hacia los nudillos y 8 hacia afuera, huesos ×0.85, +6° hacia los dedos.
- **Puño:** falanges a 82/88/45° (V35 usaba 85/100/70°: con la mano de una pieza las puntas se metían en la palma).
  - En los clips que dejan el pulgar sin acomodar, el pulgar se acuesta sobre el puño, como en la Hoja de vistas.

## Medidas

- **SENKU nuevo** `copox/medicion/mano_silueta.py`: silueta de la palma contra `mano-con-regla.jpg`, alineada en la muñeca y la punta del dedo medio.
  - IoU total 0.83 · dedos 0.76 · palma 0.91 · pulgar 0.75.
  - `mano.py` (razones por piezas) ya no aplica a la mano de una pieza.
- **gltf-rig-guardian:** 56 huesos, 120 clips y 46 morphs, sin cambio. Primitivas 70 → 58 (14 piezas viejas fuera, 2 manos nuevas). Triángulos de las dos manos: 2008 → 4260.
- **Uniones:** fuera de las manos, sin cambio. En las manos, la membrana estira (p99 ×3.3, 1.7 % de las aristas > ×3; las aristas son de 0.5–1 mm). La métrica de ×3 se pensó para las piezas viejas.

## visual-critic (agente independiente, cada referencia por separado)

**Veredicto: ISSUES_FOUND** (antes INCOMPLETE).

- **R1:**
  - La forma general coincide.
  - Borde del meñique algo ancho y membrana pulgar-índice honda.
  - Costura en el dorso donde se une el pulgar.
- **R2:** los dedos van rectos en reposo (en R2 vienen algo flexionados); las cámaras no están calibradas.
- **R3:** el puño se ve compacto de perfil; de frente, las manos quedan algo chicas.
- **Peor:** puntas dentadas en puños, mejoradas después con el puño 82/88/45.

## Pendiente

- Costura del dorso en la base del pulgar.
- Membrana pulgar-índice menos honda.
- Puntas de los dedos en los puños más limpias.
- Tamaño de los puños de frente contra la hoja.
