# COPOX · Motor de medición v2

17 oct 2026 · Elio (Claude) · Propuesta, sin fusionar.

## Para qué

Medir un personaje 3D contra sus referencias **imitando la pose y la cámara de cada render**. Las referencias no se corrigen: se reproducen. La meta es que el GLB, puesto igual y fotografiado igual, se vea como la referencia.

## Qué cambia frente a `alth_character_audit.py`

| Antes | Ahora (`copox/medicion`) |
|---|---|
| trimesh + scipy | Solo NumPy + Pillow |
| Malla en reposo; sin poses | Skin + morphs en cualquier clip/tiempo (`gltf.Modelo.posar`) |
| Escala por alto de la silueta (el pelo la descuadra) | Unidad **ED** = distancia entre ojos; anclas de ojos y de suelo |
| Ortográfica; 3/4 fijo a 45° | Cámara con yaw, elevación, roll y perspectiva opcional (`camara.Camara`) |
| Silueta binaria | Mapa por clases con la paleta ALTH (pelo, piel, claro, oscuro, azul), igual para referencia y modelo |
| Regiones en cajas fijas que presuponen proporciones | Perfiles de ancho por altura y puntos detectados (ojos, entrepierna, pies, cabeza) |
| Puntos del modelo por nombre de nodo | Puntos detectados en el render, igual que en la referencia |
| — | Búsqueda de pose + elevación + distancia que mejor imita la toma |

## Uso

```
python -m copox.medicion.comparar manifiesto.json --salida evidencia/ --base carpeta/
```

El manifiesto lista el GLB, las poses candidatas, elevaciones, distancias y referencias (imagen, recorte, yaw o lista de yaw, ancla). **Un manifiesto por hoja.** Las vistas de una misma hoja comparten escala, pose y línea de suelo; una imagen distinta va en otra corrida.

Salida:
- `reporte.json`: ajuste, búsqueda completa, IoU por clase, medidas y perfil de anchos por vista.
- `lamina_<vista>.png`: referencia | modelo | clases del modelo | diferencia.

## Pruebas

`python -m unittest tests.test_medicion_v2`: cámara, paleta, hueco encerrado, ojos contra ceja, perfiles y render de un cubo sintético.

## Límites

- La clasificación por color asume la paleta plana ALTH; en fotos reales no aplica.
- El ajuste de cámara es una búsqueda en rejilla (pocos valores), no una optimización continua.
- La referencia está vestida y el modelo base no: las brechas mezclan cuerpo, ropa y pelo. El reporte las separa por clase, pero la interpretación es humana.
- El rasterizador es CPU en Python: unos 4 min por hoja con búsqueda completa y unos 30 s con cámara fija.
- IoU y anchos no prueban parecido; la revisión de Admin sigue siendo el filtro final.

## Actualización · edición de proporciones (17 oct 2026, tarde)

- `copox/medicion/proporciones.py`: edita proporciones por huesos en un GLB con skin.
  - Mueve huesos y vértices con la mezcla de pesos.
  - Escala segmentos a lo largo de su eje (manos) y escala solo vértices (cuello).
  - Acorta piernas manteniendo los pies en el piso.
  - Recalcula traslaciones locales, inverseBindMatrices y normales.
  - Desplaza las claves de traslación animadas para que los clips sigan siendo válidos.
- `comparar.py`:
  - Margen de fondo alrededor de cada panel; antes el modelo se recortaba y la medida de la suela se pegaba al borde.
  - Ancla horizontal opcional `"ancla_x": "cara"` (punta de la cara) para perfiles; el centro de cabeza con pelo sesgaba la postura.
  - Guarda los mapas de clases (`clases_<vista>.npz`) y las anclas en el reporte.
- Recetas usadas con Adán: `docs/medicion/ediciones_v07.json`, `docs/medicion/ediciones_v08.json`. Manifiesto: `docs/medicion/manifiesto_hoja_theo.json`.
- Los GLB no se suben al repositorio público.

## Renderizador v1 y compactador (17 oct 2026, noche)

- `copox/render/`: renderizador para Elio y Argos (NumPy + Pillow). Instrucciones: `copox/render/LEEME_IA.md`.
  - Rasterizador vectorizado con capas por píxel; modos color, arcilla, malla, normales, curvatura, clases y clases_tri.
  - Vistas guardadas y códigos de vista; sello con modelo, hash, vista, modo, autor, fecha y código.
  - Láminas contra referencia (ancla ojos → suela) y A/B entre versiones.
  - Descarta caras traseras como Godot.
  - Medido en Theo V03 (≈90 mil triángulos): 0.1–0.3 s en `clases`, 0.6–1.1 s en modos con luz a 512 px, 2–4.5 s a 1024 px. El render anterior tardaba ≈6.5 s por vista en `clases`.
  - Concordancia con el render anterior (`clases_tri`, sin descarte de caras): 100% de píxeles iguales en 6 vistas de Adán V10 y 6 de Theo V03.
