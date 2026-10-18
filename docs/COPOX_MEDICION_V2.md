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
