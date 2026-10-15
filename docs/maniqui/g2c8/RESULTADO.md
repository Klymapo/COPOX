# G2-C8 · color uniforme y auditoría de huecos (2026-10-15)

Estado: **mejora local de color; refinamiento geométrico en PLATEAU; sin aprobación visual ni promoción**. El archivo de partida es el G2-C7 V2 experimental (`0efe44e912a23c2dfae2be850494d7e8a93475606af5e08ba49e69e536daed63`), que se conserva intacto. El nuevo candidato es `build/g2c8/maniqui_G2C8_COLOR_UNIFORME_SIN_APROBAR.glb`, SHA-256 `bf4ec71a56e94c61c3933c7194ec44026b6e8c31648175f4c497ba167c139e50`. Procedimiento reproducible: `python3 tools/maniqui/g2c8_uniform_skin.py`.

## Modificación aplicada

Las primitivas 3–23 (torso, brazos, manos, piernas y pies) reciben exactamente el mismo material de piel que la cabeza, índice 25, color base lineal `[0.7764705882352941, 0.5843137254901961, 0.4745098039215686, 1]`. Ojos y cejas de la primitiva 24 conservan su atlas. Cero triángulos agregados/eliminados y cero vértices modificados; todos los buffers binarios, nodos, skin, materiales definidos y animaciones son idénticos. El color en pantalla varía por normales y luces, a pesar de compartir material.

## Diagnóstico de huecos y uniones

- Torso (primitiva 3), ambas piernas (4–5), ambos brazos (6–7), palmas (9/17) y pies (15/23) ya son superficies cerradas: **cero aristas de borde** por primitiva. En un GLB de superficie, esas envolturas definen el volumen interior; rellenarlo con polígonos internos sólo crearía geometría superpuesta. Esto no significa que todas las piezas formen una sola malla continua ni que sus uniones sean visualmente correctas.
- La cara (primitiva 0) tiene 44 ciclos de borde espacial, incluido uno de 413 vértices que recorre cara y mandíbula; calva (1), uno de 164; cuello (2), dos de 36. Los conectores de muñeca tienen dos anillos de 24 y cada dedo un anillo de 12.
- Los anillos abiertos de los dedos están en **su base**, dentro de la palma. Se abortó un ensayo de tapa antes de exportar al comprobar su orientación y posición. Taparlos habría añadido intersecciones internas, no mejorado las yemas ni suavizado una unión visible.
- El pliegue central de la frente pertenece a la geometría fragmentada de la cara entre cejas y puente nasal; el casco de calva permanece liso. Los parches faciales R1/R2/R3 de G2-C5 fallaron por cruces, nuevas aristas no manifold o persistencia visual del defecto. No se repitió ese método ni se desplazaron vértices de ojos, cejas, nariz o calva sin una reconstrucción segura.
- Persisten huecos faciales, discontinuidad mandibular-cuello y uniones de hombro/mano visibles. La vista lateral revela además deformación grave ya presente en V2. Por ello el candidato **no satisface** la solicitud geométrica completa y queda bloqueado para promoción.

## Evidencia y compatibilidad

Capturas reales del GLB exportado e importado por Blender 4.3.2 en `build/g2c8/captures/COLOR/`: frontal, perfiles izquierdo/derecho, posterior, tres cuartos derecho, rostro, nariz y oreja. Comparativa con mismas cámaras y luces: `build/g2c8/COMPARATIVA_REAL.png`. Script de render: `build/g2c8/render.py`.

Godot 4.7.2 headless: GLB bruto error 43 heredado; copia de compatibilidad `build/g2c8/COLOR_compat.glb` importa con error 0 y conserva 25 superficies, 56 huesos y 29 clips enumerados. De 145 muestras de pose ósea, todas coinciden con L1; diez clips tienen movimiento óseo. Quince canales morph faciales huérfanos se eliminan sólo en la copia compatible y no deben declararse funcionales. Reportes: `docs/maniqui/g2c8/COLOR.json`, `COLOR_compat.json`, `build/g2c8/godot/godot_report.json`.

Siguiente mejora viable: reconstrucción craneofacial con fuente de referencia sólida y transferencia de skin/morph auditada, seguida de unión mandibular-cuello medida. Este paso requiere un nuevo experimento regional con comparación artística; no puede inferirse de un cierre automático de bordes. Ninguna versión anterior se ha sobrescrito o aprobado.
