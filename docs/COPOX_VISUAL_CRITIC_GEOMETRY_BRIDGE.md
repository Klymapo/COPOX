# COPOX · Visual Critic conectado al motor geométrico (v0.1)
Fecha: 2026-10-14 · Estado: investigación experimental, no activación de cassettes ni promoción.

## Qué cambia
Se enlazaron:
1. `copox/visual/critic.py`: inventaría y compara **todas** las referencias y vistas/poses; registra cada anomalía con matriz completa de apoyo/contradicción/no visible/incierta.
2. `copox/visual/mesh_diagnostics.py`: para una ROI indexada, mide protrusión respecto a un plano **aportado por el brief o una referencia 3D fiable**, número de componentes conectados, aristas de frontera y SHA-256 del buffer de malla.
3. `copox/visual/geometry_planner.py`: selecciona operación *propuesta*, **nunca ejecuta ni promociona** un modelo de usuario.
4. Módulos matemáticos existentes: `copox/geometry/surface_sculpt.py`, `anatomic_cut.py`, `surface_stitch.py`.

## Reglas de selección verificables
| Evidencia multivista + malla | Propuesta | Bloqueos obligatorios |
|---|---|---|
| Abultamiento documentado + exceso sobre plano declarado + región continua | **Scully** | ROI sin máscara, curvatura objetivo inferida, parámetros/budget faltantes, contradicción entre referencias |
| Fragmentos medidos o caras flotantes + máscara anatómica + plano de corte medido | **Anatomic Cut** | Facets protegidos inciertos, morph/UV/skin sin soporte, ausencia de evidencia de fragmentos |
| Bordes realmente abiertos + loops orientados compatibles + atributos/skin compatibles | **Surface Stitch** | Loops con cardinalidad distinta, winding dudoso, atributos distintos, morphs no soportados o distancia de puente sin medir |

**La visualización aislada no puede establecer cuál es la causa de la anomalía.** Las máscaras de silueta son evidencia de diferencia, no detector automático de "bulto", "fragmento" o "costura". La familia de defecto debe documentarse mediante inspección artística o mediciones de conectividad verificadas.

**Ninguna operación se aplica automáticamente a los GLB de usuario**. El estado `PLANS_FOR_SANDBOX` significa que la operación tiene prerrequisitos para una copia de laboratorio, no autorización artística ni legal. Hay revisión visual humana pendiente y aprobación de Admin separada.

## Manifiesto de mediciones
El JSON de `--geometry-diagnostics` incluye `anomalies`, una entrada por ID de anomalía del reporte visual. Ejemplo de abultamiento medido:

```json
{
  "anomalies": {
    "frente-01": {
      "kind": "surface_bulge",
      "signed_excess_mm": 14.0,
      "region_topology_continuous": true,
      "measurement_provenance": {
        "source_sha256": "REEMPLAZAR_CON_SHA256_DE_64_HEX",
        "measurement_method": "indexed mesh ROI plane-excess v1",
        "coordinate_system": "Y-up / meters"
      },
      "flatten": {
        "direction": [0, 0, 1],
        "target_projection": 0.244,
        "region_center": [0, 0.09, 0.21],
        "region_radii": [0.18, 0.17, 0.21],
        "strength": 0.9,
        "falloff": 0.35,
        "max_displacement": 0.045
      }
    }
  }
}
```

Estos números son **ilustrativos**, NO para Alastor ni el Maniquí real. El plano frontal debe derivar de una meta artistica validada; un elipsoide natural también puede sobresalir de un plano arbitrario.

Para fragmentos: `kind=surface_fragments`, `disconnected_components` o `floating_triangles` medidos, `safe_cut_plane_measured=true`, `protected_faces_mask_ready=true`, `skin_attributes_supported=true`, `cut_plane={normal,offset}`.

Para costuras: `kind=open_seam`, `target_boundary_edges>0`, `loop_vertex_counts=[N,N]`, `loop_winding_valid=true`, `attributes_compatible=true`, `morph_targets_present=false`, `max_gap_m>0`. Estos valores deben venir del adaptador geométrico real, no de una conclusión verbal.

## Ejecución

```bash
python -m copox.visual.critic refs.json --root . \
  --output .copox/evidence/visual \
  --geometry-diagnostics diagnosed_mesh.json

# Reutilizar reporte visual existente:
python -m copox.visual.geometry_planner \
  --visual-report .copox/evidence/visual/report.json \
  --geometry-diagnostics diagnosed_mesh.json \
  --output .copox/evidence/visual/geometry_plan.json

# Validar integración y prohibiciones:
python -m unittest discover -s tests -p 'test_visual_geometry_planner.py' -v

# Demostración completamente matemática, SIN Hunyuan ni Beta:
python -m tools.geometry.demo_visual_loop
```

Un defecto en una sola vista y no en otras sigue siendo relevante. Si el ID de una referencia no se evaluó, `BLOCKED`. Si hay opiniones contradictorias, `RESEARCH_REQUIRED`. Si se propone una operación, el resultado exige protección de facciones, preflight estructural, comparación de todas las vistas, tests de rig/Godot y revisión Admin.

## Demo de extremo a extremo
`tools/geometry/demo_visual_loop.py` crea cabeza elipsoidal **propia** + bulto **intencional**; produce capturas exactas front/3⁄4/side/back, máscaras y reportes. El operador se elige a partir del inventario de las cuatro referencias, un diagnóstico geométrico medido y el tipo sintético conocido. `Scully` se ejecuta sólo en el fixture sintético, después se vuelve a comparar con las mismas cuatro referencias. No significa detección semántica de una cara real sin referencia, ni aprobación de un personaje de juego. Evidencias: `docs/visual/geometry_loop_demo/` en rama experimental. Workflow `.github/workflows/copox-visual-geometry-demo.yml`.

## Próximas mejoras técnicas
1. Capturar y registrar referencias adicionales no sólo de repositorio: vídeo con timestamps, derecha/izquierda, primer plano, expresiones.
2. Añadir extracción **medida** de fragmentos, bucles y continuidad de normales para completar Cut/Stitch sin introducir valores ficticios.
3. Aumentar detector regional de bultos con análisis de curvatura y landmarks alineados a todas las cámaras declaradas.
4. Adaptador GLB multimat con skin/UV/rig/morph, validador glTF y reimportación Godot.
5. Integrar como cassette OPCIONAL después de QA. No ejecutar en producción sin aprobación humana.

## Registro de cambios
- 2026-10-14: creado planificador evidencial, medición de ROI y demo sintético. Visual Critic y las tres skills geométricas conectadas por instrucciones operativas. Pruebas de fail-closed de referencias y procedencia. Sin fusión ni modificación de activos históricos.
