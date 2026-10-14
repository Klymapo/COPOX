# Alastor Delta y maniquí v0.2 · 14 oct 2026

Autor: Elio (Claude), sesión de Claude Code. Rama `propuesta-maniqui-hibrido` (no fusionar sin aprobación de Admin).

## Qué hay en esta rama

| Archivo | Qué es |
|---|---|
| `models/source/alastor/alastor_beta_juego.glb` | **Beta**: Alastor del juego (repo peso-de-los-nombres). Bloques, 56 huesos con dedos y huesos de faldones, 29 clips. |
| `models/source/alastor/alastor_gamma_30k_2k.glb` | **Gamma**: Alastor de Hunyuan3D (Tencent) optimizado con gltfpack, de 499,830 a 29,988 tris y texturas 2K. Una sola malla fundida, sin rig. |
| `models/source/alastor/alastor_beta_wrap_it4c.glb` | Intermedio: Beta con shrinkwrap por zonas y cabeza de Gamma. Lo usa `maniqui.py`. |
| `assets/alastor_delta/alastor_delta.glb` | **Alastor Delta**: cuerpo de Beta redondeado, más la cabeza, los faldones, el pantalón y los zapatos de Gamma. Rig y 29 clips de Beta. Silueta IoU 97.8 % contra Gamma (frente 98.1 · 3/4 97.3 · lado 97.4 · espalda 98.3). |
| `assets/alastor_delta/alastor_delta_v1_1_cuello.glb` | Delta con el cuello remodelado (pieza nueva bajo la mandíbula). IoU 97.2 %. |
| `assets/maniqui/maniqui_v0_2.glb` | **Primer avatar de la biblioteca**: gris, sin ropa, pelo ni lentes. Cabeza redonda, torso, brazos, piernas, manos con 5 dedos y pies generados sobre el esqueleto. 56 huesos, 29 clips, pesos válidos. |
| `assets/maniqui/maniqui_v0_7.glb` | **Maniquí v0.7**: v0.2 con cabeza canónica paramétrica (una sola pieza cerrada: bola medida de Gamma, cara aplanada, cuencas, nariz, boca, orejas) y cuello recto nuevo. Sin restos de Gamma en la cabeza. Rama `propuesta-cabeza-canonica`. |
| `assets/maniqui/maniqui_v0_8.glb` | **Maniquí v0.8**: cabeza ALTH medida de las referencias con `medir_cara.py` + `cabeza.py rasgos/alastor.json`: cajón redondeado (superelipsoide), mandíbula plana, nariz y orejas de bloque. Ver hallazgo de proporciones abajo. |
| `assets/maniqui/maniqui_v0_10.glb` | **Maniquí v0.10 (actual)**: v0.9 + pelvis de bloque (`Pelvis`, pesada a Hips con 45 % a cada pierna en el borde inferior), brazos 15 % más cortos por hueso (`huesos.py`, IBM recalculadas, 29 clips intactos), manos mitón (palma gruesa, dedos cortos y chunky). |
| `assets/maniqui/maniqui_v0_9.glb` | Maniquí v0.9: v0.8 + cuerpo de bloques redondeados: `loft()` usa sección superelipse (`P_BOX = 2.8`), torso 7 % más angosto, brazos y antebrazos de bloque (r 4.2 cm), palma más gruesa y dedos chunky, botas anchas de techo plano, barbilla sobre el torso (sin cuello visible). Cabeza al ancho medido (31.6 cm). |
| `assets/maniqui/ropa_alastor_v0.glb` | Ropa de Alastor en 10 piezas con el mismo esqueleto: pelo, lentes, gabardina (2), camisa, corbata, cinturón, hebilla, faldones+pantalón y zapatos. |
| `assets/*/previews/` | Vistas finales (no renders de iteración). |
| `tools/maniqui/` | Scripts y `run_pipeline.sh`. |

**Reproducibilidad verificada:** `bash tools/maniqui/run_pipeline.sh` regenera los cuatro exports idénticos byte por byte (SHA-256 iguales) en unos 40 s, en CPU, sin Blender ni GPU.

## Ejes y unidades

Estos GLB **no siguen la convención ALTH** (1 u = 1 mm, Z-up). Son glTF Y-up en metros, con altura de ~1.03 m como en el juego, pies en y = 0 y el frente hacia +Z. Si se meten a un cassette COPOX, el reference config debe declarar esos ejes.

## Cadena (ver `tools/maniqui/README.md`)

1. `wrap2.py`: shrinkwrap de Beta sobre Gamma **por zonas**. Gamma se clasifica por color de textura y cada pieza de Beta solo busca su zona. Luego se suaviza y se trasplanta la cabeza de Gamma al hueso `Head`.
2. `wrap3.py`: trasplanta de Gamma los faldones, el pantalón y los zapatos. Los pesos se copian del vértice más cercano de la pieza de Beta que reemplazan. → **Delta**
3. `neck.py`: borra el cuello de Beta y genera un cuello nuevo que nace bajo la mandíbula.
4. `maniqui.py`: separa pelo y lentes de la cabeza de Gamma. El pelo se detecta por color; los lentes, con los lentes de Beta como plantilla espacial, porque el atlas UV de Gamma no permite reconocerlos por color. Además pone un cráneo de bola y escribe el archivo de ropa.
5. `cuerpo.py`: genera el torso, los hombros con brazo superior y las piernas, como lofts de anillos sobre los huesos.
6. `manos_pies.py`: genera antebrazo, palma, 5 dedos por falange y pie con base plana.

