# Adán V38 · antebrazo y muñeca según las referencias de Adán (SIN APROBAR)

**Pedidos de Admin (18 oct 2026):**
- "Podemos ir empezando a trabajar el antebrazo para editar las muñecas y mantener coherencia en las uniones."
- Puños más gruesos, "si al volver los dedos más gruesos llegamos a un mejor parecido con la mano con regla".
- Referencias nuevas de Adán (cuerpo, brazo, cabeza, torso, piernas y pies): `refs/personajes/adan/`.

**Decisiones de Admin:**
- Antebrazo "como la Hoja".
- Codo: "seguir la referencia nueva".

**Resultado:**
- `ADAN_V38.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v38.py ADAN_V22_HABLA.glb ADAN_V38.glb` (V37 + este paso).

## Qué cambió

1. **Codo 1.5 cm hacia el hombro** (`proporciones` tipo nuevo `mover_articulacion`).
   - El brazo se acorta y el antebrazo se alarga.
   - La muñeca y la mano no se mueven, así que la mano sigue llegando a la entrepierna.
2. **Perfil del brazo** (ancho y grueso, de la muñeca al codo y hasta 2/3 del brazo).
   - Medido en `adan-brazo-4-vistas.jpg`.
   - Escala absoluta tomada de `adan-cuerpo-4-vistas.jpg`, porque las dos hojas no coinciden: con la escala del largo de mano, el brazo de la hoja del brazo sale ~25 % más delgado que en la hoja del cuerpo.
   - La hoja del brazo da la forma; la del cuerpo da el tamaño.
   - El cambio se mezcla por peso del hueso y se desvanece hacia el hombro.
3. **Muñeca nueva.**
   - Se quitó el cono "Antebrazo", que estrangulaba la muñeca.
   - La muñeca ahora es parte de la superficie implícita de la mano (`mano_geo.muneca`): un cilindro elíptico que sale de dentro del último anillo del antebrazo y se funde con la palma.
   - Pesos: del antebrazo en la orilla, que pasan a los de la mano 6 mm después de la articulación.
   - Intentos descartados:
     - Un tubo aparte dejaba un escalón tipo manga.
     - El borde abierto de la palma formaba un labio.
4. **Palma.**
   - Más gruesa en la muñeca (×1.7), con el grueso extra hacia el dorso: la cara de la palma queda plana para los agarres.
   - Más angosta en la muñeca (0.72): la referencia del brazo y la mano con regla coinciden en esto.
5. **Agarre.**
   - El cálculo de contacto con la palma usa la palma real, no la muñeca, que en V38 es más gruesa.
   - Nuevos criterios: todas las falanges deben tocar y alejarse del pliegue de la palma cuesta.
   - El agarre de pistola V37 se conserva (índice en el gatillo, pulgar en el armazón).

## Medidas

- **SENKU `mano_silueta`:** ahora tiene la opción `punta_robusta`.
  - Antes se alineaba con un solo vértice de la punta del medio. Al cambiar la malla, ese vértice salta y la silueta gira ~1.5°, lo que mueve el IoU ±0.02 sin cambio real de forma.
  - Con la alineación robusta, la serie es consistente: V36 0.839 → V37 0.846 → **V38 0.857** (palma 0.938 · dedos 0.783 · pulgar 0.789).
- **Dedos más gruesos, probados y descartados:**
  - Gruesos ×1.12: IoU 0.842; ×1.25: 0.821.
  - Ovalados ×1.3: 0.842.
  - Según la condición de Admin, no se aplican.
- **Grosor del brazo de frente contra la hoja del cuerpo** (misma envergadura): V38 ≈ referencia una vez descontado el contorno blanco de la referencia.

## Pendiente

- **Picos del puño.**
  - Puños 82/80/30 y 78/72/25 dan los mismos picos.
  - No son las puntas de los dedos: es la piel del lado de la palma que se dobla sobre sí misma en los nudillos (límite del skinning lineal).
  - Necesita pesos o forma correctiva en esa zona.
- **Costura antebrazo–mano.** La muñeca ya sale del último anillo con el mismo radio y el borde tiene las normales de la mano. Queda una línea tenue, sobre todo en CHXP por la oclusión ambiental; en Godot apenas se ve.
- **Pose de apuntar.** La revisión independiente vio pliegues pequeños en el dorso de la muñeca: el giro lo hace la mano, no el antebrazo.
- **Malla de la mano: corregida en V38.** Desde V36 tenía las caras y normales hacia adentro; se veía bien sólo porque el material es de dos caras. Ahora el volumen con signo se revisa y la malla se voltea.
- **Anillo claro en la muñeca** en el plano amplio de Godot (ya existía en V37). No cambia con las normales ni con la orientación de la malla. Probablemente es la sombra de la cabeza sobre el antebrazo, con la mano al sol; falta confirmarlo.
- **Pronación.** Lo natural sería que el antebrazo hiciera la pronación al apuntar, no la mano.
- **Hombro y brazo superior.** Son la siguiente etapa; el perfil sólo llega a 2/3 del brazo.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v38/`)

- `hoja_v38_brazo.png`: referencia del brazo arriba, V38 abajo.
- `cuerpo_ref_v37_v38.png`: referencia del cuerpo, V37 y V38.
- `rq_cmp.png`: muñeca en Godot en la pose de apuntar, V37 arriba y V38 abajo.
- `godot_v38.png`, `disparo_zoom_v38.gif`, `disparo_amplio_v38.gif`: agarre y gatillo.
- Reproducible bit a bit (verificado).
- `punos_abc.png`: los tres puños probados.

## Corrección (18 oct 2026, durante V39)

El agarre que quedó dentro de `ADAN_V38.glb` NO tiene el pulgar en su contacto: está a 30.7 mm y penetra 4.3 mm. La receta resolvía el agarre con la mano intermedia (antes de la muñeca nueva). La prueba que había dado "pulgar en el armazón, 0 mm" se corrió sobre la mano final, fuera de la receta. En V39 el agarre se resuelve con la mano final.
