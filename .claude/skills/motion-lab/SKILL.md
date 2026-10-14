---
name: motion-lab
description: Crea, mide y corrige animaciones corporales con biomecánica, contactos, trayectoria y timing; contrasta todos los movimientos y fotogramas contra todas las referencias aportadas.
---

# Motion Lab · movimientos con biomecánica

1. Inventariar **todos** los vídeos, fotogramas y poses aportados, con ID, vista, FPS, duración, fase de acción y soporte. Pasar la matriz a `visual-critic`; si faltan momentos/vistas clave, bloquear conclusiones de fidelidad.
2. Leer `rig-architect` para jerarquía, límites, tamaño, centros de masa y pies. No generar una caminata sólo con rotación sinusoidal de piernas: modelar fases de apoyo y balanceo, pelvis, rodillas, tobillos, contrapeso de brazos, tronco y mirada.
3. Separar locomoción (idle/walk/run/sprint/jump/land/turn), interacción (sentarse, levantarse, manipular objetos), combate y animación contextual. Derivar velocidad, cadencia, longitud de paso y anticipación desde referencias, sin inventar magnitudes si no se midieron.
4. Definir timeline y curvas interpoladas reproducibles, SLERP para rotaciones; pies plantados durante apoyo, suelo, colisiones, contacto manos-objetos, continuidad y foot sliding. Reportar penetraciones y violaciones de joint limits.
5. Validar transiciones, root motion, loops y sincronización con eventos del juego. Mantener los 29 clips heredados si el candidato se basa en Maniquí, sin sobrescribirlos; nuevos clips versionados y probados.
6. Generar capturas reales multivista y contact sheets temporales en fotogramas clave (inicio, transición, mitad, final y eventos) para **cada vídeo de referencia**; comparar con `visual-critic`, sin promediar ocultando un mal aterrizaje.
7. Aplicar preflight de clip, pose y peso barato antes de render profundo; ejecutar pruebas Godot y gestos solo en finalistas. No declarar física real cuando sólo se usó cinemática.
8. Entregar clips por separado, hoja temporal multivista, informe de foot contacts, trayectorias y diferencia por referencia. No fusionar sin aprobación.

