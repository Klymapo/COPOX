# Adán V30 · boca plana sin escalón en la quijada (SIN APROBAR)

- **Pedido de Admin (18 oct 2026):** en V29 se veía un desnivel en la mandíbula; primero mejorar el render para verlo, luego arreglarlo.
- **Resultado:** `ADAN_V30.glb`, SHA-256 `98454d28664bf1dc690dc78bfadb7c2f496c1d45d78a62a063ebf9a25718d29a` (en `Klymapo/copox-modelos`). Receta: `docs/medicion/receta_adan_v30.py ADAN_V22_HABLA.glb ADAN_V30.glb`, reproducible bit a bit (verificado).

## CHXP y SENKU nuevos

- `luz=juego`: el sol del visor de Godot (−40, −30, 0) con sombras proyectadas (mapa de profundidad desde el sol, sesgo grande como el de Godot) y normales del archivo. Calibrada contra el visor: zona al sol / zona de canto ≈ 1.7.
- Modo `quiebres`: mapa de calor de cambios bruscos de forma.
- `copox/medicion/quiebres.py`: pasa-altos de forma y de luz de juego en boca + quijada + comisuras contra la mejilla. PASS si la luz ≤ 2.5 × la mejilla.

## Causa del desnivel

Perfiles SENKU al centro: el relleno de V29 dejaba la piel casi vertical (normal Ny ≈ 0) hasta 1 cm debajo de la rendija y luego doblaba de golpe hacia la quijada (Ny −0.5). A los lados de la boca la piel natural baja suave. Con el sol del juego, la zona plana se iluminaba y el doblez hacía la "U" oscura; las marcas ")(" de las comisuras eran el mismo quiebre visto de lado.

## Arreglo

Se rellena el **residuo** z − g(x, y), donde g es la forma natural de la quijada ajustada en la piel a los lados de la boca (polinomio suave, error máx. 2.1 mm·u; congelado arriba de y = 0.565 para no marcar ondas en los cachetes). Lo plano sigue plano y la quijada conserva su curva. El pulido y el alisado de comisuras también trabajan sobre el residuo. Gestos (morphs) intactos.

## Medidas

| | V28 | V29 | V30 |
|---|---|---|---|
| quiebres · luz (boca/quijada) | 3.89 | 2.00 | **0.77** |
| quiebres · luz (comisuras) | 3.38 | 3.13 | **0.80** |
| quiebres · forma | 5.33 | 3.34 | **1.28** |
| veredicto | FAIL | FAIL | **PASS** |
| rugosidad reposo | 4.1 | 2.3 | **1.1** |

Con gestos (luz de juego): sonrisa 0.93, vis_A 1.05, vis_E 1.06, triste 0.90 (V29: 2.5–3.3).

## Probado y descartado

- Perfil por franjas con spline (mediana cada 3 mm): metía rayas horizontales en los cachetes.

## Pendiente

- Queda un brillo muy leve bajo el centro de la boca (no lo marca SENKU).
- Revisión visual y aprobación de Admin.
