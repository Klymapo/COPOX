---
name: scully
description: Esculpe matemáticamente regiones de mallas 3D (como aplanar frente o redondear nuca) con planos de referencia, curvas de transición, límites de desplazamiento y máscaras de protección.
---

# Scully · Surface Sculpt

## Activación
Usar cuando la forma correcta puede obtenerse deformando suavemente una superficie sana: frente, mejillas, nuca, piezas de armadura u objetos.

## Procedimiento
1. Leer `AGENTS.md`, `CLAUDE.md` y `docs/COPOX_PROCEDIMIENTO_GEOMETRICO_CODEX_2026-10-14.md`.
2. Validar baseline, hash SHA-256, procedencia y coordenadas (glTF Y-up/m en Maniquí; Z-up/mm en otros proyectos).
3. Obtener una región editable y excluir vértices de ojos, boca, orejas o piezas congeladas; registrar ROI, plano, fuerza y límite de desplazamiento.
4. Ejecutar `copox.geometry.surface_sculpt.flatten_surface`; devuelve posiciones nuevas y desplazamientos medidos. Si el presupuesto se excede, rechazar sin recortar silenciosamente.
5. Crear una copia con versión; recalcular normales/UV donde corresponda en un adaptador de malla, **no** escribir un GLB directamente desde esta función.
6. Aplicar `copox-auditoria-3d`, cuatro vistas reales y comparación enfocada a la región intervenida. No confundir cambio visible con mejora.
7. Si el defecto es una placa fragmentada, costura, topología abierta o componentes superpuestos, **usar Anatomic Cut y Surface Stitch**; Scully por sí sola no corrige esos defectos.
8. No fusionar ni reemplazar modelos sin aprobación.

## Comprobación
`python -m unittest discover -s tests -p 'test_geometry_operations.py' -v`.

## Enlace con Visual Critic
No aplanar una frente sólo por lectura textual del agente. Exigir `geometry_plan.json` con `operator=Scully`, medición positiva `signed_excess_mm` y trazabilidad; la vista/pose problemática debe contrastarse con **TODAS las referencias aportadas**. Si otras vistas contradicen el cambio, el plan exige investigación, no deformación.
La operación emplea el plano, ROI, falloff y presupuesto del plan verificado; todas las facciones congeladas requieren máscara explícita. Después generar nuevas vistas y volver a ejecutar Visual Critic sobre cada referencia. `PLAN_READY_FOR_SANDBOX` nunca significa permiso para alterar baseline.
