# ALTH-META · Auditoría de mantenimiento (2026-10-12)

**Dictamen:** CONSERVAR. Laboratorio central de assets y pipeline experimental AlasTheo; no trasladar modelos a Godot sin verificación de escala, semejanza, rig y procedencia.

## Hallazgos del inventario

- Árbol `main`: 434 archivos rastreados en el corte inspeccionado. Asset notable: `assets/joven_rubio/theo_alpha.glb` (~8.86 MB) y referencias visuales (muchas PNG de ~1–2 MB). **No deben considerarse descartables** por tamaño: sirven para comparar fidelidad.
- `Stylizer` ya reside en `tools/stylizer/`, con puente `UNREVIEWED`, suite aislada y archivo histórico privado externo; no requiere otro repositorio activo.
- ALASTHEO original cuenta con un bundle Git restaurable persistente en `docs/integration/git-backups` y Wiki revisada como vacía.
- El workflow `copox-scheduler.yml` **no contiene cron activo**: utiliza solo `workflow_dispatch` desde el 9 de octubre. No reactivarlo sin orden explícita.
- El directorio `.github/workflows/` contiene muchas campañas experimentales y workflows históricos. Su presencia es **deuda de navegación y mantenimiento**, pero borrarlos a ciegas rompería la reproducibilidad de pruebas. Clasificar por uso y evidencia antes de retirar alguno.
- El audit de integración y la suite Stylizer habían reportado PASS después de la consolidación. Las pruebas no equivalen a aprobación artística.

## Mejora entregada

`python scripts/audit_workflows.py` enumera los triggers de workflows directamente desde los archivos YAML (sin permisos GitHub, tokens ni dependencias instalables). Con `--fail-on-schedule` permite revisar y bloquear programaciones activas **solo cuando se invoque explícitamente**. Un YAML complejo puede requerir comprobación manual; este lector es un inventario de primera línea, no un parser YAML completo.

## Próximos ahorros posibles sin pérdida de valor

1. Clasificar manuales recientes frente a experimentos históricos, conservar en `docs/` los resultados y solo después archivar definiciones obsoletas.
2. Generar imágenes de prueba en artifacts de vida limitada y conservar en Git únicamente baselines seleccionadas, cuando no sean necesarias como referencias maestras.
3. No ejecutar proveedores externos, Kaggle/IA ni campañas de generación por defecto; mantener aprobaciones explícitas para las corridas costosas.
4. Mantener protegidas rutas de assets, el contrato Alpha y el archivo original. No tocar GLB/BLEND ni escalas automáticamente.

**Límites:** esta fase no hace refactor Blender/Godot ni reconstruye geometría. Tampoco afirma verificar licencias de todas las referencias externas.
