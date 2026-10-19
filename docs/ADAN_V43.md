# Adán V43 · cadera coherente y short más chico (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** "El ancho de la cadera no es coherente de cintura para abajo con el resto del torso. El bóxer también se ve muy grande." Decisiones: subir el dobladillo, short "solo más chico", corregir el volumen de la ropa de una vez. Piernas y pies ya aprobados.

**Resultado:**
- `ADAN_V43.glb`, SHA-256 `af9e5883fc51dd7523aef7beddcc63b79fb74287860a46e1ba1d448cc4854295`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v43.py ADAN_V22_HABLA.glb ADAN_V43.glb` (V42 + este paso).
- Antes de armar se verificó que el entorno reproduce V42 bit a bit (`84faed12…65fa`).

## Medidas

Contra `refs/personajes/adan/adan-cuerpo-4-vistas.jpg`, vista FRONT. Unidad W = medio ancho de la cintura del torso justo arriba del short.

| | Referencia | V42 | V43 |
|---|---|---|---|
| Boca del short | 1.05 | 1.33 | 1.05 |
| Entrepierna | 1.24 | 1.42 | 1.33 |
| Dobladillo | 1.30 | 1.46 | 1.36 |
| Centro de la pierna | 0.72 | 0.89 | 0.79 |

- **La incoherencia de V42:** la pretina era 31 % más ancha que la cintura (`HOLGURA_CINT` salió de la hoja de piernas, no de la del cuerpo) y las piernas iban muy separadas.
- **Por qué el dobladillo no llega a 1.30:** las piernas de V42 (aprobadas) son más gruesas que las de la hoja. Con 1.30 asomarían por la tela.
- **Alto:** el short de V42 ya coincidía con la hoja. Es 20 % más chico por decisión de Admin, no por la referencia.

## Qué cambió

1. **Piernas 1 cm más adentro cada una.** Se movió el hueso UpperLeg con toda su cadena y se corrigieron las matrices de enlace. La forma de pierna y pie es la de V42; el tobillo queda en el mismo lugar (y = 0.0589).
2. **Short nuevo**, con el mismo código implícito (`short_geo.py`):
   - Boca de 1.05 W, abrazando el torso, sin escalón.
   - Dobladillo de y 0.134 a 0.162: el short mide 20 % menos.
   - Entrepierna de 0.180 a 0.190, con la proporción de la hoja.
   - Fondo de 0.088–0.092 a 0.082–0.084: menos pompa de lado.
   - Muesca de 0.024 a 0.016.

## Prueba en Godot 4.7.2 (Walk y Run, vistas 0, −35 y 90)

- **Caminar:** mejor que V42. La tela casi no se arruga y ya no queda la solapa colgando.
- **Correr:** mejor que V42, pero no limpio. Con la rodilla arriba, el frente del short todavía se levanta y se ve un pico pequeño de lado. Es el mismo problema de V42 (cómo la tela sigue al muslo), más chico.
- **Siguiente técnica si hace falta:** forma correctiva o hueso de tela en la entrepierna. Se deja para las pruebas de ropa.

## Evidencia

- `cuerpo_v42_v43.png`: cuerpo en 4 vistas, antes y después.
- `short_v42_v43.png`: acercamiento a cadera y short en 4 vistas.
- `godot_{Walk,Run}_{0,m35,90}.png`: 4 cuadros por clip y vista, V42 arriba y V43 abajo.

## Pendiente

- Revisión de Admin.
- Short al correr: decidir en las pruebas de ropa.
