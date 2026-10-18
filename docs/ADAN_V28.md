# Adán V28 · boca, uniones, manos y movimiento (SIN APROBAR)

- **Resultado:** `ADAN_V28.glb`, SHA-256 `88377d998dd206a9a64f94b07d5d2280d57e05efde6ecaf5c1e9da73695018b5` (en `Klymapo/copox-modelos`, privado).
- **Receta:** `docs/medicion/receta_adan_v28.py ADAN_V22_HABLA.glb ADAN_V28.glb` → corre V25 → V26 → V27 → V28; reproducible bit a bit (verificado).
- Hecho el 18 oct 2026 en sesión directa, porque la tarea nocturna no tuvo acceso al repo privado (ver `docs/NOCHE_2026-10-18.md`).

## V26 · boca sin bultos (`receta_adan_v26.py`)

SENKU nuevo: `copox/medicion/rugosidad.py` = desviación de la curvatura en el anillo de la boca dividida entre la de la mejilla (1 = igual de liso que la mejilla).

| Gesto | V25 | V26 |
|---|---|---|
| reposo | 4.1 | 4.1 |
| boca_sonrisa | 8.7 | 6.8 |
| boca_lado_L | 8.8 | 4.8 |
| vis_E | 7.4 | 6.9 |
| vis_A | 8.9 | 9.6 |
| boca_o | 8.7 | 9.8 |

- Gestos viejos de boca (sonrisa, triste, tensa, o, abrir, soplar, lado L/R) rehechos con campos limpios: eran de V13 y hacían grumos en las comisuras.
- Deltas de todos los gestos de boca suavizados sobre la malla.
- Probado y descartado: aplanar los labios contra un ajuste local de la piel (el reposo empeoró de 4.1 a 8.4, quedaba un hundido arriba del labio).
- **Honesto:** el reposo no bajó. Lo que queda es el relieve propio del labio de arriba (la "cresta" que se ve en arcilla). Bajarlo más pide rehacer la topología de la boca, no solo mover vértices.

## V27 · uniones, manos y muñeca (`receta_adan_v27.py`)

SENKU nuevo: `copox/movimiento/uniones.py` (peor estiramiento y aplastamiento de aristas por pieza en cada clip).

- Pesos de piel repesados por cadena de huesos con rampas suaves en cada unión: hombro → brazo → antebrazo, muñeca, los 5 dedos (3 falanges), pulgar en una sola cadena (ya no se separa en pedazos), rodilla, tobillo y dedos del pie.
- Borde del puño metido dentro de la mano (el "aro" de la muñeca).

| | V26 | V27 |
|---|---|---|
| Peor estiramiento (74 clips) | ×4.46 | ×2.99 |
| Clips con estiramiento > ×3 | 33 | 0 |

- Pendiente: el aplastamiento en la axila sigue (aristas al 2–8 % con el brazo abajo). Viene de que el rig está en pose T; no se ve roto en los renders, pero si Admin lo nota, la solución es un hueso de corrección o pesos de volumen en la axila.

## V28 · movimiento (`copox/movimiento/locomocion.py`)

Clips hechos por código (sin Blender), en ejes del mundo y con "miras" (el hueso apunta a una dirección):

| Clip | Qué hace |
|---|---|
| `Walk-loop` 1.0 s | IK de dos huesos, pie plantado. Avanza **0.259 u/s** sin patinar (el tobillo de apoyo va a 0.259 ± 0.006). |
| `Run-loop` 0.6 s | IK con fase de vuelo, brazos doblados, torso inclinado. **0.834 u/s** (± 0.017). |
| `Jump` 1.0 s | Agacharse, impulso, aire (la cadera sube 0.20 del alto), caída, aterrizaje. |
| `Dash` 0.55 s | Arranque inclinado, piernas en tijera, brazos atrás, puños. |
| `Punch_R`, `Punch_L` 0.6 s | Guardia, golpe recto con giro de cadera, puños cerrados. |
| `PointFwd` 1.6 s | Brazo al frente, índice recto, demás dedos cerrados. |
| `Aim-loop` 1.2 s | Apuntar con pistola: derecha al frente, izquierda sostiene. |
| `Point`, `M31_4_Senalar`, `M34_5_Tableta` | Índice estirado de verdad. |

Godot (`copox/godot/movimiento/`):
- `ControladorAdan`: `mover(dir, corriendo)`, `saltar()`, `dash()`, `golpe("R"/"L")`, `senalar()`, `apuntar()`, `equipar(ruta_glb)`. Mueve al personaje a las velocidades medidas; con CharacterBody3D usa `velocidad_deseada`.
- `prueba_controlador.tscn`: caminar → correr → saltar → dash → parar → señalar → puñetazos → pistola y apuntar (GIF en capturas).
- Armas: `equipar()` pega el arma a la mano derecha con su nodo `AGARRE`.

## Pendiente

- Florete: falta su postura de guardia y ataque (el agarre funciona; la pose de esgrima no está hecha).
- Locomoción: está hecha por código; se ve correcta pero algo rígida. Pulirla a mano (o con capturas de referencia) le daría más vida.
- Giros y frenado: el controlador gira en el lugar; no hay clips de giro ni de frenado.
