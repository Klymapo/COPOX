# Adán V34 · manos, segunda ronda: proporciones contra la mano con regla (SIN APROBAR)

- **Resultado:** `ADAN_V34.glb`, SHA-256 `1b80f19624a2b3015652e7ef2755614f4eef798d7240f0d7106617fd538f6d5f`. Receta `docs/medicion/receta_adan_v34.py` (V33 + este paso), reproducible bit a bit.
- **SENKU nuevo:** `copox/medicion/mano.py`. Mide razones en pose T contra `refs/infografias/mano-con-regla.jpg`; los landmarks se leyeron sobre rejilla.

| razón | ref | V33 | V34 |
|---|---|---|---|
| ancho / largo de palma | 1.06 | 1.85 | 1.50 (chibi a propósito) |
| dedo medio / palma | 0.95 | 0.94 | 0.88 |
| ancho de dedo / palma | 0.23 | 0.23 | 0.23 |
| hueco / palma | 0.035 | 0.021 | 0.028 |
| índice / medio | 0.79 | 0.75 | 0.81 |
| anular / medio | 0.87 | 0.81 | 0.90 |
| meñique / medio | 0.62 | 0.49 | 0.59 |
| pulgar / palma | 0.81 | 1.26 | 0.97 |
| ángulo del pulgar | 43° | 73° | 73° (sin cambio) |
| mano − entrepierna (Hc, cuerpo.py) | −0.035 (hoja) | +0.014 | −0.026 |

## Qué se hizo

- Palma 30 % más larga: los vértices se estiran desde la muñeca y los dedos y el pulgar se trasladan rígidos.
- Dedos más largos sobre su eje, con el grosor igual: medio ×1.17, índice ×1.23, anular ×1.26, meñique ×1.30.
- Pesos por cadena rehechos.
- Solo cambiaron las manos (1176 vértices, |x| ≥ 0.291). Uniones: máx. ×2.96, 0 clips > ×3; los clips con aplastamiento < 0.25 bajaron de 69 a 67.

## Revisión visual independiente (agente revisor-visual-alth)

- **Mejora:** sí en la mano abierta (dedos más largos, escalonado legible). En las poses (puño, señalar, Idle) casi no cambia.
- **Defectos que quedan, por impacto:**
  1. El puño de Punch_R no es compacto: los dedos son bloques sueltos y las puntas asoman.
  2. La raíz del pulgar se cruza con la palma; el pulgar sale casi perpendicular (73° contra 43°).
  3. Idle: los dedos parecen garra en escalones duros.
  4. PointFwd: los dedos doblados se cruzan.
  5. Del dorso a los dedos hay un escalón recto, sin bisel de nudillos.
- **No tocar:** anchos y huecos de dedos, razones entre dedos, palma chibi.

## Siguiente

Pulgar (base y ángulo) y cierre del puño. Toca la pose de reposo del pulgar y las rotaciones de los clips de mano.
