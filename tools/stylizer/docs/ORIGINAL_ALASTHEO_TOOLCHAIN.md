# Stylizer en el ecosistema AlasTheo

Stylizer es una **herramienta auxiliar privada**, no un juego ni el repositorio principal de modelos. Conecta conceptualmente la generación de mallas a partir de imágenes con el flujo de producción del universo AlasTheo. Este documento no presume que exista una integración automática entre repositorios.

## Responsabilidades

| Repositorio | Rol | Qué no debe hacer |
| --- | --- | --- |
| [alth-meta](https://github.com/Klymapo/alth-meta) (público) | Autoridad de especificaciones ALTH-META, assets y evidencia de auditoría | Aprobar automáticamente resultados sin revisión |
| **stylizer** (privado) | Prototipado, generación 2D→3D, preparación GLB y experimentos anatómicos | Reemplazar assets aprobados sin revisión |
| [peso-de-los-nombres](https://github.com/Klymapo/peso-de-los-nombres) (privado) | Videojuego Godot, escenas y runtime | Incorporar scripts de generación Python como autoloads o lógica jugable |
| [Legado ALASTHEO](https://github.com/Klymapo/alth-meta/tree/main/docs/integration) (en alth-meta público) | Historia documental previa consolidada y auditable | Recibir desarrollo nuevo |

## Flujo de trabajo recomendado

1. Definir las medidas, requisitos visuales y presupuesto técnico en **alth-meta**.
2. Generar o experimentar en **Stylizer**; guardar la entrada, salida y manifiestos del proceso. Algunas rutas y proveedores requieren credenciales o dependen de cuotas externas.
3. Revisar el GLB, la silueta, las proporciones, los materiales y las vistas de referencia en Blender. Una exportación técnica no implica aprobación estética.
4. Proponer el asset a **alth-meta** como candidato independiente y procesarlo mediante sus controles/aprobaciones. **Theo Alpha y todos los assets protegidos permanecen intactos.**
5. Cuando esté aprobado, importar el recurso seleccionado en el videojuego **peso-de-los-nombres** y validar escenas y animaciones. Los cambios del juego necesitan sus pruebas.
6. Mantener el origen y las versiones; no usar cambios directos de un repo a otro sin revisión.

**No implementado automáticamente:** sincronización de archivos entre los tres repositorios, despliegue de candidatos, aprobación automática y reemplazo de assets. Se requieren flujos explícitos si se quieren integrar en el futuro.

## Conocimiento histórico recuperado

El material del antiguo repositorio privado **STYLIZED** está íntegramente preservado en [`research/alth-anatomy/`](../research/alth-anatomy/README.md): 12 archivos idénticos por Git SHA, tres scripts Blender v0.8.x, medidas en CSV/XLSX y documentos de anatomía. Ese material es **candidato de investigación**, no estándar aprobado.

## Seguridad y visibilidad

Este repositorio es **privado**. `alth-meta` es **público**. Evitar mover al repo público tokens, experimentos privados, prompts internos, archivos no autorizados o datos sensibles. Si se decide publicar un módulo de Stylizer, auditar primero su código y procedencia de datos.

## Conservación

- Mantener Stylizer como herramienta independiente por ahora: su Python, dependencias, tests y colas no son parte del runtime Godot.
- No renombrar ni fusionar directamente repositorios hasta verificar despliegues/CI/importaciones.
- Priorizar organización por roles y documentación antes que copiar binarios repetidos o integrar código experimental en producción.

Actualizado el 12 de octubre de 2026.
