---
name: copox-geometria
description: Construye o repara superficies de mallas 3D mediante ajuste elipsoidal, detección de bucles y puentes de contorno, sin usar IA generativa; úsala para cráneos, uniones, nuca, patillas, extremidades y assets de ALTH/COPOX.
---

# COPOX · Geometría matemática reproducible

1. Leer `AGENTS.md`, `CLAUDE.md` y `docs/COPOX_PROCEDIMIENTO_GEOMETRICO_CODEX_2026-10-14.md`.
2. Exigir baseline y SHA-256, licencia/procedencia, unidades/ejes y región editable. Nunca asumir que Beta/Delta/Gamma/r3 es licencia independiente.
3. Diagnóstico antes de generar: geometrías y `primitive.extras.pieza`, índices/UV, islas, loops de bordes, regiones protegidas y normales.
4. Elegir una operación de `copox/geometry/kernel.py`: `fit_axis_ellipsoid`, `resample_closed`, `boundary_loops` o `bridge_equal_loops`. Usar el resultado de diagnóstico para elegir, no invocar elipsoid para ojos, labios ni dedos.
5. `bridge_equal_loops` requiere DOS bordes auténticos en UNA malla indexada y con igual conteo de vértices. Si los lados están en primitivas glTF distintas, diseñar un ensamblado seguro de atributos e índices; no fingir soldadura ni usar el puente directamente.
6. Para contornos de distinta longitud, autointersecciones o UV/winding ambiguos: `RESEARCH_REQUIRED`. No interpolar skin, morphs ni UV sin un módulo y pruebas explícitas.
7. Tres candidatos hermanos como máximo; salida nueva por versión; nunca sobrescribir, borrar ni fusionar.
8. Ejecutar el skill `copox-auditoria-3d` para cualquier GLB producido. Mostrar PNG reales frente/perfil/trasera/3-4, detalle y comparación antes de pedir aprobación.
9. `main`, baselines aprobadas y assets heredados intactos. Registrar movimientos GitHub/Drive en Registro de cambios.

## Herramientas concretas
- `python -m unittest discover -s tests -p 'test_geometry_kernel.py' -v`
- `copox/geometry/kernel.py`: funciones puras NumPy, SciPy sólo para ajuste de elipsoide.
- `tools/maniqui/reconstruir_v03.py`: caso histórico, **no para nuevas fuentes limpias**.
- `copox/geometry/preflight_gate.py`: gate de métricas (no calcula las métricas).
- `copox/geometry/maniqui_geometry_recipe.example.json`: contrato de ejemplo sin activar.

