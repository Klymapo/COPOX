# Adán V48 · cabeza de una sola pieza con caras planas (SIN APROBAR)

**Pedido de Admin (19 oct 2026):**
- "Queremos que la cara se vea plana de frente. Y de atrás y los lados también. Es una sola pieza lisa en sus lados."
- "Los pómulos se ven muy marcados."
- "Una sola pieza lisa sin bultos en la nuca, veo una masa sobresalir."
- Las cejas no se tocan.

**Resultado:**
- `ADAN_V48.glb`, SHA-256 `8b9b017719fce3eb047c060ff2f8f0a519c285f98d5042618b4181b1735cd298`. Reproducible.
- Receta: `docs/medicion/receta_adan_v48.py ADAN_V47.glb ADAN_V48.glb` (unos segundos).

## Método (`copox/medicion/cabeza_caja.py`)

Escalado radial desde el centro de la cabeza hacia una caja redondeada, como la hoja de la cabeza:
- Para cada dirección se mide la envolvente actual (cara sin orejas ni nariz, más el pelo) y se lleva al radio de la caja.
- Se mueven juntos piel, pelo, ojos, cejas, párpados, boca, nariz y orejas. Los deltas de los 46 gestos se escalan con el mismo factor (jacobiano).
- El cuello no se toca: la transición va de y 0.49 a 0.575, sin escalón en la quijada.

**Caja:**
- Semiancho de 14 cm. La cara y el pelo forman un solo bloque (antes el pelo sobresalía 3 cm a los lados).
- Frente plano a la altura de la frente: los cachetes y los pómulos salen al plano.
- Atrás plano.
- Aristas de 4 cm; la quijada se angosta 8 % abajo.

**Nuca:** después de la caja, el pelo baja hasta 2 cm más y se sella sobre la piel (`pelo_nuca`, 1.5 mm de separación: sin motas).

## Verificación

- **CHXP:** frente, lados y espalda planos. En la arcilla no hay escalón en la quijada.
- **Godot 4.7.2:**
  - Nuca limpia desde nivel y desde abajo.
  - Las 24 expresiones (G23–G26, V04, neutra) funcionan.
  - Controlador del juego: caminar, correr, señalar, golpe.

## Queda

- **Facciones más grandes:** la cara se agrandó hasta un 12 % en algunas zonas (la boca se ve un poco más ancha) porque viaja con la superficie. Si molesta, se puede excluir de ese escalado a ojos, cejas y boca.
- **Lados:** la línea del nacimiento del pelo sobre la sien se ve algo dentada.
- **Bajo la nuca** sigue una franja de piel lisa entre el pelo y el cuello. Ya no hay masa.

## Evidencia (rama `capturas`, `capturas/2026-10-19/adan_v48/`)

- `cabeza_v47_v48.png`
- `par_cabeza_V48.png`
- `par_cuerpo_V48.png`
- `v48_godot.png` (nuca y cara en Godot)
- `godot_caras_v48.png` (24 expresiones)
- `godot_controlador_v48.png`

---

# V48 no aprobada · camino A (V48.1) descartado

**V48:** Admin no la aprobó (19 oct 2026). La caja completa dejó la cabeza como ladrillo y agrandó facciones y pelo.

**Camino A** (`receta_adan_v48_1.py`): partir de V47 y aplanar solo pómulos, lados y nuca con un campo local (`cabeza_caja.mascara_local`). Dos intentos:
1. **Hacia el plano (±8 %):** cachetes inflados como bolsa y bordes marcados en las orillas de cada zona.
2. **Solo hacia adentro:** casi sin cambio (3 mm como máximo) y un pliegue en arco detrás de la oreja.

**Conclusión:** los cachetes de V47 son la esquina redondeada de la cabeza, no un bulto. Aplanar exige sacar esa esquina, y hacerlo en una sola zona deja escalones. No se publica GLB.

Opciones a Admin: A2 (caja de V48 a media fuerza con las facciones fijas), A3 (solo la nuca) o dejar V47.

---

# Adán V48.2 · sin rollo en la nuca ni visera sobre los ojos (SIN APROBAR)

**Pedido de Admin (19 oct 2026):** con capturas de V47, "¿Ves los bultos en nuca y cejas que me refiero?". Martillo.

