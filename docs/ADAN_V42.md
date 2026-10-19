# Adán V42 · piernas y pies de bloques (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** "Sigue con piernas desde cadera y pies".

**Resultado:**
- `ADAN_V42.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v42.py ADAN_V22_HABLA.glb ADAN_V42.glb` (V41 + este paso).

## Medidas

La regla es el dobladillo del short, porque en V41 ya coincide con la hoja.
- **Ancho de la pierna:** 0.35 del ancho del short en el dobladillo, igual en la hoja del cuerpo y en V41. No cambia.
- **Pliegue del tobillo:** al 44 % de la altura del dobladillo (hoja del cuerpo, de frente): y = 0.059.
- **Largo del pie:** 1.8 veces el fondo de la pierna (hoja de pies, de lado): 0.18. V41 ya medía eso.

En medidas, piernas y pies ya coincidían. Lo que no coincidía era la forma: el pie era una "bota" redonda con suela y sin dedos.

## Qué cambió (`copox/medicion/pie_geo.py`)

Una superficie implícita por pierna reemplaza `Pierna*_PIEL`, `Pie*`, `Cana*` y `Suela*`:
- **Pierna:** un prisma recto que sale de dentro del short y se angosta un poco hacia el tobillo.
- **Pie:** sale de la pierna con planos inclinados, como en la hoja de pies:
  - El lado de adentro es recto.
  - Afuera y atrás (talón) se abren hacia el piso.
  - El empeine es plano bajo la pierna y baja en rampa recta hasta los dedos.
- **Dedos:** cuatro bloques separados; el gordo, hacia adentro, es más ancho y más largo.
- **Tobillo:** un pliegue suave (unión 0.012).
- **Planta:** al piso exacto (y = 0).
- **Pesos:** transferidos de las piezas viejas (pierna, pie, caña y suela), con Toes en los dedos.

## Pendiente

- La costura trasera del short y el pliegue del frente.
- La mano con pistola, después de aprobar las manos.
