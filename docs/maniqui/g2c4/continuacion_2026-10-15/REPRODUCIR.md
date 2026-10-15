# Reproducir continuación G2-C4

Requiere V3 exacta, la referencia Delta y los ensayos B2 de la campaña
inicial. Recuperarlos de los paquetes enlazados en `../ENTREGABLES.md`;
verificar SHA antes de operar. No usar r3 como modelo final.

Python con numpy, scipy y Pillow; Node con `gltf-validator`; Godot oficial
4.7.2 y Xvfb con Mesa. Herramientas gratuitas, sin servicios generativos.
El flujo base inicial se documenta en `../REPRODUCIR.md`.

Desde la raíz del repositorio, sin candidatos de continuación existentes:

```sh
python tools/maniqui/g2c4_surface_patch.py
python tools/maniqui/g2c4_jaw_transition.py
python tools/maniqui/g2c4_jaw_transition.py --c3
python tools/maniqui/g2c4_continue_qa.py
NODE_PATH=/ruta/node_modules node build/g2c4_continuacion/godot/validate.cjs
DISPLAY=:97 LIBGL_ALWAYS_SOFTWARE=1 /ruta/Godot_v4.7.2-stable_linux.x86_64 --path build/g2c4_continuacion/godot --script qa.gd
python tools/maniqui/g2c4_continue_audit.py
```

Iniciar Xvfb :97 previamente. No usar el Godot 4.6.3 del sistema para
atribuir resultados a 4.7.2. No ejecutar por segunda vez sobre los mismos
GLB: los generadores se detienen para conservarlos. Para reproducción,
usar otra copia aislada del repositorio/directorio de salida.

Los candidatos se rechazan por cruces aunque el proceso de auditoría de
invariantes termine sin excepción: ver `geometry_status`, `artistic_status`
y `production_approved`, no sólo el código de salida del script.

SHA256 maestros:

- A3: `77031b0b6d9faa706fdd320a7bdb723a8716378ae2487f2c2d6ef69684560ad9`
- C2: `c2e22b61ea5a4914260c757c9cf21799059091557011d9232bb9d796714b392f`
- C3: `119055f16f68bcc2470e80d47b5dd6932bcdbea22dea2447d1f06ff34818781c`

Las selecciones anatómicas se guardan en cada JSON. Son específicas de V3;
otro personaje necesita medición, clasificación de piezas y perfil propio.
