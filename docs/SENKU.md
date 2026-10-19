# SENKU · motor matemático de COPOX

SENKU (`copox/medicion`) mide y edita modelos GLB sin abrir Blender:
- lectura y edición de glTF;
- proporciones y esqueleto;
- superficies implícitas (torso, manos de bloques, muñeca);
- siluetas e IoU contra referencias;
- quiebres de sombreado, rugosidad, paleta y piezas flotantes.

Rama `senku` creada desde `main` el 18 oct 2026 a pedido de Admin. El código viene de `propuesta/pruebas-movimiento` (commit d26b803).

## Contenido

- `copox/medicion/`: SENKU.
- `copox/render/`: CHXP, el renderizador. SENKU lo usa para rasterizar siluetas (`mano_silueta`) y para la luz del juego (`quiebres`).
- `tests/test_medicion_v2.py`: pruebas (`python3 -m unittest tests.test_medicion_v2`).
- `docs/COPOX_MEDICION_V2.md`: detalle del motor.

## Requisitos

Todos gratuitos: Python 3, NumPy, Pillow, scikit-image y SciPy. La simplificación de mallas usa Godot 4 headless (`GODOT_BIN`).

Esta rama no se fusiona a `main` sin aprobación de Admin.
