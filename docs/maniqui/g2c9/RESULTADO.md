# G2-C9 · Huecos y suavizado facial (2026-10-15)

**Resultado: PLATEAU; ningún candidato se promueve.** Base inmutable G2-C8 color uniforme SHA-256 `bf4ec71a56e94c61c3933c7194ec44026b6e8c31648175f4c497ba167c139e50`. Tres ensayos hermanos, todos derivados directamente de esa base. No se editó G2-C8 ni se fusionó nada.

## Diagnóstico medido

El rostro de la base presenta 44 ciclos de borde en la superficie de piel, incluido uno de 413 vértices que mezcla cara y mandíbula; al reunir la superficie de ojos/cejas por posición, aparecen 57 ciclos por la fragmentación y costuras del atlas. La zona glabelar entre cejas y nariz es una isla separada de 110 triángulos con un borde exterior de 32 vértices y tres aberturas interiores de 3, 3 y 4. La captura diagnóstica de iluminación emisiva `build/g2c9/emission/COLOR/detalle_rostro.png` demuestra que la franja oscura bajo los ojos es en buena parte sombreado/oclusión de superficies fragmentadas: no corresponde a un único contorno plano que pueda taparse sin invadir los ojos. La calva lisa no es el origen del pliegue central.

Blender seleccionaba automáticamente `Sit-pose` al importar el GLB. Las capturas iniciales comparaban ese clip, pero **no** eran T pose. Para la comparativa final se desactivaron la acción y todas las pistas NLA, se restauró `matrix_basis` de cada hueso y se renderizó la pose de reposo real. Las cabezas de LeftUpperArm, LeftLowerArm y LeftHand están en altura Blender Z=0.455, respectivamente X=0.135, 0.221, 0.366; el lado derecho es simétrico. Los brazos de la malla quedan extendidos horizontalmente. Todas las imágenes comparadas proceden de los GLB exportados, importados por Blender 4.3.2, con cámara e iluminación iguales.

## Tres ensayos independientes

| Ensayo | Archivo GLB / SHA-256 | Cambio y filtro geométrico | Juicio visual |
|---|---|---|---|
| H · mejilla | `build/g2c9/maniqui_G2C9_HUECOS_MEJILLAS_SIN_APROBAR.glb` / `4109abcfaf8e968fa5990a0a271a0f586bf85f9cf91252e9a06c799e33e0ba62` | Cerró dos triángulos pequeños bajo la mejilla izquierda; bordes soldados 617→611, non-manifold 1→1, cero cruces nuevos; cero vértices movidos. Un tercer parche de mejilla derecha se descartó antes de exportar porque aumentaba las aristas non-manifold. | **Rechazado:** las capturas frontal, perfil y acercamiento son idénticas píxel a píxel a G2-C8; los huecos que importan siguen visibles. |
| N · normales | `build/g2c9/maniqui_G2C9_NORMALES_ROSTRO_SIN_APROBAR.glb` / `64b35ea54929f0a014d4f18db1117106f4c702f4e39cd5569e787be246fcbed4` | Reparación de 99 normales de piel frontal basada en vecinos, sin mover geometría ni tocar atlas ocular. | **Rechazado:** suavizado insuficiente; persisten el pliegue y las bandas oscuras. |
| F · glabela | `build/g2c9/maniqui_G2C9_GLABELA_SUAVE_SIN_APROBAR.glb` / `2ebd757117bdfa2503db3b783f73936b5546607d157e22c585804b1770af3cce` | Cerró tres pequeños ciclos glabelares con cuatro triángulos; suavizó sólo la profundidad de 48 vértices interiores, desplazamiento máximo 0.003071 unidades GLB; borde exterior fijo, ojos/cejas/nariz punta intactos, sin cruces nuevos ni incremento non-manifold. | **Rechazado:** la mancha central se acentúa y el parecido empeora, pese a la mejora topológica local. |

Todos conservan 56 huesos, 29 definiciones de clip, pesos, materiales y estructura de skin. La funcionalidad de los morphs faciales sigue limitada por los 15 canales huérfanos heredados. Las copias compatibles derivadas por `gltf_sanitize.py` sirven para importar y renderizar; no se confunden con los GLB originales. No se afirma cierre completo de los huecos de ojos, nariz ni mandíbula.

## Comparativa T pose

`build/g2c9/COMPARATIVA_T_POSE_REAL.png`: columnas G2-C8 base / H invisible / F rechazado; filas frontal completo, perfil derecho completo y acercamiento frontal. H muestra por qué un resultado técnicamente correcto puede carecer de valor visual; F muestra por qué no se acepta el suavizado sólo por sus métricas. Las capturas finales originales sin montaje están en `build/g2c9/captures_tpose/`; las anteriores en `captures_huecos/` y `captures_glabella/` corresponden al clip `Sit-pose` autoseleccionado por Blender y no deben etiquetarse como T pose.

La comparación de píxeles con cámara idéntica confirmó H: 0 píxeles distintos en frontal, perfil y acercamiento. F cambia 436, 34 y 2910 píxeles respectivamente (umbral de diferencia por canal >4), pero el cambio local acentúa el defecto. Estas cifras miden diferencia, no calidad ni porcentaje de parecido.

## Próximo método necesario

La cara requiere reconstrucción anatómica de una superficie frontal coherente, con retopología guiada por la referencia, conservación explícita de ojos/nariz/boca, transferencia de pesos y evaluación de expresiones y poses. Las restauraciones de triángulos fuente R1–R3 y estos cierres pequeños han alcanzado un límite visual. No se debe continuar rellenando ciclos por inercia ni usar F como padre de otra versión. El GLB experimental más reciente que sigue como base de trabajo es G2-C8, sin aprobación final.