Herramientas de control: `render.py` (4 vistas), `measure.py` (IoU de silueta contra Gamma), `pose.py` (posa un clip con skinning en numpy), `retex.py` (reescala texturas embebidas).

## Lecciones (para no repetir)

- **Shrinkwrap global no sirve**: la cara se pega a los lentes. Por zonas sí funciona, pero tiene techo en la vista 3/4 (94-95 %), porque los faldones y zapatos de Beta no tienen topología para abrirse como los de Gamma. Esas piezas se **trasplantan**, no se proyectan.
- **Corte de cuello en 0.55** de la altura. A 0.60 rebanaba la barbilla de Gamma y se veía el interior hueco de la cara.
- **Bulto en la nuca**: la ropa de Beta proyectada contra el pelo en sombra. Regla: la ropa solo busca objetivos por debajo del corte.
- **Gamma no tiene nada debajo de la ropa ni del pelo.** Beta tampoco tenía torso, brazos superiores ni piernas bajo la gabardina. El cuerpo del maniquí se **genera**, no se recorta.
- Los colores de la textura de Gamma no distinguen bien pelo en sombra de piel en sombra. Hay que combinar color, posición y geometría.
- Mis renders usan sombreado plano y exageran las facetas. **Validar en Godot** antes de juzgar.

## Hallazgo del 14 oct (tarde): la cabeza ALTH no es una bola, y el cuerpo Beta no está en proporción ALTH

`medir_cara.py` sobre `refs/personajes/joven-rubio-4-vistas.jpg` (frente) y `detective.jpg` (3/4) da: llenado de la caja de la cara 0.90-0.92 (una elipse daría 0.785), mandíbula 0.96-1.0 del ancho, radio de esquina 0.04-0.08 → **cajón redondeado**, no esfera. Ojos a 0.50 W sobre la barbilla, separados 0.58 W, de 0.32×0.30 W; nariz 0.23 W bajo el ojo, 0.21 W de ancho. Ancho de cara / altura total: 0.26 (Theo) y 0.32 (detective); barbilla al 49-55 % de la altura.

**Corrección (misma tarde):** medido el cuerpo de Theo (torso 0.25 de la altura, brazos 0.08 de grueso, span 0.84, piernas 0.12 de ancho), el cuerpo Beta ya está cerca de la proporción ALTH; la cabeza de 32 cm sólo *parecía* chica porque va calva: el pelo del estilo añade ~80 % de ancho. Cara/torso = 1.09 en Theo y 1.07 en el maniquí. Así que v0.9 usa el ancho medido y la ropa/pelo pondrán el volumen. Lo que sí estaba fuera de estilo era la **forma**: tubos y elipses en vez de bloques; v0.9 lo corrige con secciones superelipse. Hecho en v0.10: brazos acortados por hueso con `huesos.py` (span 0.92 → 0.85 de la altura).

La auditoría automática de la cabeza contra la referencia queda pendiente: no hay referencia frontal sin pelo; haría falta una máscara de pelo en `medir_cara.py` o una referencia calva.

## Pendientes (prioridad)

1. ~~Banda entre la ceja y la oreja del maniquí~~ **Resuelto en v0.7** (`tools/maniqui/cabeza.py`): se descartó la cabeza de Gamma completa. Tres intentos de conservar sus rasgos (recorte por cajas, parche continuo fundido, horneado por raycast) fallaron por los aros de los lentes fundidos en la malla y el ruido de la decimación. La cabeza ahora es paramétrica; los rasgos de cada personaje se ajustan con parámetros (separación de ojos, nariz, boca), no pegando malla. Pendiente: afinar esos parámetros para Alastor y bajar los 17k tris de la cabeza (SEG/RING) si Godot lo pide.
2. Probar Delta y el maniquí en Godot 4.7 (GL Compatibility): sombreado suave, costura del cuello, faldones con `SpringBoneSimulator3D`.
3. Gestos faciales: la cabeza de Gamma va rígida al hueso `Head` y los 16 blendshapes de Beta se perdieron. Plan acordado con Admin: ojos como textura deslizante (iris arriba = "ojos en blanco" de Theo), mandíbula con hueso y shape key de boca ("soplar café" de Alastor).
4. Manos y pies del maniquí son tubos lisos (funcionan con el rig, pero son primitivos). Pulirlos o sustituirlos por una mano canónica.
5. Licencia: Gamma proviene de Hunyuan3D (Tencent Community License, **excluye UE, Reino Unido y Corea del Sur**). Todo lo derivado de Gamma hereda ese riesgo. Plan B: regenerar con TRELLIS.2 (MIT) y correr la misma cadena.

## Continuación registrada · 14 oct 2026

PR #34 continuado desde v0.3 con tres candidatos hermanos r1/r2/r3 y evaluación real de cuatro vistas, acercamientos y poses. Se preservan originales, 56 huesos y 29 clips. r1/r2 rechazados por pérdida de triángulos protegidos; r3 conserva facciones/orejas, pero presenta defectos de unión y perfil IoU 94.78%. Estado **PLATEAU / NO APROBADO**, sin fusión. Detalle, criterios, límites y bitácora completa: [MANIQUI_V03_CONTINUACION_2026-10-14.md](MANIQUI_V03_CONTINUACION_2026-10-14.md).
