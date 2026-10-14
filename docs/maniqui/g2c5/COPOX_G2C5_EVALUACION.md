# COPOX — G2-C5 · Combinación y rellenos locales (laboratorio)

Fecha: 14 de octubre de 2026. Estado: **SIN APROBAR / NO FUSIONAR**.

## Procedencia y decisión
El usuario pidió conservar la geometría nueva evaluada en G2-C4 y rellenar los espacios blancos, en vez de regresar al modelo anterior. Se tomaron como orígenes verificados por SHA256 los modelos V3, A, B2 y C del paquete de G2-C4 de Drive. No se modificó ningún GLB de origen.

Se produjeron **dos nuevos GLB hermanos**:

1. `COPOX_G2C5_REGIONALES_CONSERVADOR_SIN_APROBAR.glb`: combina B2 (71 triángulos de montura eliminados), propuesta C de mandíbula (40 vértices originales editados), el rapado derecho A (156 triángulos seleccionados) y reconstruye **120 triángulos conectados al borde** de la región derecha, suavizando únicamente 84 vértices internos. Mantiene fuera **36 triángulos** de fragmentos sueltos y conserva 19 vértices de borde. **No hay inversiones** en los 120 triángulos reconstruidos. La zona detrás de la oreja mejora parcialmente pero **queda un hueco lateral visible**.

2. `COPOX_G2C5_CANDIDATO_SIN_APROBAR.glb`: contiene lo anterior y además 2,196 triángulos de respaldo facial y 240 triángulos submandibulares experimentales. Es un **experimento óptico de relleno**, NO una unión física: los parches no comparten el borde de la malla original, y pueden verse bordes artificiales alrededor de los ojos. **Rechazado como modelo final**. Se conserva únicamente para evaluación y para diseñar una retopología verdaderamente soldada.

## Evaluación
- Los GLB superaron lectura estructural mediante `trimesh` (34 geometrías) y comparación de metadatos de `skins`, `animations`, `nodes`, `materials` y resto de primitivas con C; 56 huesos, 29 definiciones de animación conservadas.
- Previsualización local de 6 vistas reales (raster con ocultación de caras posteriores). **No hubo ejecución de Godot 4.7.2 en esta iteración.**
- Los morph targets vacíos y defectos glTF de G2-C4 siguen siendo históricos; no hay garantía de movimiento facial funcional ni de mallado hermético.
- **Mandíbula/neck no aprobados anatómicamente**: se incluyó la propuesta C solo por solicitud de preservar la variante nueva, sin declarar unión válida al cuello.
- Ninguna variante está aprobada y no se han reemplazado originales.

## Próxima ingeniería antes de aprobar
1. Retopología **de borde real** tras la oreja derecha para cerrar el último hueco y conservar su pabellón.
2. Reconstruir la piel facial tras las gafas mediante polígonos conectados al borde y materiales/pesos correctos, sin parches flotantes, sin tapar ojos.
3. Diseñar anillo de transición mandíbula-cuello con loops medidos y skin continuo, no con superficies ópticas.
4. Ejecutar importación Godot, poses y comprobación de morph targets, y volver a mostrar seis vistas con comparaciones.

## Archivos
- `COPOX_G2C5_COMPARATIVA_6V.png` muestra V3, G2-C4 A, variante conservadora, variante óptica experimental (seis vistas por versión).
- Ambos GLB junto con scripts, reportes y comparativas en `COPOX_G2C5_ENTREGA_EXPERIMENTAL.zip`.
- Base G2-C4: https://github.com/Klymapo/COPOX/pull/47 .

## REGISTRO DE CAMBIOS
14-oct-2026: creada rama de notas `experimentos/g2c5-relleno-regional-candidatos` desde #47. Salidas binarias generadas en el laboratorio de ChatGPT, suministradas separadamente, **no subidas al repositorio**. Conservar status experimental; ninguna fusión/autopromoción.
