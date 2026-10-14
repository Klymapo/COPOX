---
name: contour-extractor
description: Extrae y verifica bucles topológicos dirigidos de mallas 3D. Rechaza UV seams, fragmentos, aristas nonmanifold y contornos anatómicos no aprobados; compara todas las vistas de referencia.
---

# COPOX · Contour Extractor G2-C

## Activación
Antes de cualquier Surface Stitch, Anatomic Cut, loft o reparación de borde facial, en personajes y otros assets.

## Entradas
GLB y SHA-256, selección inequívoca de pieza, índices y primitiva, `reference_manifest` de TODAS las imágenes/vídeos aportados, landmarks anatómicos validados, unidades y orientación. No mezclar dos personajes aunque sus referencias estén juntas.

## Proceso obligatorio
1. Ejecutar `visual-critic` contra **todas** las referencias de la identidad correcta; exigir cobertura y registrar contradicciones por vista.
2. Con `copox.geometry.kernel.boundary_loops(faces)`, extraer aristas con incidencia en exactamente 1 cara; un borde sin manifold requiere reparación previa. **Nunca** detectar bordes con `mesh.edges_unique_length == 1`: esa propiedad mide distancias, no incidencia topológica.
3. Distinguir agujeros físicos de seams por UV duplicadas. La agrupación por posición sirve sólo como diagnóstico, no como soldadura.
4. Una referencia frontal no decide por sí sola una patilla o nuca. Identificar contornos por región, si hace falta recortar la isla grande, proteger ojos/cejas/nariz/orejas/mandíbula. No inferir un loop de Cara por su proximidad a Cráneo.
5. Registrar índices orientados, dirección de winding, conectividad, correspondencia por landmark, distancia de borde, clasificación de islas y matriz de evidencias por referencia.
6. **GATE**: exactamente dos bucles reales no ramificados, anatómicamente homologables, elegidos explícitamente. Si falla, STOP; no invocar motor de costura ni generar GLB.
7. Ejecutar `python -m tools.maniqui.g2c_r3_preflight` como ejemplo negativo real: r3 debe quedar bloqueado. Este veto no es un error del motor.

## Salida
JSON de contornos auténticos, máscaras y atribución a todas las vistas, SHA y acta `READY_FOR_STITCH` o `BLOCKED`. No aprobar por mera coincidencia de posiciones; no modificar el baseline.

## G2-C2 · Alastor sin lentes (requisito artístico)
El objetivo de la cabeza es **SIN montura, cristales, puente ni patillas de lentes**. Consultar `copox.geometry.eyewear_guard` y `tools.maniqui.g2c2_no_glasses` antes de delimitar el nuevo contorno. El maniquí histórico movió la pieza etiquetada `Lentes` al GLB separado `ropa_alastor_v0.glb`: NO reutilizar esa pieza al reconstruir frente o sienes. Si hay residuos sin etiqueta mezclados con los triángulos de Cara, clasificarlos como `REVIEW_REQUIRED` por zona, **no borrar ojos, cejas, párpados ni orejas** para quitarlos. Comparar cada vista original provista, y documentar si quedaron rastros de patillas sobre sienes.
