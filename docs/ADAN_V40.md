# Adán V40 · torso suave y manos intercambiables de bloques (SIN APROBAR)

**Pedido de Admin (18 oct 2026):**
- Conservar la silueta del torso de V39, pero sin músculos definidos, como en la referencia.
- Brazos y manos como en las referencias, sin separación visible entre la mano y el brazo.
- Trabajar las manos aparte, iguales a las referencias, y unirlas con el mismo radio de muñeca.
- Para sostener objetos: un asset por objeto, intercambiando manos.

**Decisiones de Admin:**
- Torso: "pecho suave + clavícula".
- Manos: "bloques redondeados, suave".
- Juego inicial: abierta relajada, puño y señalar.
- Las manos van en el archivo de Adán.
- La hoja del brazo y la del cuerpo no coinciden en el tamaño de la mano contra el antebrazo. Decisión: "manos más grandes" (×1.3), para igualar el antebrazo de V39.
- La mano con pistola se hace después de aprobar las manos base.
- Manos de bloques: "así van". En reposo (Idle), mano abierta relajada aunque el clip traía puños (`MANO_FIJA`).
- Después de V40: piernas, cadera y short.

**Resultado:**
- `ADAN_V40.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v40.py ADAN_V22_HABLA.glb ADAN_V40.glb` (V39 + este paso).

## Qué cambió

1. **Torso suave** (`rasgos_suaves`). La misma superficie y el mismo perfil de V39, pero sólo con cuatro rasgos:
   - Un pecho que apenas se lee como plano.
   - La clavícula insinuada.
   - Deltoides y trapecio suaves.
   - Sin abdomen, línea alba, omóplatos ni surco de la columna.
2. **Manos de bloques** (`copox/medicion/mano_bloques.py`).
   - Superficie implícita medida en `adan-brazo-4-vistas.jpg`:
     - Palma en losa redondeada.
     - Cada dedo es una barra de falanges con extremos redondeados; los dedos van separados entre sí.
     - Pulgar ancho, unido a la palma por una cuña tenar del lado de la muñeca.
   - Se modelan ya en su pose; no usan huesos de dedos:
     - **Abierta:** dedos rectos en abanico leve.
     - **Puño:** pulgar por fuera de las falanges medias.
     - **Señalar:** índice recto.
   - Cada una se corta 2 mm después del último anillo del antebrazo y se cose a él. El anillo es la "boca de muñeca" estándar y comparte posiciones, normales y pesos, así que no queda escalón.
   - Pesos: el antebrazo en la orilla pasa a la mano rígida 6 mm después de la muñeca.
   - Se acaban los picos del puño: el puño ya no es piel doblada por el skinning.
3. **Intercambio.**
   - Seis mallas: `MANO_{ABIERTA|PUNO|SENALAR}_{L|R}`.
   - El nodo `MANOS` lleva en extras qué mano usa cada clip y cuándo. Se calcula de la flexión de los dedos que traía cada clip; por ejemplo, PointFwd = señalar, y en Wave se cambia en el tiempo.
   - En Godot, `ControladorAdan` muestra la mano que toca cada cuadro. `forzar_mano(lado, estado)` la fija, por ejemplo para un asset sosteniendo algo.
   - Se quitaron las manos viejas de una pieza.

## Pendiente

- **Mano con pistola**, después de aprobar las manos base. Hasta entonces el agarre `AGARRE_PISTOLA` sigue en el archivo, pero sus dedos no mueven la mano rígida.
- **Piernas, cadera y short:** piernas más juntas, cadera más angosta, dobladillo, pretina y cordón.
- **Pies.**

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v40/`)

- `manos_ref.png`: la hoja del brazo arriba y la primera mano (×1.0) abajo, con el cuello en la muñeca.
- `manos_ref2.png`: lo mismo con la mano ×1.3.
- `godot_manos.png` (dev, antes de `MANO_FIJA`): Idle (puños), PointFwd (señalar) y Wave (abierta), con el intercambio en Godot.
