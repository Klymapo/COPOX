# ALTH-META · Guía para no perderse

**¿Qué es?** Es el taller de modelos 3D de AlasTheo. Aquí experimentamos con personajes, caras, manos, poses, escala y exportación a Godot. **Que algo esté en este laboratorio no significa que ya esté aprobado para el juego.**

## Tres puertas de entrada

1. **Quiero ver cómo deben verse los personajes:** entra en [Referencias](../assets/references/README.md) y `refs/`.
2. **Quiero encontrar los modelos y pruebas:** entra en `assets/` (modelos y versiones) y `models/` (organización del material).
3. **Quiero revisar o mejorar un candidato:** entra en `chsp-x/` (mesa de revisión), `copox/` (pruebas) y `tools/stylizer/` (herramienta experimental ya integrada).

## Mapa de carpetas

| Carpeta | Para qué sirve |
|---|---|
| `assets/` | Modelos, versiones, pruebas y archivos GLB |
| `refs/` | Imágenes para comparar formas, proporciones y estilo |
| `chsp-x/` | Mesa de revisión y decisiones de aprobación |
| `copox/` | Ensayos, auditorías y aprendizaje entre iteraciones |
| `tools/stylizer/` | Herramienta que genera propuestas todavía no aprobadas |
| `docs/` | Bitácoras, decisiones, guías y respaldos históricos |
| `spec/`, `alth/`, `scripts/` | Las reglas y herramientas de construcción |
| `tests/` | Pruebas automáticas |
| `archive/` | Cosas conservadas para poder consultarlas después |

## Tres reglas para no estropear nada

- **Nunca sustituir Theo Alpha, Detective ni otro modelo de referencia sin revisión visual y pruebas.**
- **No borrar ramas `bucle/`, `progreso`, ramas con GLB, evidencia o intentos COPOX por parecer antiguas.** Pueden contener el único registro de un experimento.
- La automatización de pruebas **COPOX Scheduler sigue en modo manual**; no se han activado ejecuciones programadas en esta organización.

## Ramas y nombres

[Abre el catálogo completo de ramas](RAMAS_2026-10-12.md): diferencia «versión aceptada», «propuesta», «experimento» y «rama terminada». Las ramas antiguas conservan su nombre mientras aún tengan algún valor de investigación; las futuras pueden llevar nombres sencillos como `experimento/theo-manos` o `docs/guia-personajes`.

La historia de ALASTHEO y Stylizer originales está respaldada e integrada en este mismo laboratorio. No necesitas visitar los repositorios que ya eliminamos.
