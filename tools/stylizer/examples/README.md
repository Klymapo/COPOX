# Ejemplo 3D libre · Cubo experimental

Base mínima de geometría y materiales, sin datos personales, modelos de terceros, créditos, tokens, proveedores de pago ni Blender obligatorio.

Desde `tools/stylizer/`:

```bash
python examples/build_cube.py examples/example_cube.glb
python alth_bridge.py --input examples/example_cube.glb --output-dir examples/reports --asset-id cubo-prueba
python -m unittest discover -s tests -v
```

**Qué aporta:** un GLB 2.0 completo con seis caras, normales, material PBR azul, 12 triángulos, una escena y un nodo. Es suficiente para probar lectura, exportación e intercambio de manifiestos. El generador es determinista (mismos bytes por ejecución). No requiere conexión ni servicio externo.

**Qué NO aporta:** semejanza de Theo/Alastor, rig, animaciones, proporciones de personajes, procedencia artística ni validación de calidad. La geometría de un cubo de lado 1 tiene **unidades arbitrarias**; no debe usarse para definir la estatura de Theo Alpha.

El manifiesto emitido por el puente queda en `UNREVIEWED`. Su escala, silueta y demás comprobaciones quedan pendientes. Los archivos `*.glb` generados y `reports/` pueden eliminarse y recrearse cuando se necesiten.

La historia de las decisiones y los antiguos prototipos se encuentra en [el cuaderno experimental](../docs/HISTORIAL_EXPERIMENTAL.md).
