# Adán V32 · manos — rediseño del cuerpo, paso 2 (SIN APROBAR)

- **Resultado:** `ADAN_V32.glb`, SHA-256 `78b599dbfb948fc83e443711d1b6957385cafb4a2e4d72000f0c12ef166cc6b7`. Receta `docs/medicion/receta_adan_v32.py` (V31 + este paso), reproducible bit a bit.
- **Tamaño:** con los brazos abajo la mano mide 0.082 u de alto (puño de la hoja: 0.084). Se conserva.
- **Qué se hizo** (solo se movieron vértices; topología, pesos, UV y morphs intactos):
  - Dedos y pulgar: la sección pasó de prisma cuadrado a "cuadrado redondo" (superelipse n = 2.3). Puntas en domo romo; antes eran planas cortadas.
  - Palma: esquinas del contorno recortadas (superelipse n = 3) y dorso un poco abombado.
  - Normales suaves recalculadas por pieza.
- Solo cambiaron 618 vértices (|x| ≥ 0.292, solo manos), con un desplazamiento máximo de 6 mm·u. Uniones: máx. ×2.96, 0 clips > ×3 (igual que V31).
- **Pendiente:** membranas en "U" entre dedos (hoy los dedos son piezas aparte metidas en la palma; necesita geometría nueva) y la pose relajada de la mano en Idle (dedos en gancho).
