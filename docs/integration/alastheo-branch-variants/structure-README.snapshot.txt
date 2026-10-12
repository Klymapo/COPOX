# ALASTHEO

Repositorio maestro de **producción visual y 3D** de AlasTheo.

Su objetivo es mantener separadas y trazables las referencias, archivos fuente, exportaciones, documentación técnica y evidencia de validación. El proyecto jugable de Godot puede evolucionar de forma independiente en `Klymapo/peso-de-los-nombres`.

## Estructura

```text
ALASTHEO/
├─ assets/          # referencias y material visual de entrada
├─ models/          # archivos 3D fuente, exports y previews
├─ scripts/         # Blender, pipeline y utilidades
├─ tests/           # validaciones, capturas y evidencia
├─ docs/            # producción, diseño, pipeline y decisiones
├─ archive/         # iteraciones obsoletas o experimentos preservados
├─ .github/         # plantillas y flujo de colaboración
├─ .gitattributes
└─ .gitignore
```

Consulta [`docs/STRUCTURE.md`](docs/STRUCTURE.md) para saber dónde colocar cada archivo y [`docs/NAMING.md`](docs/NAMING.md) para las reglas de nombres y versiones.

## Regla principal

- **Fuente editable** → `models/source/`
- **Entregable reproducible** → `models/exports/`
- **Imagen de revisión** → `models/previews/`
- **Referencia visual** → `assets/references/`
- **Script** → `scripts/`
- **Medición, prueba o evidencia** → `tests/`
- **Documento de decisión o especificación** → `docs/`
- **Material que ya no forma parte del flujo activo** → `archive/`

## Versionado recomendado

Usa versiones de tres dígitos para modelos: `theo_v010.blend`, `theo_v010.glb`, `theo_v010_front.png`.

No uses nombres como `final`, `final2`, `nuevo_final` o similares. La versión identifica el estado; Git conserva el historial.

## Estado actual

El libro de producción vive en `docs/production/`. A medida que se incorporen modelos, referencias y automatizaciones, deben respetar esta estructura para mantener el repositorio legible y automatizable.
