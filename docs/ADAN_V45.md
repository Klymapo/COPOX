# Adán V45 · liso y plano: nuca, brazos, manos y pies (SIN APROBAR)

**Pedido de Admin (18 oct 2026):**
- "Suavizado general. Queremos que no haya bultos… todo liso y plano. Tampoco queremos huecos. Veo un bulto en la nuca y hoyos en los brazos."
- "Corrige lo necesario de brazos y manos… dale una pasada a los pies. Prioriza likeness con las referencias de Adán renderizado."

**Decisiones:**
- Pies: forma de la hoja de pies, tamaño de la hoja del cuerpo.
- La mano de empuñar va después.
- Para sostener cosas se usan manos intercambiables; las armas actuales no son las finales.

**Resultado:**
- `ADAN_V45.glb`, SHA-256 `49883bdf43299897a27d14a8c01431df8af275ea711aa6134a1000359b902639`. Reproducible: dos armados dan el mismo SHA.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v45.py ADAN_V44.glb ADAN_V45.glb` (unos 3 minutos).

## Qué cambió

1. **Nuca** (`copox/medicion/pelo_nuca.py`):
   - **Hueco:** entre el borde del pelo y la piel había una rendija por la que se veía el interior de la boca. En CHXP salía como manchas oscuras; en Godot, como una línea rojiza.
   - **Bulto:** bajo el pelo quedaba una bola de piel.
   - **Arreglo:** la franja baja del pelo baja hasta 2.4 cm en el centro de la nuca (se desvanece hacia las orejas) y se acuesta sobre la piel, a 0.6 mm.
   - Se proyecta al punto exacto más cercano de cada superficie; no se crea geometría.
   - **Verificación:** interior de la boca visible desde atrás, de 216 px a 0.
2. **Brazos** (`copox/medicion/brazo_geo.py`):
   - Ahora son una superficie continua de sección caja redondeada, del mismo tamaño que V44.
   - Sin el relieve viejo (bultos de bíceps y antebrazo) y con el codo limitado a un estrechamiento de 3 %.
   - El barrido sigue 1 cm más allá de cada boca, para que el corte no toque las tapas. Las normales salen del gradiente del campo, así que no hay línea en la muñeca.
3. **Manos:** las de V44 (mismo estilo y poses), cosidas al anillo nuevo de la muñeca.
4. **Pies** (`pie_geo.py`, parámetros nuevos `escalon` y `caida`; por defecto el pie es idéntico al de antes):
   - La pierna queda como en V42–V44, porque estaba aprobada.
   - Se probó una pierna más cónica de 8 caras, como la hoja, y dejaba rayas al sombrear y al caminar en Godot. Se descartó.
   - El pie cambia hacia la hoja de pies: talón más abierto, pie un poco más abierto hacia afuera, dedos más delgados y separados, con las puntas en diagonal y la punta un poco caída.

## Medida "liso y plano" (`copox/medicion/liso.py`)

Porcentaje del área con quiebre alto en el mapa de quiebres, por región:

| Región | V44 | V45 |
|---|---|---|
| Brazos | 67.8 % | 7.7 % |
| Nuca | 22.2 % | 25.0 % (el borde del pelo ahora está sobre la piel: es la línea del nacimiento, a propósito) |
| Torso | 25.1 % | 16.6 % |

**Sin calibrar:** en piernas, pies y manos la medida sale alta en superficies que se ven lisas, por los triángulos largos del simplificado. Todavía no sirve de criterio de aprobado ahí.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v45/`)

- **01–06 (CHXP):** cuerpo, técnico, contra la hoja, cara, manos, short y pies.
- **07–10 (Godot 4.7.2):** controlador, movimiento en 3 vistas, todos los clips y nuca.

## Revisión independiente (revisor-visual-alth): UNA_CORRECCIÓN

- **Nuca:** SÍ. Ya no están las manchas oscuras ni la línea rojiza de Godot. Duda: motas claras pequeñas a lo largo del borde del pelo.
- **Brazos:** SÍ, lisos y continuos.
- **Manos:** SÍ en la abierta, sin la V del dorso. Puño y señalar conservan el contorno ondulado del lado de la muñeca, como en V44.
- **Pies:** PARCIAL. Dedos y talón ya van como la hoja.
- **B1:** en el tobillo hay un aro donde la pierna se une al pie; en la hoja la unión es limpia. Ya estaba en V44.
  - Dos intentos con el mismo método no lo mejoraron: empeine a la altura del pliegue con unión 0.0015, y unión de 0.014. Se queda como V45.
  - Necesita otra técnica: pierna y pie como una sola pieza hecha por secciones, no un campo con unión suave.
- **Regresiones contra V44:** ninguna.

## Pendiente

- Tobillo sin aro (B1), con otra técnica.
- Motas en el borde del pelo de la nuca.
- Contorno de la muñeca en puño y señalar.
- Mano de empuñar, para objetos y armas finales.
- Short al correr: para las pruebas de ropa.
- Calibrar `liso.py` para piernas, pies y manos.
