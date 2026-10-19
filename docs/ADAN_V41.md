# Adán V41 · manos corregidas y short de una pieza (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** "Corrige lo del revisor y pasamos a parte inferior del cuerpo."

**Resultado:**
- `ADAN_V41.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS`.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v41.py ADAN_V22_HABLA.glb ADAN_V41.glb` (V40 + este paso).
- Los cambios de manos viven en `mano_bloques.py` y `receta_adan_v40.py`. Por eso, para reproducir V40 exacto hay que usar el commit `1006f42`.

## 1. Manos (revisión de V40)

- **Dedos-bloque.**
  - Dedos 14 % más cortos, más gruesos (grueso/ancho 0.92; antes 0.74) y casi sin ranura (2 px de la hoja; antes 5).
  - El ancho de los cuatro juntos no cambia.
- **Muñeca sin escalón.**
  - El último anillo del antebrazo no es una elipse, y el tubo de la muñeca sí. Ahora, en los 12 mm después de la costura, la mano toma el radio del anillo en cada ángulo (`mano_bloques.ajustar_boca`).
  - El tubo es más grueso y más largo (30 mm), así el grosor baja poco a poco hasta la palma.
- **Dorso.**
  - Con muñeca, la losa de la palma empieza 12 mm dentro del tubo, y la unión es más suave (0.018).
  - La línea del dorso se volvió una sombra suave.
- La línea del "codo" que vio el revisor era la costura de la muñeca: con el brazo colgando se lee a esa altura.

## 2. Short de una pieza (`copox/medicion/short_geo.py`)

Las proporciones ya coincidían con la hoja de piernas, medidas contra el ancho del torso:

| Medida | Referencia | V40 |
|---|---|---|
| Ancho del short en la cintura | 1.31 | 1.35 |
| Ancho del short en el dobladillo | 1.41 | 1.44 |
| Piernas de borde a borde | 1.41 | 1.38 |

Lo que no coincidía era la forma:
- Las piezas del torso y de las perneras estaban encimadas y dejaban una "solapa" al frente.
- El hueco de la entrepierna era ancho.
- El azul estaba muy saturado.
- No había pretina ni cordón.

Cómo queda ahora:
- **Una sola superficie implícita:**
  - Caja de sección superelipse de la cintura al dobladillo, con una muesca estrecha en la entrepierna, como en la hoja.
  - La boca de la cintura abraza al torso (+4 mm), así no se ve el interior.
  - Las bocas de las perneras quedan abiertas, con el borde al plano exacto.
- **Pretina:** los 18 mm de arriba, partidos por un plano exacto, con su propio material y 1.2 mm de resalte.
- **Cordón:** un moño al frente (nudo, dos lazadas y dos puntas). Va en el hueso Hips.
- **Colores de la paleta:**
  - Short: `azul_desaturado/2` #4F6D9A.
  - Pretina: `azul_desaturado/3` #3B5475.
  - Cordón: `medidos/cabello_blanco` #DDDDE7.
- **Pesos:** transferidos de las piezas viejas del short y suavizados.

## Pendiente

- **Pies:** etapa siguiente de la parte inferior. Tobillo más bajo, dedos y talón como la hoja de pies.
- **Short:** costura trasera (canesú) y pliegue del frente, como la hoja. Detalles menores.
- **Mano con pistola**, después de aprobar las manos.
