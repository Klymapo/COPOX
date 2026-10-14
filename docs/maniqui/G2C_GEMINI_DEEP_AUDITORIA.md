# COPOX G2-C · Revisión de Gemini/Deep y motor de costura seguro

Fecha 2026-10-14. **PR experimental**, no modificar `main`, no sustituir r3 ni candidatos G2/G2-B. Base: `experimentos/maniqui-g2b-piel-craneofacial`.

## Dictamen técnico de la propuesta compartida por Gemini
Se reconoce el valor de usar un greedy advancing front para costurar **dos loops orientados** de distinta longitud. Sin embargo, el código aportado NO se integra literalmente porque:
- `trimesh.edges_unique_length == 1` **no cuenta incidencias**: es una longitud geométrica; para aristas de borde, debe contarse su aparición en exactamente un triángulo.
- Los resultados de r3 prueban que el rostro tiene multitud de bordes y fragmentos; no existen exactamente 2 loops genuinos. Ningún método de greedy convierte una cara fragmentada en un único loop semánticamente válido.
- `trimesh.load(..., force="mesh")` aplana la escena/GLB y NO garantiza preservar rig, skins, UV, materiales ni animaciones. Y `Trimesh(vertices,faces).export()` no restituye mágicamente 56 huesos.
- Elegir la diagonal más corta es un criterio local útil, pero **no garantiza ausencia de autointersecciones ni calidad anatómica**.
- `trimesh.smoothing.filter_taubin` mueve vértices sin máscara. Contradice el requisito de no deformar el rostro y no debe ejecutarse globalmente.
- Deben verificarse aristas con winding compatible, longitudes de puente, triángulos degenerados, soporte UV/skin/morph y cuatro vistas reales.
- Un cierre de la primitiva `Craneo` no implica costura a otra primitiva `Cabeza` (hallazgo G2-B previo).
- Deep acertó respecto a estructuras espaciales y determinismo, pero la velocidad 10–100× de Numba **no ha sido medida** y no debe proclamarse.

## Implementación efectiva
- `copox/geometry/advancing_stitch.py` añade greedy determinista con `cKDTree` para par inicial, sin matriz NxM; un paso por cada arista de los dos bucles, N+M triángulos. Puede conectar bucles de distinta cardinalidad, con winding opuesto y MISMO espacio global indexado.
- `copox/geometry/surface_stitch.py` incorpora `stitch_parts_unequal`, que preserva `JOINTS_0`, `WEIGHTS_0`, `NORMAL`, `TEXCOORD_0`, `TEXCOORD_1`, `COLOR_0` y el material por cara **dentro de los arrays en memoria**. Rechaza diferencias de atributos y morph targets sin soporte.
- Validación: se comprueban dos loops verdaderos con `boundary_loops`, winding, cardinalidad libre (>=3 por loop), distancia máxima de TODAS las aristas cruzadas, triángulos degenerados y ratio de lados, nonmanifold por incidencia indexada, y ausencia de bucles restantes. No suaviza ni modifica los vértices de entrada.
- **No existe todavía serializador GLB para geometría cosida con múltiples materiales, skin y morphs que mantenga una única topología en Godot.** El motor da un resultado geométrico de memoria, no un modelo aprobado.
- Autointersecciones **no comprobadas**; output `production_ready=false`. Que todas las aristas tengan incidencia 2 y winding coherente es necesario, pero **no suficiente** para declarar una superficie física sin cruces.

## QA automatizada
- `tests/test_g2c_advancing_stitch.py`: anillos 12/19, 16/16, 128/257, datos degenerados, no-manifold, loops falsos, orientación opuesta, distancia excedida, calidad de triángulos y reproducibilidad determinista.
- `tests/test_g2c_surface_parts.py`: UV + skin + materiales por cara y fail-closed ante atributos incompatibles, pesos no normalizados y morphs.
- `tools/maniqui/g2c_r3_preflight.py`: analiza la malla de Maniquí r3 original SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b` y **bloquea** cualquier emparejamiento directo del supuesto par único de anillos. Entrega `docs/maniqui/g2c/REAL_R3_PREFLIGHT.json` sólo en artifact.
- `.github/workflows/maniqui-g2c.yml`: Python 3.11 y dependencias gratuitas ancladas en versiones compatibles, sin tokens externos, sin IA generativa, sin cambios de modelos. El CI sólo verifica matemática y seguridad, no la apariencia.

## Skills creadas e instaladas para ambos agentes
Cada una tiene el mismo SKILL.md en `.codex/skills` y `.claude/skills`:
1. `contour-extractor`: extraer un perímetro de Cara anatómicamente correcto, contrastado contra TODAS las referencias, sin confundir seams UV con agujeros físicos.
2. `stitch-advancing-front`: ejecutar el motor de loops desiguales y verificar topología/dimensiones, con rechazo explícito de autointersecciones no comprobadas.
3. `gltf-rig-guardian`: conservar UV/material/skin/morph/animaciones en exportación; Godot y muestras temporales; los 15 canales faciales huérfanos históricos siguen pendientes de Facial Acting.

Secuencia: **Visual Critic → Contour Extractor → Anatomic Cut localizado (si realmente hace falta) → Stitch Advancing Front → GLTF Rig Guardian → pruebas de Godot → auditoría artística de todas las vistas → autorización de Admin**.

## Próximo umbral antes de coser un modelo real
Extraer el contorno facial principal en r3 sin borrar facciones (17 islas pequeñas + gran isla), homologarlo visualmente con el borde craneal de 128 vértices, comprobar que la costura no atraviesa orejas/cejas/ojos, disponer de export GLB multiatributo y probar las poses de los 13 clips con claves cambiantes y las expresiones aún por recuperar. Si faltan correspondencias artísticas, devolver `BLOCKED` sin generar falsa reparación.

**Sin fusiones, aprobación de modelos, sustitución de GLB, ni borrados de fuentes.**
