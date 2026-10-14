# COPOX — Primera auditoría del Maniquí r3 real · Visual Critic × Motor Matemático
**Fecha:** 2026-10-14. **Estado:** DIAGNÓSTICO COMPLETO / CORRECCIÓN BLOQUEADA DE FORMA FUNDAMENTADA.

## Experimento reproducible
- Fuente: `assets/maniqui/maniqui_v0_3_r3.glb`, SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`.
- Rig intacto (no modificado): 56 huesos y 29 clips.
- Scripts: `tools/maniqui/r3_visual_critic_real.py`, `r3_segment_islands.py`, `r3_seam_readiness.py`.
- Workflow `.github/workflows/maniqui-r3-critic-real.yml` completó SUCCESS en [run #38606596422](https://github.com/Klymapo/COPOX/actions/runs/38606596422), runner estándar Linux, Python NumPy/SciPy/Pillow gratuito.
- Se usaron seis archivos de referencias relevantes versionados en `refs/`; referencias de cabello castaño/gafas vs hombre mayor canoso/barba de identidad no verificada. Todos pasaron por Visual Critic individualmente, pero cámaras `unknown`, no equiparables al cráneo gris calvo. El repertorio de vídeos/Drive/chat histórico no está garantizado como completo. Por lo tanto, **no calcular IoU artístico con dichas imágenes ni afirmar parecido**.

## Capturas reales de r3
- `r3_fourviews.png`: frontal, 3/4, perfil y trasera, pose base, GLB real.
- `r3_head_details.png`: las mismas cuatro vistas enfocadas a cabeza.
- `r3_face_islands_4views.png`: colores por conectividad geométrica; no implica que un componente sea malo.
- Artefacto Actions `r3-real-critic-all-references`: imágenes de comparación una por cada una de las seis referencias, reporte original de Visual Critic y todos los archivos de evidencia. Retención 30 días.

## Topología realmente medida
| Aspecto | Cabeza | Cráneo |
|---|---:|---:|
| Vértices originales | 5,647 | 4,097 |
| Triángulos | 3,894 | 8,064 |
| Componentes por índices | 297 | 1 |
| Componentes tras agrupar posiciones a 1 micrómetro SÓLO PARA DIAGNÓSTICO | 18 | 1 |
| Bordes abiertos por índices | 3,310 | 128 |
| Bordes abiertos tras agrupar posiciones | 898 | 128 |
| Aristas non-manifold tras agrupar posiciones | 1 | 0 |

Entre las **18 islas** geométricas, la dominante concentra **3,718 triángulos**. Las otras 17 suman **176 triángulos**; muchas cruzan máscaras de ojos/nariz/boca u orejas. Las islas pequeñas NO pueden borrarse automáticamente. El origen del defecto visual dominante está dentro de la isla grande y en la unión con el Cráneo, no meramente en piezas sueltas.

## Distancias entre bordes reales (sin soldadura)
- El borde de la cúpula tiene 128 aristas y 128 vértices.
- La cara presenta 898 aristas y 851 vértices en su frontera *agrupada por posición*; **no es un loop anatómico equivalente de 128 vértices**.
- Nearest-neighbor detecta sólo **90** vértices de borde facial distintos para los 128 del cráneo (**38 colisiones** de correspondencia).
- Distancia al vértice de borde facial más cercano, mediana: **10.719 mm**; percentil 95 **28.685 mm**, máximo **34.599 mm**.
- Mediana por zona: **frente 16.438 mm**, **sienes 10.463 mm**, **nuca 10.722 mm**.
- La búsqueda del vecino cercano puede seleccionar cejas, oreja o una placa, y NO es un algoritmo fiable de soldadura. El borde de Cara tiene además una arista non-manifold tras agrupar duplicados por posición.

**Veredicto Stitch:** `stitch_allowed=false`. Antes hay que localizar el contorno anatómico objetivo, separar facciones, limpiar topología con máscaras explícitas, resamplear bucles compatibles y transferir atributos. Soldar 128 puntos hacia sus 128 vecinos más cercanos sería incorrecto.

## Dictamen Visual Critic
- Referencias locales presentes: 6/6 comparadas individualmente; sin cámaras calibradas, con conflictos de identidad, por lo que `REVIEW_REQUIRED`.
- La irregularidad topológica está medida, pero las imágenes contextuales no constituyen prueba de *forma artística ideal*. El `geometry_plan.json` devuelve `RESEARCH_REQUIRED`/`INSUFFICIENT_EVIDENCE`: es el resultado **correcto del gate**.
- No se ejecutaron Scully/Anatomic Cut/Surface Stitch sobre r3 ni se exportó una falsa reparación. No se cambiaron ni rig ni animaciones ni modelos base.

## Próximo experimento recomendado (G2)
1. Crear máscaras regionales por **triángulo**, no por tamaño de isla: cejas/ojos/nariz/orejas/boca congeladas; frente/nuca/patillas diferenciadas. Verificarlas contra todas las referencias realmente del mismo personaje.
2. Segmentar el borde anatómico exterior del rostro principal y registrar su winding y landmarks; **evitar conectividad por proximidad sin criterio**.
3. Producir un nuevo `Anatomic Cut` que retire placas elegidas con evidencia; probar todas las vistas antes de conectar una cúpula.
4. Generar nuevo loop que admita resampleo a 128 puntos sin perder UV/skin/morphs; ejecutar `Surface Stitch` en UNA malla indexada común; validar export e import con varios materiales y rig.
5. Comparar antes/después con imágenes reales, animaciones y Godot. Si no mejora frente/perfil/3-4/espalda, declarar PLATEAU; no sobreescribir ninguna versión.

**No se puede certificar independencia legal de la geometría de r3 respecto a Gamma**. Esta prueba es investigación histórica y de motor; la nueva línea de modelos propios debe nacer de referencias con derechos verificables.

## Registro de cambios
- 2026-10-14: creada rama `experimentos/maniqui-r3-visual-critico`, PR borrador #39 basado en PR #38, sin tocar `main`.
- 2026-10-14: ejecutado workflow de cuatro vistas reales, las seis referencias comparativas, mapa de 18 islas y medidas espaciales de contornos; se bloqueó la corrección por falta de compatibilidad/topología y fuentes artísticas comparables.
- Ningún GLB alterado, ningún candidato aprobado, sin fusiones ni borrados.
