# Adán V35 · manos, tercera ronda: pulgar y puños (SIN APROBAR)

- **Decisión de Admin (18 oct 2026):** sombreado suave (no facetado). Usar las skills de Argos (rama `propuesta/g2c-advancing-front-skills`, sin fusionar): rig-architect, motion-lab, gltf-rig-guardian y visual-critic.
- **Resultado:** `ADAN_V35.glb`, SHA-256 `e9a08ea2c8570e0453588fd8632607032b5ccda9ba8fa877c0e5added971a43c`. Receta `docs/medicion/receta_adan_v35.py` (V34 + este paso), reproducible bit a bit.

## Qué se hizo

- **Pulgar (rig-architect):** gira 30° en el plano de la palma hacia los dedos, alrededor de la cabeza del metacarpo, con sus vértices. SENKU `mano.py`: ángulo 73° → 43° (ref 43°).
  - Herramienta nueva en `copox/medicion/proporciones.py`: edición `rotar` y `conjugar_claves`.
  - Las claves del pulgar en todos los clips se conjugan (q' = R q R⁻¹, 291 canales): cada pose queda igual pero girada como el reposo. El pulgar ya no sale como palo en Idle.
- **Puños (motion-lab):** en cada clip y cuadro, la curva del proximal decide cuánto puño hay. Los dedos que ya cerraban (≥ 35°) se llevan juntos a 85/100/70°; los gestos de mano abierta (< 15°) no se tocan. 1044 canales.
- Pesos por cadena rehechos.

## gltf-rig-guardian

V34 → V35: 56 huesos, 120 clips, 46 morphs y 70 primitivas (sin cambio).

## Uniones (SENKU)

- Estiramiento máx. ×2.96, 0 clips > ×3 (igual).
- Clips con aplastamiento < 0.25: de 67 a 78. Es el pliegue del nudillo cerrando en los puños. Los peores siguen siendo las axilas (preexistente).

## visual-critic (agente independiente, cada referencia por separado)

- **R3, Hoja de vistas (puños a los lados): ISSUE.** El puño de Idle y M31_3_Puno no se cierra en bloque: las puntas asoman y las falanges se leen como piezas.
- **R1 y R2, mano con regla: UNDECIDED.** Faltan renders con la cámara alineada (palma de frente e isométricas).
- **Veredicto técnico:** INCOMPLETE (no es aprobación).
- **Nota propia:** en la lámina de cuerpo entero contra la hoja (`hoja_v35_manos.png`) las manos ya se leen como puños a los costados, como en la hoja; de frente se ven más delgados que los de la hoja.

## Pendiente

- Puño compacto de verdad: los dedos son piezas separadas metidas en la palma. Cerrarlo en bloque pide geometría (membranas en U, unir dedos a la palma) o un morph de "puño", no solo rotaciones.
- Renders alineados a R1/R2 y manifiesto `copox.visual.critic` con máscaras.
