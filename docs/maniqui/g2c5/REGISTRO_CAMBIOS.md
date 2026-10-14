# G2-C5 · Relleno experimental conservando la versión nueva
**14 oct 2026 · NO APROBADO · Sin fusionar · Sin reemplazar GLB**

Partimos de la rama/PR #47 (G2-C4) y de cuatro GLB verificados por SHA256: V3 (`0a100a9400...`), A (`e5660a56...`), B2 (`daf3737d...`), C (`3a045ef...`). El usuario pidió conservar la forma nueva y rellenar huecos, no revertir a V3.

## Intervenciones materializadas en GLB (laboratorio externo al repo)
- Se mantuvo B2 (71 caras de montura retiradas) y el ajuste C de mandíbula, pese a su rechazo anatómico previo; no se oculta ese estado.
- Se seleccionaron los 156 triángulos que A había quitado detrás de la oreja derecha y se reconstruyeron 120 del área verdaderamente anclada. Los 36 triángulos aislados se mantienen rapados. La reparación mueve **84 vértices internos**, preserva **19 del borde**, aplica Laplaciano 30% y no invierte las 120 caras reparadas. **Aún queda hueco lateral**, por lo que no es una reparación completa.
- Se generó una **variante conservadora G2-C5** que sólo combina esas correcciones. SHA256 `34ccc30b0f5565204c2b16395daff8d6303da869dbf432ef51b8db6080e8e070`.
- Se generó otra **variante óptica experimental** con 2,196 caras nuevas detrás de vacíos faciales y 240 para la región submandibular. Los paneles no están soldados al perímetro y generan artefactos estéticos. **Rechazada como solución final**, conservada sólo para investigación. SHA256 `908aef0e812c4997e6e241691fdfebbb7e4caeb844e310da88a962414a278342`.

## Evidencias y QA
- Se generaron seis vistas de cada modelo con rasterizador local y culling de caras posteriores; la comparación muestra V3, A (hueco), G2-C5 conservadora y G2-C5 óptica.
- Ambos archivos GLB reimportan a `trimesh` (34 geometrías) y conservan 56 huesos, 29 definiciones de clips, escenas, nodos, materiales y primitivas fuera de Cabeza. Originales no sustituidos.
- **No se ejecutó Godot en esta ronda.** No declarar animaciones faciales funcionales, retopología manifold ni neck anatómico. Los defectos de importación glTF maestros son históricos.
- **Conclusión:** avance parcial en relleno detrás de oreja y combinación reproducible; no autorizar promoción. El ojo aún necesita cirugía de borde auténtica; la mandíbula C todavía no forma un anillo de cuello útil.

## Artefacto persistente
Paquete ZIP comprobado en **Drive Gaston → APPS → COPOX** con dos GLB, scripts, comparativas y reportes:
https://drive.google.com/file/d/1M4Yw3WiRt6_j3uKScRTD9ojKha2SttOF/view?usp=drivesdk

Este PR registra el trabajo. **Los binarios y scripts reproducibles están en el ZIP de Drive, no añadidos al GitHub**, para no sobreescribir modelos ni inflar el repositorio sin aprobación.

## REGISTRO DE CAMBIOS
2026-10-14: el usuario aprobó continuar sobre geometría nueva G2-C4. Se construyeron dos candidatos (conservador/óptico), inspeccionaron seis vistas por versión y se descartó el óptico por artefactos; se preservó el conservador como prototipo local. Bitácora y paquetes en Gaston. Pendientes: soldadura real de límites detrás de oreja, retopología de ojos, anillo anatómico mandíbula-cuello, importación Godot y revisión artística. NO MERGE.
