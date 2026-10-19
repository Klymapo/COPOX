# Adán V47 · mano 85 %, puño de bloque y brazo recto (SIN APROBAR)

**Pedido de Admin (19 oct 2026):**
- "Reducir un 15 % el tamaño de la mano". Decisión: la punta del dedo queda más arriba de la entrepierna.
- "Cuando cierre el puño, que no se vean los nudillos sobresalir".
- "Mantener recto y liso las uniones de todo el brazo".

**Resultado:**
- `ADAN_V47.glb`, SHA-256 `d2c9e1656c836411ca4f24eda6040fa29fe9eb86d5aced53ccb2abbb14fd35c4`. Reproducible.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v47.py ADAN_V46_1.glb ADAN_V47.glb` (menos de 1 minuto).

## Qué cambió

1. **Manos al 85 %:** abierta, puño y señalar. Largo de 17.0 a 14.4 cm; palma de 9.2 a 7.8 cm de ancho. Mismo estilo de V44.
2. **Puño de bloque** (`mano_bloques._bloque`, pose con `bloque`):
   - Los dedos doblados son una sola caja redondeada, al ras del dorso, con la cara de adelante plana. Así no sobresale ningún nudillo.
   - Ranuras leves entre dedos, al frente y abajo.
   - Unión suave con la palma.
   - Señalar usa el mismo bloque con medio, anular y meñique; el índice sale recto.
3. **Brazo recto** (`brazo_geo`, `lineal=True`):
   - Del hombro a la muñeca los semiejes van en línea recta: sin bulto de bíceps y sin cintura en el codo (`codo_max=0`).
   - Muñeca de 6.4 × 6.6 cm (V46.1: 7.6 × 8.3), según la hoja del brazo: 0.73 del brazo y menos ancha que la palma.
4. **Codo:** los pesos de brazo a antebrazo pasan en una rampa de 5 cm (antes eran los transferidos de la malla vieja). Junto al hombro quedan los de antes.

**Sin tocar:** pies (V46.1), piernas, torso, short y cabeza.

## Verificación

- **CHXP:** brazo de cerca en pose A, sin bíceps ni esquina en el codo. Puño sin nudillos; en el mapa de quiebres solo se marcan las ranuras y las aristas del bloque.
- **Godot 4.7.2, controlador:** caminar, correr, señalar, golpes y pistola bien. Banco con Walk, Run, Punch_R, Punch_L y PointFwd.

## Queda

- Línea leve entre la palma y el bloque del puño, por arriba.
- En la vista de palma (FRONT de la hoja del brazo) se ve el anillo de la costura de la muñeca. Ya estaba antes.
- El pulgar en el puño queda casi tapado por el bloque.

## Evidencia (rama `capturas`, `capturas/2026-10-19/adan_v47/`)

- `v47_prueba.png` (V46.1 contra V47: cuerpo, brazo, manos)
- `v47_puno.png`
- `par_brazo_V47.png`
- `par_cuerpo_V47.png`
- `godot_controlador_v47.png`
- `godot_movimiento_v47.png`
