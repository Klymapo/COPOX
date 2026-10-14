---
name: cloth-dynamics
description: Construye y prueba movimiento de tela en gabardinas, faldones y otras prendas, con colisiones al caminar o sentarse y comparación con todas las referencias de ropa y movimiento suministradas.
---

# Cloth Dynamics · prendas y física responsable

1. Recopilar **todas** las referencias de ropa, poses y vídeo: de pie, caminando, sentado, corriendo, girando, acciones y vistas frontal/lateral/3-4/trasera. Revisarlas por `visual-critic`, incluyendo reversos y espaldas.
2. Mapear topología, capas, anclajes de hombros/cintura, grosor, pinning y zonas que deben conservarse (dobladillos, botones, mangas y bolsillos). Probar anatomía y contacto con tronco/piernas/manos.
3. Elegir explícitamente si se usará armature/auxiliary bones, springbones de Godot, simulación de cloth, blend de poses o cinemática de cola. No afirmar simulación física real si la tela se mueve por huesos.
4. Definir gravedad, rigidez, amortiguamiento, masa, viento/arrastre y límites en unidades del modelo; evitar valores mágicos no derivados. Preparar colisionadores de cuerpo/prendas y resolver autointersección de faldones.
5. Evaluar walk/run/sit/stand/turn/jump y contacto con asientos, rodillas, manos y gabardina; revisar estabilidad y clipping durante transiciones y no sólo poses finales.
6. Comparar todas las vistas, poses y fotogramas de referencia **de forma individual** con `visual-critic`; documentar ambigüedad si el vídeo oculta la parte posterior.
7. Ejecutar pruebas de importación y físicas Godot con evidencia real, frame-by-frame cuando sea necesario, junto a métricas de intersección y penetración. No modificar el rig base sin aprobación.
8. Entregar prenda GLB versionada (cuando corresponda), parámetros reproducibles, colisionadores, videos/capturas y reporte de fallos pendientes.