- `copox/medicion/compactar.py`: quita datos huérfanos que dejan las ediciones. Adán V10 24.0 → 7.9 MB; Theo V03 35.2 → 7.9 MB; 112 clips × 5 tiempos idénticos (diferencia 0.0) y texturas iguales.
- Pruebas: `python -m unittest tests.test_render`.

## Nombres y likeness de rostro (17 oct 2026, noche)

- Nombres de Admin: **CHXP** = renderizador (`copox/render`); **SENKU** = motor matemático (`copox/medicion`).
- `copox/medicion/orientar.py`: detecta piezas con caras invertidas (volumen con signo) y las voltea (orden de triángulos y normales). En Adán: 22 piezas de brazos, piernas y manos, más 2 del short. Se excluyen la cavidad de la boca y las placas doubleSided.
- `copox/render/rostro.py`: render del rostro en el marco de SENKU (ojos en u = ±0.5 ED, 40 px/ED) y lámina contra los parches de referencia `R_*/P_*`.
- `ocultar` en los códigos de vista acepta también nombres de material.
- Receta `docs/medicion/receta_theo_v05.py`:
  - Ojos: forma ancha, iris alto y oscuro, brillo único y párpado grueso.
  - Cejas: barra levemente inclinada, 0.08 ED más abajo.
  - Nariz: ×0.72 de ancho y ×0.65 de saliente.
  - Rasgos de Theo: cara baja −9 % y media sonrisa.
  - Con `--solo-estilo` aplica solo el canon de estilo (para Adán).
- IoU de rasgos en el marco SENKU (oscuro: ojos, cejas, boca), Theo V03 → V05:
  - R_15: 0.415 → 0.482
  - R_1: 0.352 → 0.439
  - R_0: 0.345 → 0.443
  - Esclerótica (claro): de ~0.09 a ~0.28.

## Rostro y cabeza, segunda pasada (Theo V06, Adán V13)

- CHXP:
  - `sombreado=archivo` usa las normales guardadas en el GLB, como Godot.
  - Lee `COLOR_0` (multiplica el color base en espacio lineal).
  - `render_rostro(..., px=)` permite el marco SENKU a más resolución.
- Hallazgo con `sombreado=archivo`: desde V09 (Adán) y V01 (Theo), las ediciones de rostro dejaban normales viejas. ~3,800 vértices de la cara con más de 45° de error; en Godot se verían "labios fantasma" y pliegues falsos.
  - `Editor.recalcular_normales` las rehace con el mismo criterio que el original.
  - V06/V13: 0 vértices con error.
- `Editor.color_vertices`: rubor en mejillas y nariz más rosada con `COLOR_0`. Hay que verificar en Godot que el material use el color de vértice.
- Receta `docs/medicion/receta_theo_v06.py` (sobre V05; `--solo-estilo` para Adán):
  - Boca: +0.05 ED arriba y ×1.12 de ancho, con labios e interior movidos por el mismo campo.
  - Sonrisa de lado.
  - Cara baja aplanada, sin papada.
  - Fondo negro de la boca y materiales de dos caras (boca y gorro de pelo).
  - Rubor y normales.
- Se probaron y descartaron por medición:
  - Cejas más gruesas: IoU de rasgos 0.453 → 0.441.
  - Costados de la cabeza más angostos: IoU de piel de la cara baja 0.738 → 0.718.
- Theo V06 contra R_15, R_1, R_0 y el acercamiento de la Hoja (media de las 4):
  - Rasgos oscuros: 0.453 (V03 0.365).
  - Esclerótica: 0.283 (V03 0.089).
  - Piel de la cara baja: 0.738.
- Huecos visibles en 48 tomas de cabeza: de 7,420 px (V05) a 944 (V06); 0 en la boca.

## Pómulos y orejas (Theo V07, Adán V14)

- Pedido de Admin: «pómulos muy marcados, orejas sumidas». Receta `docs/medicion/receta_theo_v07.py`:
  - Costados del cráneo y pómulos: ancho máximo de 1.28 a 1.12 ED en v −0.2…0.6, para costados rectos como en las referencias.
  - Frente de las mejillas hacia una superficie suave, más suavizado laplaciano.
  - Orejas: misma posición externa, cara interna estirada hasta el cráneo. Sobresalen ≈0.33 ED en vez de ≈0.17, y llevan un panel interior más oscuro (COLOR_0).
  - Mandíbula ×1.08 (solo Theo).
- Theo V07: rasgos oscuros 0.460 (V06 0.453); piel de la cara baja 0.731 (V06 0.738).
- Techo realista: las referencias entre sí coinciden en piel 0.75–0.93 y en rasgos 0.53–0.78 (R_15 vs R_1/R_0). Un IoU de 1.0 contra todas a la vez no es alcanzable; la meta útil es acercarse a ese techo.
