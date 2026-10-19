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