**Resultado:**
- `ADAN_V48_2.glb`, SHA-256 `ec83c0a4e23dc87be6d14d4824d6718e0dc6936e6b882357eefc4ce9414594f2`. Reproducible.
- Receta: `docs/medicion/receta_adan_v48_2.py ADAN_V47.glb ADAN_V48_2.glb`. Parte de V47: V48 y V48.1 no se usan.

**Qué cambió** (`copox/medicion/bultos_cabeza.py`):
1. **Rollo de la nuca:**
   - El pelo caía recto y bajo la oreja se enrollaba unos 3.5 cm hacia adentro. Ahora el plano de atrás baja recto hasta la orilla.
   - El desplazamiento se calcula una sola vez sobre el pelo y se aplica igual al pelo y a la piel de abajo, así la piel no atraviesa el pelo.
   - Después se alisa solo esa franja baja del pelo (Taubin, con la orilla fija).
2. **Visera de las cejas:**
   - La piel sobre los ojos sobresalía unos 2.5 mm. Ahora la frente baja recta desde el nacimiento del pelo (y 0.74) hasta arriba de los párpados (y 0.674); hasta 4.7 mm hacia adentro.
   - Las cejas se mueven con la piel.
   - La franja no toca los párpados: con la primera versión (y0 = 0.652), los ojos cerrados hacían ruido.

**Sin tocar:** forma general, cachetes, ojos, boca, nariz y orejas (como V47).

**Godot:** de espalda, el pelo cae liso hasta su orilla. Perfil limpio. Las 24 expresiones funcionan, con los párpados cerrados limpios.

**Queda:**
- Bajo la orilla del pelo de la nuca, la piel todavía redondea hacia el cuello.
- Algunas motas en esa orilla, porque esta vez no se reselló.

**Evidencia** (rama `capturas`, `capturas/2026-10-19/adan_v48_2/`):
- `cabeza_v47_v48_2.png`
- `v48_2_godot.png`
- `godot_caras_v48_2.png`

---

# V48.2 no aprobada · V48.3 en curso (sin GLB publicado)

**V48.2:** Admin no la aprobó. En las mismas vistas de sus capturas casi no cambiaba, y de espalda la terraza se veía más grumosa.

**V48.3** (`receta_adan_v48_3.py`, `pelo_cascara.py`), sobre V47:
- La piel de la nuca se alisa.
- La frente queda recta hasta la sien.
- El radio del pelo se suaviza sobre su propia malla, con la orilla fija.
- La piel escondida bajo el pelo se mete para no asomar.

**Estado:**
- La terraza ya no está: de espalda y de perfil el pelo es una sola superficie.
- Queda una textura granulosa en el pelo y unos pedacitos de piel en la orilla de atrás.
- Intentos que no funcionaron: envolvente por dirección (inflaba la nuca 4 cm) y piso de piel (copiaba su grano).

**Siguiente técnica propuesta:** pelo nuevo con malla nueva, por campo implícito y marching cubes, en lugar de mover la malla vieja.

### V48.3 · iteraciones del pelo implícito (19 oct 2026) — PLATEAU, sin aprobar

Técnica: malla nueva del pelo desde un campo implícito (`pelo_cascara.py`), marching cubes + Taubin, LOD a ~9.5 k tris.

1. `PeloImplicito` (rejilla az/el): pelo liso, sin terraza; hundía la coronilla (polo de la rejilla) y dentaba la orilla.
2. `PeloImplicitoEsfera` (direcciones de Fibonacci, máscara pelo vs piel descubierta): coronilla resuelta, pelo liso
   en las cuatro vistas. **Queda:** la orilla es un canto de 4 mm con línea irregular (frente, patilla, nuca abajo).
   GLB reproducible: SHA-256 `6cefca0d…3259`. Es la versión que se conserva.
3. `PeloImplicitoRas` (orilla al ras de la piel con el radio radial de la piel): **descartada**. La piel tiene varias
   capas por dirección (cabeza + cuello + interior), el promedio radial las mezcla y el pelo se rompió en placas.

Tope de 3 iteraciones del método alcanzado → PLATEAU. Propuesta para la siguiente técnica: la orilla con distancia real
a la malla de la piel (no radial): pelo = {distancia a la piel < g(máscara)} afuera de la piel, con g → 0 en la orilla.
