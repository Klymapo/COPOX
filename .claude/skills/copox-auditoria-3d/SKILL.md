---
name: copox-auditoria-3d
description: Audita modelos GLB generados o modificados por COPOX, protege rig y facciones, compara cuatro vistas y separa preflight de pruebas profundas; úsala antes de aprobar cualquier variante de personaje o asset.
---

# COPOX · Auditoría por niveles de costo

1. Leer `AGENTS.md`, `CLAUDE.md` y el brief del asset.
2. Validar SHA de baseline, ejes/unidades y procedencia. Si falta dato crítico, detener: `RESEARCH_REQUIRED`.
3. Filtro barato (sin renders de movimiento): esquemas glTF, mallas, índices, `NaN`, áreas, normales, self-intersection si disponible; comprobar skin/animaciones, triangulos protegidos e islas UV sin soldar por posición de manera ciega.
4. Calcular métricas focales realmente medidas y pasarlas a `copox/geometry/preflight_gate.py`. No inventar `seam_connected`, `target_improvement_pp` ni usar un valor fijo por defecto.
5. Si `REJECTED_EARLY`, guardar causa y **no** ejecutar 87 muestras profundas. Si `DEEP_ELIGIBLE`, la etiqueta significa 'puede analizarse', **NO aprobado**.
6. Capturar cuatro vistas y acercamiento del área intervenida con cámaras idénticas; comparar contra referencia artística aprobada. IoU global es control de regresión, no criterio artístico único.
7. Sólo finalistas: validar poses Wave/Sit/Nod/HeadShake, los 29 clips si existen, importación Godot; verificar morphs, UV y pesos. Reportar falta de pruebas sin falsear un PASS.
8. Reportar `APROBABLE`, `UNA_CORRECCIÓN` o `REHACER/PLATEAU`; promoción sólo con aprobación explícita de Admin.

Comandos de referencia: `tools/maniqui/evaluar_v03.py`, `tools/maniqui/auditar_v03.py`; `copox/geometry/preflight_gate.py --metrics ... --config ... --output ...`.

