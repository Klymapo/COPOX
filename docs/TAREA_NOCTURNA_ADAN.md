# Tarea nocturna · Adán (18 oct 2026, de 1 a 7 am, una corrida por hora)

Autorizada por Admin por adelantado. Cada corrida es una sesión nueva de Elio: lee este archivo completo antes de tocar nada.

## Dónde está todo

- **Código y recetas:** `Klymapo/COPOX`, rama `propuesta/pruebas-movimiento`. Nunca `main`; no fusionar; no abrir PR.
- **Modelos GLB:** `Klymapo/copox-modelos` (PRIVADO). Carpeta `adan/`. La versión vigente la dice `adan/ULTIMA.txt` (nombre de archivo + SHA-256). Los GLB **nunca** van a COPOX (es público).
- **Capturas:** rama `capturas` de COPOX, `capturas/2026-10-18/ADAN_<versión>/elio/`.
- **Bitácora de la noche:** `docs/NOCHE_2026-10-18.md` en la rama de COPOX (una sección por corrida).
- **Registro en Drive:** documento maestro "01 — COPOX · Memoria maestra integral" (id `1SYG_u3faWWcYKXSAzUePnOwQAApLmrAVpDwXtWE_K28`), sección "Registro de cambios": una entrada por corrida con fecha, qué cambió, commits y hash.

## Arranque de cada corrida (≈10 min)

1. `add_repo` de `Klymapo/COPOX` y `Klymapo/copox-modelos` con acceso push; clonar ambos (COPOX con `-b propuesta/pruebas-movimiento --depth 1`).
2. Leer `docs/NOCHE_2026-10-18.md` para saber qué hizo la corrida anterior y qué sigue. Verificar en la fuente (repo), no en reportes viejos.
3. Bajar el GLB vigente de `copox-modelos` y verificar su SHA-256 contra `ULTIMA.txt`.
4. Godot 4.7.2 oficial: `https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip`. Proyecto de pruebas: `copox/godot/` (LOD desactivados; `xvfb-run`). Copiar el GLB como `theo.glb`, `--headless --import`.
5. Skills: `godot-kit:animation-system` (y `player-controller`, `state-machine` si hace falta). Referencias visuales: `refs/` del repo y la Hoja de vistas.

## Herramientas propias

- **CHXP** (`copox/render`, `LEEME_IA.md`): render por código de vista; modos color, arcilla, malla, normales, **curvatura** (para bultos), clases.
- **SENKU** (`copox/medicion`): medición; `orejas.py`; `copox/movimiento/analizar.py` (por clip: huesos activos, estiramiento de aristas, mano en cabeza/torso, piso).
- **Banco de movimiento** (`copox/godot/movimiento/`): `BancoMovimiento` (AnimationTree por capas) y `prueba_movimiento.tscn` (modos `secuencia`, `clips`, `caras`).
- `copox/movimiento/laminas.py` (láminas y GIF), `tira_morphs.py`.

## Reglas

- Cada cambio es una **receta reproducible** `docs/medicion/receta_adan_vNN.py` que parte de la versión anterior; versión nueva = número nuevo (V26, V27…), **sin aprobar**. El maestro y versiones anteriores no se tocan.
- Medir antes y después (SENKU / CHXP curvatura / Godot). Si una versión no mejora lo medido o rompe algo, no se publica: se documenta y se sigue.
- Máximo 3 intentos por problema por corrida; si no sale, PLATEAU documentado y al siguiente punto.
- Presupuesto cero; nada de servicios de pago.
- No borrar nada. No tocar `main`.
- Al final de cada corrida: GLB nuevo a `copox-modelos/adan/` + `ULTIMA.txt`; código a la rama; capturas a `capturas`; sección en `NOCHE_2026-10-18.md`; entrada en el maestro de Drive.

## Lista de trabajo (en orden; cada corrida toma lo siguiente pendiente)

1. **Boca y labios sin bultos.** Admin aún ve "pequeños bultos" en boca/labios. Medir con CHXP `curvatura` (cara_frente y cara_34, reposo y visemas) y en Godot de cerca. Meta: alrededor de la boca la curvatura debe ser tan pareja como la mejilla (comparar desviación de curvatura en el anillo de la boca contra un parche de mejilla). Lo que ya se probó está en `docs/ADAN_V25.md`.
2. **Huesos y uniones (brazos, piernas, hombros, codos, rodillas, cadera, cuello).** Con `analizar.py`: hoy el hombro colapsa con el brazo arriba de ~110° (estiramiento ×26–×90). Corregir pesos de piel (suavizado de pesos en las uniones, reparto entre huesos vecinos) y, si hace falta, ubicación de los huesos. Meta: estiramiento máx < ×3 en todos los clips; sin mano dentro de cabeza/torso.
3. **Manos.** Huesos de dedos: pulgar se rompe en el puño, `M31_4_Senalar` no extiende el índice, aro oscuro en la muñeca. Corregir pesos y poses de mano.
4. **Locomoción.** Clips nuevos con keyframes por código (sin Blender): `Walk-loop`, `Run-loop`, `Jump` (impulso, aire, caída, aterrizaje), `Dash`. Proporciones chibi (2.5 cabezas): pasos cortos, rebote vertical, brazos con contrapeso. Probar en el banco con un controlador (`player-controller`): idle↔walk↔run por velocidad, salto y dash. Meta: pies sin patinar (medir deslizamiento del pie apoyado), sin atravesar el piso.
5. **Armas (provisionales).** Hacer dos armas de prueba simples, en el estilo ALTH y a escala chibi, marcadas PROVISIONAL: una de una mano (para las poses `M36_*`) y una de dos manos/empuñadura (para `M35_*`). Ponerlas en el hueso de la mano con un punto de agarre (BoneAttachment3D en Godot) y verificar que los dedos las rodean sin atravesarlas. Admin cambiará las armas reales de Theo y Alastor después.
6. **Acciones:** `Point` (índice extendido de verdad), `Punch_L`/`Punch_R` (lanzar puño con giro de cadera), y con arma: guardia, ataque, apuntar.
7. **Escena final de prueba:** caminar → correr → saltar → dash → detenerse → señalar → golpe → sacar arma, en GIF.

## Corrida de las 7 am (la última)

Además de su trabajo: resumen para Admin en `NOCHE_2026-10-18.md` (qué quedó, qué no, cifras antes/después, versión final con hash, qué falta decidir) y una entrada final en el maestro. Después de esa corrida la tarea programada ya no debe hacer nada.
