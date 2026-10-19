# Adán V43.1 · una sola mano visible por defecto (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** las manos "se ven dobles, encimadas sobre sí mismas".

**Causa:**
- Desde V40, cada mano trae tres mallas en el mismo lugar: `MANO_ABIERTA`, `MANO_PUNO` y `MANO_SENALAR`.
- El controlador del juego (`copox/godot/movimiento/controlador_adan.gd`) prende una según el clip.
- En el archivo las tres venían visibles. Todo lo que no usa ese controlador (CHXP, el banco `prueba_movimiento` de Godot, Blender) las dibujaba encimadas.
- Las capturas de V40 a V43 muestran ese encimado. No era la forma real de la mano en el juego.

**Resultado:**
- `ADAN_V43_1.glb`, SHA-256 `cd9be611a15165c56207620f2da9d994e15e6b4fbfb7eaa888be442a7d6f9dbc`. Reproducible: dos armados dan el mismo SHA.
- Receta: `docs/medicion/receta_adan_v43_1.py ADAN_V43.glb ADAN_V43_1.glb`.

## Qué cambió

1. **GLB:** puño y señalar quedan ocultos por defecto con la extensión estándar `KHR_node_visibility`.
   - Godot 4.7.2 la respeta al importar: solo la mano abierta queda visible.
   - El controlador sigue cambiando `.visible` como antes.
   - Geometría, pesos y medidas iguales a V43.
2. **CHXP (`copox/render`):**
   - Ya no dibuja lo que el archivo marca oculto, igual que Godot.
   - Clave nueva `mostrar=` para sacar una variante a propósito, p. ej. `mano_izq;mostrar=MANO_PUNO_L;ocultar=MANO_ABIERTA_L`.

## Verificación

- **Godot:** `prueba_controlador` con V43.1 muestra una mano por lado. Abierta al caminar, puño al correr y golpear, índice al señalar.
- **Banco de pruebas:** le falta `armas/PISTOLA_ALTH_PROVISIONAL.glb` (lo genera `copox/armas/armas_alth.py`). No afecta a las manos.
- **CHXP:** de cerca, V43 asomaba dedos de más bajo la palma; V43.1 queda limpia.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v43_1/`)

- `manos_v43_1.png`: V43 encimada, V43.1 con una mano, y puño y señalar a demanda.
- `godot_controlador_v43_1.png`: caminar, correr, señalar y golpe en Godot con el controlador.

## Pendiente

- Rediseño de los dedos contra la hoja del brazo: largos, delgados, separados, pulgar abierto, mano más plana y sin la línea del dorso.
- Short al correr: queda para las pruebas de ropa.
