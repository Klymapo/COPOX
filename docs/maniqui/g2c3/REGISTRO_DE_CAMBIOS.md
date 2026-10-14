# COPOX · G2-C3 — Continuidad de calva, nuca y rapado local

**Estado:** PROTOTIPO / SIN APROBACIÓN ARTÍSTICA — PR borrador #45, no fusionar.

## Diagnóstico
El parche G2-C2 «suavizada» no modificaba suficientemente la silueta porque
añadía una banda solo bajo una pequeña sección de la calva existente.
Las facetas de «Cabeza» seguían sobresaliendo detrás y junto a las orejas.

## Tratamiento nuevo
Se parte del borde real de la primitiva \`Craneo\` del GLB histórico r3,
con un arco contiguo mayor que el de 34 aristas del G2-C2. Se construyen
cinco niveles descendentes curvos y estrechamiento progresivo hacia la nuca.
El borde superior original sigue compartiendo exactamente sus índices;
ningún vértice antiguo del cráneo se desplaza.

El rapado actúa sobre **índices de triángulos** de la primitiva \`Cabeza\`,
no sobre los vértices ni morph targets. Se descartan candidatos totalmente
posteriores y, de modo conservador, patillas laterales ubicadas por detrás
del rostro. La operación usa un **veto por vértice** para proteger:
- parte anterior del rostro (cualquier vértice z ≥ +0.075);
- orejas y margen: |x| ≥ 0.187, y ∈ [0.605,0.805], z ∈ [-0.17,+0.164].
Si una sola esquina está en esas zonas, el triángulo completo permanece.

Nota: los límites son valores anatómicos aproximados de **r3**; no son
parámetros reutilizables sin calibración con otro personaje o malla.

## Candidatos separados y sus diferencias
- **conservador:** retira solo facetas de pelo que cumplan z < -0.098 y patillas z < -0.025; caída máxima prevista 0.158 m.
- **completo:** amplía el recorte posterior hasta z < -0.075 y patillas hasta z < +0.012; caída máxima prevista 0.188 m.
Ambos permanecen en GLB *hermanos*, con sufijo \`SIN_APROBAR\`.

## Verificación objetiva (no reemplaza evaluación artística)
1. Fuente GLB r3 comprobada con hash SHA256 fijo.
2. Rig 56 huesos, 29 definiciones de animación, materiales, nodos, pesos y morph targets no editados.
3. Todos los triángulos originales del cráneo permanecen intactos. La malla de Cara pierde solamente caras clasificadas fuera del área protegida.
4. En ninguna variante se borra un triángulo que toque un punto de rostro u oreja protegido.
5. Seis vistas de los GLB reales, mismas cámaras y encuadre, diferencia en píxeles.
6. Importación triple con Godot 4.7.2 oficial — r3, conservador, completo — como prueba estructural, no de animación funcional.
7. No se afirma watertight, unión completa cráneo-cara ni likeness aprobado.
8. Criterio de rechazo automático si menos del 2.5 % de la captura posterior difiere del original.

## Archivos y evidencias
- Script: \`tools/maniqui/g2c3_surface_rebuild.py\`
- Workflow: \`.github/workflows/maniqui-g2c3-visible-nape.yml\`
- Reporte resultante: \`docs/maniqui/g2c3/visible/REPORTE_G2C3.json\`
- Captura seis vistas: \`docs/maniqui/g2c3/visible/G2C3_ANTES_DESPUES_6V.png\`
- Triángulos nuevos resaltados: \`docs/maniqui/g2c3/visible/G2C3_NUEVA_SUPERFICIE_6V.png\`
- Los GLB resultantes se entregan como artifact de Actions, no se promueven al repositorio de producción.

## REGISTRO DE CAMBIOS
**2026-10-14** — Respuesta a revisión artística: rechazo de la solución G2-C2 por escasa diferencia visible. Se creó \`experimentos/g2c3-nuca-superficie-visible\` y PR borrador #45 desde el resultado de G2-C2. Implementados dos cortes de pelo por ROI protegida, continuidad desde la calva original hasta nuca inferior, verificación de visualización en seis cámaras y ensayo en Godot 4.7.2. **PENDIENTE**: resultado del workflow y revisión visual real. No se eliminó ni sustituyó ningún modelo anterior; no se fusionó.

**2026-10-14 · Ejecución y auditoría de G2-C3 v1.** Workflow #38627282410: SUCCESS; 56 huesos, 29 animaciones nombradas y 24 superficies preservadas tras importación Godot 4.7.2 en las 3 variantes. Dos GLB reales preservados solo en artifact #11923879581, no fusionados. Perfil completo: 540 caras de nuca nuevas y 275 vértices; 980 triángulos traseros retirados, 34 de patillas; 0 triángulos protegidos afectados; 7.412 % de los píxeles de espalda cambiados. **Veredicto artístico: NO APROBADO**, aunque el cambio es ahora visible, porque el primer relleno presenta franjas marcadas y algunos restos laterales. Reales: `docs/maniqui/g2c3/visible/G2C3_ANTES_DESPUES_6V.png`.

**2026-10-14 · Segunda iteración G2-C3 v2 lisa.** Nueva rutina y workflow independientes `tools/maniqui/g2c3_surface_rebuild_v2.py`, `.github/workflows/maniqui-g2c3-smooth-v2.yml`; v1 preservada. Se sustituyeron **solo en el algoritmo v2** 5 bandas por 18 anillos de descenso progresivo, 990 vértices + 1944 caras nuevas; recálculo exclusivo de normales añadidas, 55 vértices de borde original compartidos, 0 vértices antiguos modificados, orientación normal exterior confirmada (~0.18). El perfil conservador_v2 elimina 900 triángulos traseros + 34 de patillas; el completo_v2 998 triángulos traseros + 34 de patillas + **46 triángulos de un mechón lateral aislado topológicamente**, confirmando la firma de 46 caras antes de rapar para no tocar el pabellón principal. Cero caras clasificadas como oreja o rostro protegido eliminadas. Comparación real de v2 en 6 vistas: `docs/maniqui/g2c3/visible/v2/G2C3_ANTES_DESPUES_6V.png`; resalte de nueva superficie `docs/maniqui/g2c3/visible/v2/G2C3_NUEVA_SUPERFICIE_6V.png`. Perfil completo v2: 6.535 % píxeles posteriores distintos de r3, GLB SHA256 `b7998d382f13ef8997a2dc2f73539a61da9ec5aa27605897534b13d47f3517e6`; conservador_v2 GLB SHA256 `ae5270ff2c94d836adfd8424d90fe40e3ba800d2311dc99ee1243aa95d765a44`. Workflow oficial Godot 4.7.2 **SUCCESS #38627886457**, artefacto dos GLB con evidencia #11926060091 (30 días): https://github.com/Klymapo/COPOX/actions/runs/38627886457/artifacts/11926060091 . **Juicio visual**: mejora apreciable y menos franjas, pero no se declara corrección completa de patillas ni cierre facial; existen salientes laterales residuales, huecos de la cara y la conexión con cuello/cara no es manifold. No modificar facciones u orejas sin nueva auditoría. Sin fusión ni sustitución del r3 o versiones anteriores.
