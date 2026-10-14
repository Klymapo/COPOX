# Maniquí r3 · Anatomic Cut G2 — ensayo verificable
Fecha 2026-10-14. Estado: **PR #40 BORRADOR, GLB DE PRUEBA NO SOLDADO NI APROBADO**.

## Objetivo y reglas
Restablecer el ciclo de Codex sobre geometría real: clasificar regiones anatómicas por triángulo, revisar cuatro vistas, efectuar un corte conservador y comprobar que protege el rig y las facciones antes de intentar soldadura. Nunca borrar ni sobrescribir la base ni otros modelos. Baseline: `assets/maniqui/maniqui_v0_3_r3.glb`, SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b` (modelo de origen histórico mixto Beta/Gamma). glTF Y-up, +Z frente, metros.

## Implementación reusable
- `copox/geometry/anatomic_roi.py`: máscaras por cara con prioridad absoluta de región congelada, cajas anatómicas definidas por cassette, banda angular paramétrica/cKDTree alrededor de costura real. Cada triángulo cae en exactamente una de cuatro clases (congelado / recorte propuesto / revisar / sin efecto). No modifica entradas ni GLB.
- `copox/geometry/contour_graph.py`: grafo de aristas abiertas después de soldadura espacial en COPIA ANÁLITICA a 1µm (no exportar), informa componentes, vértices de bifurcación, ciclos cerrados, aristas nonmanifold y cercanía al borde real de 128 posiciones del cráneo. Un ciclo geométrico no equivale a un contorno anatómico identificado.
- `tools/maniqui/g2_anatomic_dryrun.py`: ejecuta tres bandas hermanas desde la misma fuente, no encadenadas; cuatro vistas reales de las máscaras y simulación de corte (sin editar GLB).
- `tools/maniqui/g2_cut_probe.py`: produce **un GLB hermano exclusivamente experimental** retirando triángulos conservadores, dejando el resto de materiales/rig/animaciones/atributos idénticos. No reconstruye la costura ni mueve vértices.
- Tests: `tests/test_g2_anatomic_roi.py` y `tests/test_g2_contour_graph.py`; CI gratuita NumPy/SciPy/Pillow.

## Medidas sobre Maniquí r3

| Hipótesis | Triángulos propuestos para cortar | Triángulos anatómicos congelados | Sectores de 128 cubiertos | Bordes Cara por índice tras corte simulado |
|---|---:|---:|---:|---:|
| Conservadora | 167 | 2946 | 25.78 % | 3165 (antes 3310) |
| Intermedia | 268 | 2946 | 35.94 % | 3116 |
| Amplia | 334 | 2946 | 39.06 % | 3068 |

No se eligió simplemente la máscara más amplia. En las tres, el grafo de aristas de Cara sigue teniendo una arista nonmanifold y **ningún contorno circular válido** cercano al rim completo: 0 candidatos integrales compatibles. En los ciclos o componentes de la frontera la cobertura geométrica máxima con distancia de 25 mm es 79.688%; esto NO es un score de likeness. Una máscara que corta más triángulos y reduce aristas puede empeorar la estética o abrir una cara.

## GLB Cut Probe conservador — confirmado por auditoría estructural
- Archivo nuevo: `assets/maniqui/maniqui_v0_3_r3_g2_cut_probe.glb` (10,893,904 bytes).
- SHA256 `4ec9217c0758e473993e7665f4fbbefa83844798702f131beb3470666e081b94`.
- Se retiraron **167 triángulos** no protegidos y quedaron **3727** en Cara.
- 56 huesos, 29 clips; definiciones de nodos, skin, animaciones y bytes antiguos conservados; primitivas del cuerpo y `Craneo` no modificadas.
- Auditor original de Codex: **1357 triángulos faciales y 481 de oreja protegidos, cero pérdidas**; arrays originales de atributos de Cara conservados.
- Borde inferior del cráneo sigue con **128 aristas abiertas y sin unión física a Cara**. No hay morph targets faciales certificados, simulación física ni prueba Godot. Mantener estado CUT_ONLY_PROBE_UNAPPROVED.
- Evidencia: PNG de máscaras en `docs/maniqui/g2/`; auditoría `g2_cut_audit.json`, reporte `g2_cut_probe_report.json` y conjunto de capturas 4 vistas/poses generadas por `evaluar_v03.py` con 87 muestras de clips en GitHub Actions. Comparativa visual requiere inspección humana y fuentes del personaje.

## Qué aprendimos
1. La frente/cejas/facciones protegidas ocupan gran parte de la frontera requerida. Un recorte conservador sólo cubre el 25.8% de los sectores del cráneo; forzar 100% implicaría cortar anatomía importante.
2. La topología de Cara existente no ofrece un borde de 128 puntos soldable a la cúpula; cada ciclo aislado debe identificarse anatómicamente para evitar confundir oreja o párpado con perímetro facial.
3. **Surface Stitch G2 completo sigue BLOQUEADO.** La operación siguiente no es un corte indiscriminado sino *construcción de nueva piel de transición* que tenga un borde inferior sustentado por landmarks/tejido facial y borde superior homólogo de 128 vértices, conservando UV, rig y facciones.
4. Para Visual Critic no tenemos aún todas las referencias históricas del usuario ni cámara calibrada comparable del maniquí calvo; seis archivos locales eran heterogéneos y no justifican aprobación artística.

## Ejecución y revisión
```bash
python -m unittest discover -s tests -p 'test_g2_anatomic_roi.py' -v
python -m unittest discover -s tests -p 'test_g2_contour_graph.py' -v
python -m tools.maniqui.g2_anatomic_dryrun
python -m tools.maniqui.g2_cut_probe
```
El último comando **no sobrescribe** un GLB anterior: si ya existe, sólo acepta SHA coincidente con el reporte. La prueba de rig del candidato ejecuta `tools/maniqui/auditar_v03.py` y la evaluación de las 29 animaciones usa `tools/maniqui/evaluar_v03.py`.

## Estado de aprobación
Ningún PR fusionado; r3 ni Delta ni Theo Alpha modificados; nada de esto se considera una nueva base aprobada. La línea de modelos sin Hunyuan se mantiene separada de estos experimentos históricos.

**Cadena:** G2 PR #40 sobre #39 (Visual Critic real), depende de PR #38 (Visual Critic + kernel) y #37 (matemáticas). Resultados confirmados por [CI de máscaras y contornos](https://github.com/Klymapo/COPOX/actions/workflows/maniqui-g2.yml) y [CI de GLB](https://github.com/Klymapo/COPOX/actions/workflows/maniqui-g2-cut-probe.yml). Todos sus artefactos de Actions duran 30 días.
