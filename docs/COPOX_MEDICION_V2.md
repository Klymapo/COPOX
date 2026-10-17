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
