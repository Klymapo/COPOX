# Adán V39 · proporciones, torso con anatomía, hombros y brazos (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** "Podemos continuar con brazo, torso, hombros y muñeca? Además de los pendientes."

**Decisiones de Admin:**
- Torso: "seguir la referencia".
- Anatomía: "marcada".
- Grosor del antebrazo: "hoja del cuerpo".
- Proporciones verticales: "hacerlo todo ahora".

**Resultado:**
- `ADAN_V39.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v39.py ADAN_V22_HABLA.glb ADAN_V39.glb` (V38 + este paso).

## Medidas contra `refs/personajes/adan/adan-cuerpo-4-vistas.jpg`

Las alturas van en fracción del eje del brazo al piso; el eje del brazo queda fijo.

| | Referencia | V38 | V39 |
|---|---|---|---|
| Cintura del short | 0.361 | 0.232 | 0.361 |
| Entrepierna | 0.573 | 0.508 | 0.566 |
| Dobladillo | 0.689 | 0.615 | 0.689 |
| Torso de frente bajo la axila / cintura (÷ envergadura) | 0.256 / 0.233 | 0.313 / 0.299 | 0.246 / 0.229 |
| Fondo del torso (÷ envergadura) | 0.18–0.21 | 0.17–0.18 | 0.19–0.20 |
| Brazo de frente, del 40 al 70 % (÷ envergadura) | 0.090–0.106 | 0.079–0.091 | 0.091–0.100 |

## Qué cambió

1. **Esqueleto.**
   - La entrepierna baja 2.8 cm y el tronco, de Spine para arriba (brazos y cabeza), no se mueve.
   - Las piernas miden ×0.83, repartido entre muslo y espinilla.
   - Los pies no cambian: su etapa es aparte (dedos, talón, tobillo).
2. **Short.**
   - La cintura baja a la de la referencia.
   - La boca del short abraza al torso nuevo (1.2 cm más ancha que la cintura, como en la referencia).
   - El dobladillo baja 1.6 cm.
3. **Torso nuevo** (`copox/medicion/torso_geo.py`). Superficie implícita con el perfil medido y anatomía marcada:
   - Pectorales con pliegue inferior, esternón, abdomen en 3 filas, línea alba y ombligo.
   - Clavículas, omóplatos y columna. La columna va como surco por desplazamiento, para que no se corte entre los omóplatos.
   - Deltoides y trapecio, que terminan dentro del brazo y del cuello.
   - Pesos transferidos de la piel vieja y suavizados, con dos reglas:
     - El cuello sólo pesa en la orilla de arriba (desde y 0.470).
     - Hombro y brazo sólo pesan cerca del brazo (|x| > 0.09), como en V38.
   - Omóplatos bajos y trapecio suave: con la luz de arriba de Godot se leían como arrugas en la espalda.
   - Antes el torso tenía 170 triángulos; ahora ~5 600.
4. **Brazos.** Antebrazo y codo ×1.13 (hoja del cuerpo); se desvanece hacia el hombro.
5. **Pendientes de V38.**
   - **Pronación.** Al apuntar, la mitad del giro de la mano lo hace el antebrazo (`Clip.pronacion`), así la muñeca no se tuerce.
   - **Anillo claro en la muñeca:** confirmado como sombra de la cabeza. Sin sombras, el antebrazo y la mano tienen el mismo tono. No es la malla.
   - **Puño.**
     - Se agregaron pliegues del lado de la palma en las articulaciones de los dedos y rampas de pesos más suaves en el nudillo.
     - Los picos bajan un poco pero no se van. No vienen de la piel que se dobla adentro sino de la membrana entre la palma y los dedos y de las puntas metidas en la palma.
     - Solución propuesta: forma correctiva del puño (shape key) para la siguiente ronda.
   - **Agarre de la pistola.** Se resuelve con la mano FINAL; en V38 se resolvía con la intermedia y el pulgar quedaba a 30 mm.
     - El pulgar se apoya en un tramo del armazón (`CONTACTO_Thumb` → `CONTACTO_Thumb_fin`), no en un punto.
     - Criterio nuevo: los dedos que rodean deben cerrar ≥ ~90° en total.
     - Resultado: índice a 1.5 mm del gatillo, pulgar en contacto (0 mm, sin penetración) y medio, anular y meñique a 34–69°.
6. **SENKU `mano_silueta` (punta robusta):** 0.857, igual que V38. Los pliegues no cambian la silueta.

## Pendiente

- **Puño:** forma correctiva.
- **Piernas y cadera.** La referencia tiene las piernas más juntas y el short de la cadera más angosto.
- **Pies.** Más bajos en la referencia: tobillo a 0.842 contra 0.803.
- **Cabeza.** Aprobada en V33, pero la referencia nueva la tiene algo distinta arriba. No se tocó.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v39/`)

- `hoja_v39.png`: referencia arriba y V39 abajo, en 4 vistas.
- `torso_cerca.png`, `espalda.png`: anatomía.
- `godot_v39.png`, `disparo_zoom_v39.gif`: agarre, gatillo y pose de apuntar con pronación.
- `anillo_sombra.png`: la muñeca con y sin sombras.
- `puno_rampas.png`: el puño con las tres rampas probadas.
