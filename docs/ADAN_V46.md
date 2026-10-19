# Adán V46 · pierna baja y pie como una sola pieza (SIN APROBAR)

**Pedido de Admin (19 oct 2026):**
- "Detallamos los pies todavía más". Solo forma: sin uñas ni arco.
- Trabajo por partes: V46 pies, V47 manos y brazo, V48 nuca y cara.

**Origen:** la auditoría artística de V45 marcó el pie y el tobillo como la peor discrepancia. En el tobillo había un aro; el pie era una caja alta con aletas a los lados y la planta más ancha que el tobillo.

**Resultado:**
- `ADAN_V46.glb`, SHA-256 `857552f9479a950d5dc82ff680af23a7da9b6b2a51b8d7c2fa83c4c0c4292849`. Reproducible.
- Receta: `docs/medicion/receta_adan_v46.py ADAN_V45.glb ADAN_V46.glb` (segundos; no usa el campo implícito ni el simplificado).

## Técnica nueva (`copox/medicion/pie_loft.py`)

Pierna y pie salen de anillos horizontales cosidos en rejilla, sin unión suave. Eso quita el aro, y como no hay simplificado tampoco quedan rayas.
- **Pierna:** superelipse igual a V42–V45 (aprobada), más angosta dentro del short.
- **Pie:** bajo el tobillo, cada sección es un trapecio de esquinas redondeadas (vista desde arriba). El paso de la forma de la pierna a la del pie es gradual.

## Contra la hoja de pies (`adan-pies-4-vistas-captura.jpg`)

| | Hoja | V45 | V46 |
|---|---|---|---|
| Pliegue del tobillo ÷ fondo de la pierna | 0.82 | 0.64 | 0.82 |
| Talón (lado) | sigue la línea de la pierna; bisel abajo | sale 1 cm hacia atrás | sigue la pierna; bisel de 3 mm |
| Talón (espalda) | se abre a los lados a media altura y se bisela hacia la planta | caja más ancha abajo | igual que la hoja |
| Empeine (lado) | una diagonal del tobillo a los dedos | caja alta con escalón | una diagonal |
| Aro en el tobillo | no | sí | no |
| Dedos | 4, el gordo más grande, puntas en diagonal | igual | igual, con más caída |

Tamaño (de la hoja del cuerpo, como V42–V45): pie de 15 cm con los dedos, tobillo de 9 cm, planta de 10.5 cm.

## Godot 4.7.2

Walk, Run, Jump y Dash en frente, 3/4 y perfil: el pie no se rompe ni raya. Pesos por altura: rodilla, tobillo (desde la articulación del pie) y base de los dedos. El short sigue igual al correr (para las pruebas de ropa).

## Lo que queda, honesto

- **Planos:** el pie se ve más suave y redondeado que los planos de la hoja (sombreado suave). Para marcarlos más habría que facetar, y eso va contra "liso".
- **De lado**, sobre el empeine queda un abultamiento leve donde la pierna pasa a pie.
- **Dedos:** siguen siendo cajas iguales de alto; en la hoja son más largos y delgados.
- **Método:** 3 iteraciones con este método (tope de la regla del proyecto).

## Evidencia (rama `capturas`, `capturas/2026-10-19/adan_v46/`)

- `par_pies_V46.png` (hoja | V46 con la cámara de cada vista)
- `pies_v45_v46.png` (antes y después, con quiebres y luz del juego)
- `par_cuerpo_V46.png`
- `par_piernas_V46.png`
- `godot_pies_cerca.png`
- `godot_movimiento.png`

---

# Adán V46.1 · pendientes del pie (SIN APROBAR)

**Pedido de Admin (19 oct 2026):** "Continúa los pendientes de V46".

**Resultado:**
- `ADAN_V46_1.glb`, SHA-256 `f0898da2b357b986121813e8a255ac3c219f57d826d2acab1e9eb2353944edfd`. Reproducible.
- Receta: `docs/medicion/receta_adan_v46_1.py ADAN_V45.glb ADAN_V46_1.glb`.
- `pie_loft.py` suma parámetros nuevos; con los valores por defecto, V46 sale idéntico (`857552f9…`).

**Qué cambió:**
1. **Abultamiento de lado:** el pie llegaba a lo más ancho a media altura (11.4 cm) y se volvía a cerrar hacia la planta (10.4 cm). Ahora solo se abre el talón (vista BACK); los lados de adelante bajan planos de la pierna y se abren hacia los dedos.
2. **Escalón alrededor del tobillo:** el paso de la sección de la pierna a la del pie pasa del 15 % al 35 % de la altura del pie.
3. **Dedos como la hoja:**
   - Más bajos: 1.7 cm (el gordo ×1.2).
   - Más largos: 4.4 cm.
   - Más separados: 4.5 mm.
   - Más caídos (45 %) y con las puntas más escalonadas (1 cm).
4. **Planos un poco más marcados:** esquinas de 4–2.5 mm (antes 5.5–3.5 mm), con sombreado suave.

**Godot:** Walk, Run y Jump limpios.

**Queda:** el pie se sigue leyendo más suave que los planos facetados de la hoja. Es el límite de "liso" con sombreado suave.

**Evidencia** (rama `capturas`, `capturas/2026-10-19/adan_v46_1/`):
- `par_pies_V46_1.png`
- `pies_v46_v46_1.png`
- `godot_v46_1.png`
