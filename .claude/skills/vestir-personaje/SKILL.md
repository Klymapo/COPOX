---
name: vestir-personaje
description: Viste a un personaje ALTH-META con prendas por capas (técnica del short) desde el catálogo, o agrega una prenda nueva al catálogo. Úsala cuando haya que cambiar o crear ropa.
---

# Vestir personaje (COPOX)

**Reglas de Admin:** cada prenda es una pieza propia (no pintada), por capas, "un poco" holgada, con la textura que le
corresponde (sutil), respetando el límite pantalón/zapato. La técnica de referencia es la del short (`ropa_tubos`).

## Usar el catálogo
`copox/medicion/catalogo.py` → `ROPA`. Hoy: `traje_chaleco` (camisa + chaleco + pantalón + corbata + botones + cuello;
receta `docs/medicion/vestir_theo_v3.py`). En la ficha:
- `ropa.colores` (paleta) y `ropa.telas` (`tafetan_suave`, `sarga`, `lana_cerrada`, `saten`, `cuero`, `lona`).
- `ropa.params`: `camisa` (hol 6 mm, hol_manga…), `pantalon` (hol_pelvis 8.8 mm, hol_pierna 6.6 mm, hem, k entrepierna),
  `chaleco` (capa 4.2 mm), `corbata` (grosor, arista, separa, nudo), `chaleco_region` (cortes: v_fondo, borde…).
- La sisa del chaleco se mide del rig (articulación del brazo − 5 mm): sirve para cualquier personaje.

## Valores que ya funcionaron (Theo V4_1)
Camisa 6 mm (manga 6.5), pantalón 8.8/6.6 mm, chaleco 4.2 mm, crotch k 0.022, bastilla 0.056, textura camisa
`tafetan_suave` (amplitud 2.2 %), corbata hexagonal de 3 mm con arista y separada 2.5 mm del pecho.

## Agregar una prenda nueva
1. Skill `investigar-referencias` → brief en `docs/investigacion/<prenda>.md`.
2. Receta con `copox/medicion/ropa_tubos.py` (Tubo, `inflado`, `union`, `superficie_z`) y `texturas_tela.material_textura`.
3. Entrada en `catalogo.ROPA` con sus grupos de parámetros.
4. CHXP V3: `capas_sin_atravesar`, `hombro_cubierto`, `normales`, `sin_flotantes`, `paleta_alth` + revisión visual.

## Pendiente conocido (PLATEAU 19 oct)
`capas_sin_atravesar` (cuello oculto + chaleco/camisa en poses) y `hombro_cubierto` (~85 %). Próximo método: prueba de
capas sobre lo **visible** en el render y orilla de la sisa que siga al hueso del hombro (requiere research brief).
