# Adán V24 · ojos limpios y boca para hablar (SIN APROBAR)

- **Base:** Adán V22 HABLA (`df8d4b96…`). **Resultado:** `ADAN_V24.glb`, SHA-256 `c1939c190f9f233dfbaa6f3829437607e9fa8ff15ba1034b81a86b7d0165519c` (14.3 MB, no se sube al repo).
- **Receta:** `docs/medicion/receta_adan_v24.py` (`python receta_adan_v24.py ADAN_V22_HABLA.glb ADAN_V24.glb`, ~4 s). Incluye todo V23 (`docs/ADAN_V23.md`).
- **Decisión de Admin (18 oct 2026):** Theo quedó como prueba y ya no se usa; el trabajo sigue solo sobre Adán.

## Párpados: "ojo medio abierto o abierto por partes"

Causa real (encontrada al comparar Godot con CHXP): **Godot genera LOD automáticos al importar** y colapsa las piezas que están plegadas en reposo (párpados, dientes, lengua). De lejos, el párpado de abajo se rompía en jirones y el ojo se veía abierto por partes. CHXP no hace LOD, por eso ahí se veía bien.

- `copox/godot/project.godot`: `[importer_defaults] scene/meshes/generate_lods = false`. **Hay que hacer lo mismo en el proyecto del juego** (o desmarcar *Generate LODs* al importar cada personaje).
- `BancoMovimiento` sube `lod_bias` como respaldo.

Además, en el modelo:
- La piel del párpado toma la normal y el color (rubor incluido) de la cara y su borde fijo baja en rampa hasta la piel: ya no hay contorno ni línea bajo el ojo.
- `ojo_feliz_L/R` (nuevo): ojo cerrado en arco hacia arriba, como los guiños de las referencias. `G23_3_RespuestaAmable` y `G23_5_RisaContenida` lo usan.

## Boca reconstruida

- **Visemas `vis_A E I O U MBP FV` rehechos**: aperturas reales (A en forma de D, O redonda, U en trompa, MBP labios apretados, FV labio de abajo bajo los dientes). La mandíbula (barbilla) y el labio se mueven por separado.
- **Nuevos:** `boca_sonrisa_abierta` (sonrisa con dientes, como las referencias) y `boca_dientes` (dientes apretados: enojo, esfuerzo).
- **Dientes de arriba** (fijos al cráneo), **dientes de abajo y lengua** (siguen a la mandíbula en todos los morphs). Materiales `DIENTES_ALTH` (marfil) y `LENGUA_ALTH` (rosa-rojo).
- La cavidad negra es 2.5 veces más honda para que quepan. En reposo no asoma nada, ni de frente, ni de lado, ni desde arriba.
- `Talk-loop` usa los visemas nuevos sin cambios en sus pistas: el habla ya abre la boca de verdad.
- Expresiones: Saludo con sonrisa abierta, Sorpresa con O, Amenazante y Fastidio con dientes.

## Controles de cara (44 en total)

Párpados: `parpado`, `alegre`, `parpado_inf`, `parpado_enojo`, `parpado_triste`, `ojo_feliz` (L/R). Cejas: `ceja_arriba`, `ceja_ceno`, `ceja_triste` (L/R). Cachetes: `cachete_inflar`, `cachete_subir` (L/R). Boca: `comisura_arriba`, `comisura_abajo` (L/R), `boca_*` (soplar, abrir, sonrisa, triste, o, tensa, lado_L/R, ancha, estrecha, sonrisa_abierta, dientes), `mandibula`, `vis_*` (7).

## Pendiente conocido

- La boca a distancia de juego (cámara de cuerpo completo) se lee chica; si hace falta, se puede escalar la apertura por personaje.
- Habla sincronizada con diálogos reales (texto o audio → visemas).
