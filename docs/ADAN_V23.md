# Adán V23 · rostro expresivo (SIN APROBAR)

- **Base:** Adán V22 HABLA (`df8d4b96…`). **Resultado:** `ADAN_V23.glb`, SHA-256 `2eb31991d70e12a923c6180e767623846d98bf76a1ee37540b07c830e7a02e07` (no se sube al repo).
- **Receta:** `docs/medicion/receta_adan_v23.py` (`python receta_adan_v23.py ADAN_V22_HABLA.glb ADAN_V23.glb`, ~3 s).
- **Motivo:** las pruebas de movimiento (`docs/PRUEBAS_MOVIMIENTO_2026-10-17.md`) mostraron el párpado como parche de piel con ruido, una boca casi muda y cachetes sin control.

## Qué cambia

**Párpados (por ojo, tres capas que copian la curvatura de la placa del ojo):**
- Pestaña 3D, material nuevo `PESTANA_ALTH` del mismo color que la banda pintada. En reposo queda plegada y se ve la banda de la textura (el reposo es igual a V22). Al cerrar baja y se vuelve un arco grueso: el ojo cerrado chibi.
- Piel superior e inferior que se despliegan delante de la placa (1.0–1.8 mm·u). Ya no hay ruido de pixeles.
- Se retiran las piezas viejas del párpado (plegadas dentro de la cabeza) y la placa del ojo deja de deformarse.

**Controles de cara (morphs; 26 → 42):**

| Control | Qué hace |
|---|---|
| `parpado_L/R` | Cierre completo, con línea de pestaña (redefinido). |
| `alegre_L/R` | Párpado inferior en arco: ojo feliz (redefinido). |
| `parpado_inf_L/R` | Párpado inferior recto: entrecerrar, sospecha. |
| `parpado_enojo_L/R` | Párpado superior en diagonal, más bajo por dentro. |
| `parpado_triste_L/R` | Párpado superior en diagonal, más bajo por fuera. |
| `cachete_inflar_L/R` | Infla el cachete. |
| `cachete_subir_L/R` | Sube y adelanta el cachete (sonrisa grande); no toca el ojo. |
| `comisura_arriba_L/R`, `comisura_abajo_L/R` | Cada esquina de la boca por separado (sonrisa de lado, mueca). |
| `boca_ancha`, `boca_estrecha` | Ancho de la boca. |

Se usaron morphs y no huesos nuevos: la cara es una sola malla pesada al hueso `Head`; los morphs se ven igual en Godot, CHXP y Blender, se mezclan con las animaciones existentes y no obligan a repesar la cabeza aprobada.

**Expresiones G23–G26:** las 20 ahora también usan los controles nuevos (tabla `EXTRA_G` en la receta): sonrisas con comisuras y cachetes, sospecha y fastidio con párpado inferior, amenaza y determinación con párpado de enojo.

## Verificación

- Reposo contra V22 (CHXP, 512 px): 99 pixeles distintos en el primer plano de cara (pliegues de 0.3 mm), 25 en cuerpo completo.
- Godot 4.7.2: las 24 caras, la escena de prueba con parpadeo y mirada, sin advertencias del banco.
- Capturas: `capturas/2026-10-17/ADAN_V23/elio/` (rama `capturas`).

## Pendiente conocido

- En el borde del párpado inferior queda una línea finísima (se lee como pestaña inferior); en algunas expresiones asoma una astilla blanca en la esquina.
- La boca sigue siendo una línea fina: los gestos se leen, pero con poca amplitud. Un rediseño de labios sería un paso aparte.
- Theo V16 (mismo cambio sobre Theo V15) no se ha construido.
