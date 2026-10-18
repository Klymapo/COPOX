# Adán V31 · brazos más cortos — rediseño del cuerpo, paso 1: esqueleto (SIN APROBAR)

- **Decisiones de Admin (18 oct 2026):** rediseño pieza por pieza (esqueleto → manos → brazo → piernas → cadera → pies), referencia = Hoja de vistas (`refs/infografias/hoja-de-vistas-personaje.png`), pies descalzos con dedos y talón/tobillo detallados como uniones. Brazos: la mano llega a la entrepierna; brazo y antebrazo casi iguales.
- **Resultado:** `ADAN_V31.glb`, SHA-256 `6ff7a411945d6baed6d102884b211f786040aedf2893f1d2b3b7f5e7d5705d29` (en `Klymapo/copox-modelos`). Receta: `docs/medicion/receta_adan_v31.py ADAN_V22_HABLA.glb ADAN_V31.glb` (V30 aprobada + este paso), reproducible bit a bit (verificado).

## SENKU nuevo: `copox/medicion/cuerpo.py`

Proporciones en Hc (altura de la barbilla sobre el piso; en la hoja el pelo tapa la coronilla). Landmarks de la hoja leídos sobre rejilla (±0.015 Hc).

| medida (Hc) | hoja | V30 | V31 |
|---|---|---|---|
| hombro (altura) | 0.853 | 0.879 | 0.879 |
| entrepierna (altura) | 0.394 | 0.413 | 0.413 |
| hombro → muñeca | 0.324 | **0.452** | 0.334 |
| mano (brazos abajo) − entrepierna | −0.035 | −0.088 (rodilla) | +0.014 (entrepierna) |
| brazo / antebrazo | 0.9–1.25 (decisión) | 0.63 | 1.10 |

## Qué se hizo

- Solo el antebrazo se acortó, de 0.136 a 0.078 u, sobre su eje. La mano y los dedos se trasladaron rígidos: mismo tamaño y forma. El brazo de arriba no se tocó (0.086 u).
- Pesos por cadena rehechos (receta V27) sobre el brazo nuevo: sin esto el codo estiraba más (6 clips por encima de ×3).
- Cambiaron solo 1468 vértices (antebrazos y manos, |x| ≥ 0.215). Cara y morphs idénticos a V30. Rotaciones de los clips intactas; el agarre de armas se recalcula solo (marco del esqueleto en reposo).

## Uniones (SENKU, 82 clips)

| | V30 | V31 |
|---|---|---|
| estiramiento máx. | ×2.96 | ×2.96 |
| clips > ×3 | 0 | 0 |

## Pendiente

- Idle abre los brazos hacia afuera (la mano queda a 0.24 u del centro; en la hoja los puños van pegados al muslo). Ajuste de pose para después.
- Aim: con brazos cortos las manos se juntan frente al pecho; revisar al trabajar el brazo (V33).
- Siguiente: V32 manos (palma, pulgar con pinza, dedos redondos, membranas en U; tamaño del puño contra la hoja).
