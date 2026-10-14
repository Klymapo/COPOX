# COPOX · Scully, Anatomic Cut y Surface Stitch — prueba inicial
Fecha: 2026-10-14. Estado: **funciones y skills implementadas en PR #37; pruebas sintéticas PASS; no aprobadas para producción**.

## Procedencia y arquitectura
Todas las mallas del demo provienen de fórmulas y arrays numéricos en `tools/geometry/demo_operations.py`; no se leen Gamma, Beta, Delta, Maniquí ni otros GLB del juego. No se ejecutan API de IA ni GPU.

Los tres módulos están aislados dentro de `copox/geometry/`:
- `surface_sculpt.py`: Scully / `flatten_surface`, plano, ROI elíptica, suave transición, máscara de vértices congelados y presupuesto de desplazamiento con fallo explícito.
- `anatomic_cut.py`: `cut_plane`, clip por triangulo, máscara de protección por **cara**, atributos `POSITION`, `NORMAL`, UV, colores, `JOINTS_0` y `WEIGHTS_0` interpolados en el borde. Declinación explícita de morph targets/custom y más de 4 influencias.
- `surface_stitch.py`: `stitch_parts`, recibe dos `MeshPart` separados, junta buffers compatibles sin desplazar vértices originales, hace puente indexado por dos bucles de igual cardinalidad y preserva ID de material por cara **internamente**. El export a GLB con varios materiales aún NO conserva automáticamente dicha soldadura entre primitivas.

Las skills correspondientes están en `.codex/skills/{scully,anatomic-cut,surface-stitch}/SKILL.md` y `.claude/skills/` bajo los mismos nombres. Describen el proceso, límites, criterios de rechazo y vínculo a auditores. No son plugins de ChatGPT automáticamente instalados.

## Evidencias medibles del primer demo

Los modelos no son personajes. Son una cabeza elipsoidal matemática, corte de esa esfera, y unión de dos tapas de 16 vértices cada una (una pieza estilo cilindro).

| Operador | Datos reales |
|---|---|
| Scully | 84 vértices modificados, máximo 0.05225 m, bajo límite 0.060 m |
| Anatomic Cut | 1,152 triángulos descartados, 96 triángulos afectados recortados, 96 cruces nuevos |
| Surface Stitch | 16 emparejamientos de borde, 32 triángulos de puente, 0 bucles abiertos del ensamblado indexado |

Capturas (4 vistas por fila antes/después):
- `docs/geometry/demo/01_scully_antes_despues.png`
- `docs/geometry/demo/02_anatomic_cut.png`
- `docs/geometry/demo/03_surface_stitch.png`
- `docs/geometry/demo/surface_stitch_sintetico.glb`: GLB de geometría sintética **sin rig, morph ni materiales múltiples**.
- `docs/geometry/demo/report.json`: parámetros, métricas y SHA-256.

## Motor COPOX — nueva fase barata opcional
`copox/engine.py` admite ahora `commands.preflight` tras `mutate + execute` y antes de `capture`. La orden debe escribir `{candidate_dir}/preflight.json` con `status: DEEP_ELIGIBLE` para continuar. `REJECTED_EARLY`, estados inválidos y la falta de archivo bloquean renders y pruebas profundas. Sin comando preflight, la ejecución conserva el comportamiento previo (demostrado por prueba de regresión). No se cambió `copox/cassettes/enabled/` ni se activaron cassettes productivos.

## Ejecución gratuita y pruebas
- Tests NumPy/SciPy para geometría, conservación de caras, UV, skin, no-mutación y errores esperados: `tests/test_geometry_operations.py`.
- Tests motor para rechazo, aprobación de fase profunda, archivo ausente y comportamiento heredado: `tests/test_engine_preflight.py`.
- Pruebas previas: `test_geometry_kernel.py`, `test_geometry_provenance.py`, `test_geometry_preflight.py`.
- GitHub Actions en rama experimental, sin IA. Ejecutar:
  ```
  python -m unittest discover -s tests -p 'test_geometry_*.py' -v
  python -m unittest discover -s tests -p 'test_engine_preflight.py' -v
  python -m tools.geometry.demo_operations
  ```
- Workflow `copox-geometry-demo.yml` publica PNG + GLB + JSON exclusivamente en la rama propuesta. No promueve ningún resultado artístico.

## Limitaciones no resueltas y próximos gates
1. No hay un exportador de múltiples primitivas materiales con prueba de topología soldada tras reimportar. El GLB demo es de una sola primitiva sin rig.
2. No se han validado morph targets, autointersecciones, colisiones, facciones ni animaciones de personaje (Godot pendiente).
3. El clipping trabaja con un plano, no con un contorno anatómico arbitrario. Para r3 se necesita **corte por banda/loop anatómico**, no sólo plano.
4. Scully mueve puntos sin retopología ni recalculado automático de normales de un modelo: se requiere adaptador al exportar.
5. Las operaciones aún son módulos nuevos, no están empaquetadas en un cassette real de producción.

## Política
No modificar ni eliminar GLB históricos, `main`, ramas ajenas o baselines; no fusionar PR #37 sin aprobación. No declarar que este demo repara r3. No afirmar que el algoritmo geométrico limpia legalmente el linaje de modelos antiguos.
