# Stylizer · Herramienta de generación 3D para ALTH-META

**Estado: PROTOTIPO EXPERIMENTAL.** Versión integrada de Stylizer en AlasTheo, útil para aprender y probar ideas. Ningún modelo se declara definitivo. Los baselines son puntos de comparación y COPOX/CHSP-X conserva controles técnicos, no certificados artísticos finales.

**[Ejemplo GLB gratis, reproducible](examples/README.md)** · **[Cuaderno de experimentos e historia](docs/HISTORIAL_EXPERIMENTAL.md)**

## Funciona como aplicación independiente dentro de esta carpeta

Desde la raíz de `alth-meta`:

```bash
cd tools/stylizer
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python pipeline.py --help
python alth_bridge.py --help
```

**No hay que instalarla ni ejecutarla localmente** para consultar su código o administrar el proyecto; las instrucciones anteriores son para quien decida ejecutar o probar la herramienta. La reconstrucción de modelos requiere proveedores que pueden necesitar credenciales o tener cuotas/pago. No se activan automáticamente.

Para el servidor web con Docker y dependencias aisladas:

```bash
docker build -t alth-stylizer -f tools/stylizer/Dockerfile tools/stylizer
```

La integración en el monorrepositorio **no implica** que exista un servidor en funcionamiento. `compose.yaml` debe ejecutarse desde esta carpeta y requiere una contraseña segura, además de almacenamiento privado. No desplegar `render.yaml` del proyecto antiguo: su plan experimental era de pago.

## Integración ALTH segura: solo registro de candidatos

El nuevo puente `alth_bridge.py` toma un GLB ya generado y crea un manifiesto en una carpeta aparte:

```bash
cd tools/stylizer
python alth_bridge.py --input /ruta/modelo.glb --output-dir /ruta/candidatos --asset-id prueba-001
```

- Verifica cabecera GLB y calcula SHA-256.
- Lee `spec/alth_spec.json`, actualmente v2.0, con **Theo Alpha como referencia**.
- Detecta presencia de `skins`, animaciones y objetivos morph en el JSON glTF; no afirma haber auditado el rig.
- Conserva el GLB **sin alterarlo**, no adopta la altura predeterminada 1.8m, no reescala, no normaliza y no aplica decimación.
- Registra la propuesta en estado `UNREVIEWED` con escala, orientación, semejanza, materiales y rig en `PENDING`. No la promociona, ni cambia ningún asset aprobado.
- Impide guardar manifiestos dentro de `assets/` del proyecto y evita sobrescrituras del informe.

**Importante:** `prepare_godot.py` del programa original es un adaptador para mallas estáticas. Rechaza armatures, animaciones y shape keys y no debe usarse para personajes riggeados. Un modelo generado o preparado **no** está aprobado automáticamente para el juego.

## Ubicación y privacidad

Este código se seleccionó del antiguo `Klymapo/stylizer` con autorización para hacerlo público. Se conservaron módulos ejecutables, pruebas, Dockerfile, requisitos y manual original, incluyendo además los **12 documentos, scripts y registros originales de investigación STYLIZED**, verificados por SHA. No se importan GLB/PNG de demostración, estado de colas, contraseñas, credenciales ni propuestas de alojamiento de pago. Los archivos importados se compararon por SHA Git con su origen.

- [Investigación anatómica histórica STYLIZED](research/alth-anatomy/README.md) — candidatos, no estándar aprobado
- [Manual original](docs/ORIGINAL_STYLIZER_README.md)
- [Flujo original AlasTheo](docs/ORIGINAL_ALASTHEO_TOOLCHAIN.md)
- [Especificación vigente](../../spec/alth_spec.json)
- [COPOX](../../copox/README.md)

Para borrar `Klymapo/stylizer` como repositorio independiente, respaldar antes su **historial Git completo en un destino privado** y decidir qué hacer con sus antiguos binarios de muestra. Aquí se conservaron el código, la investigación STYLIZED, un ejemplo neutro reproducible y una cronología curada, **pero esto no equivale a un espejo de Git**.
