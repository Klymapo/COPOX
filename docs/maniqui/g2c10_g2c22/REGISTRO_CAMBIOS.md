# COPOX — Bitácora de laboratorio G2-C10 a G2-C22

**Fecha:** 2026-10-15 · **Operador:** Argos desde ChatGPT (no Codex) · **Estado:** TODO SIN APROBAR.

## Resumen
Serie experimental local sobre maniquí G2-C8: extrusión de nariz, extensión a pómulos/entreceja, caps faciales, restauración/recreación de ojos y cejas. **No se sustituye, fusiona, promociona ni borra ningún modelo.** Esta rama documenta resultados, no certifica su calidad.

Se localizaron localmente y empacaron **13 archivos GLB**, **48 PNG**, **27 scripts Python** y **13 JSON**. Dos ZIPs descargables quedan adjuntos al chat de trabajo, *no se declara subida de esos binarios a GitHub ni a Drive*. El reporte maestro de Gaston → APPS → COPOX se actualizó el 2026-10-15.

## Registro de cambios, versiones, hashes (SHA256)

| Versión | GLB / estado | SHA256 | Hallazgo |
|---|---|---|---|
| G2-C10 | maniqui_G2C10_NARIZ_EXTRUIDA_SIN_APROBAR.glb | `7b5b3c8f2ff807d1f319bfccbdf696b02ae6afc2e4f826234ccd51833b8b4fc1` | Nariz extruida hacia el interior de la cabeza; parte queda oculta; todavía no soldada. |
| G2-C11 | maniqui_G2C11_BASE_NARIZ_EXTENDIDA_SIN_APROBAR.glb | `49550d6f298911c6d24f0fdc4c12a95486386e3a81c2c8a5fc8f05d80f6fca26` | Collar nasal extendido para tapar hueco facial central. |
| G2-C12 | maniqui_G2C12_POMULOS_ENTRECEJA_SIN_APROBAR.glb | `b63b4d7506aa95d00632f48c35f7eb7e18e551f1d9bd6753eea7294e4abffcee` | Ampliación hacia pómulos y entreceja; placa anatómicamente plana. |
| G2-C13 | maniqui_G2C13_ROSTRO_COSIDO_SIN_APROBAR.glb | `7fbd00d59c8ceb2f0867decaa918ccc5184ea39b6e9a13a7c90487ae745df60e` | Puente de 30 triángulos hacia 15 vértices faciales. No demuestra malla manifold. |
| G2-C14 | maniqui_G2C14_ROSTRO_CERRADO_SIN_APROBAR.glb | `1a6b1256f2bb081785eaf4965fbbfe1a6175e368e646faca24c284230c48e886` | Cap facial de 13 triángulos, solapamientos sobre ojos. |
| G2-C15 | maniqui_G2C15_CIERRE_FINO_SIN_APROBAR.glb | `7728857f2e6fa6e7d0f5d58ff4a0dae9980171c80199b642b92a7d34ab8e9cb3` | Cap más ancho de 14 triángulos; parche base de las pruebas de ojos posteriores. |
| G2-C16 | maniqui_G2C16_OJOS_CEJAS_SIN_APROBAR.glb | `afaa3303960e417fdbb9d8aa7bfa5cdbd9c98598cbf39d9172a5655b96ec411b` | Primitivas NUEVAS de esclerótica, iris, pupila, delineado y ceja. |
| G2-C17 | maniqui_G2C17_OJOS_CEJAS_RECUPERADOS_SIN_APROBAR.glb | `2f42957a54087ce114581c04c3dc5f07cc730aae0e8bca1f1a3af1d8974a9d7b` | Segunda recreación, no rasgos genuinos anteriores al parche. |
| G2-C18 | maniqui_G2C18_OJOS_ORIGINALES_SOBRE_PARCHE_SIN_APROBAR.glb | `c8acb0f606ae4c1f0da3c0affe0092cf19bc5beeabed1cdf885d85318d517584` | Ensayo restauración de UV/rasgos de Gamma; interferencia. |
| G2-C19 | maniqui_G2C19_OJOS_ORIGINALES_SELECTIVOS_SIN_APROBAR.glb | `90f38f0d6e2aa53d1d3281cc2207ca3405d9a00af90e3ff51526ae442481f7bc` | Restauración parcial selectiva, rasgos aparecen grises en un raster sin textura. |
| G2-C20 | maniqui_G2C20_OJOS_CEJAS_VISIBLES_SIN_APROBAR.glb | `f834494bcd523159910e4a853b9c17aff2620a1b7c54e017c79c78a36d7cd1bc` | Ojos/cejas de G2-C17 superpuestos a G2-C19. Duplicación de capas. |
| G2-C21 | maniqui_G2C21_OJOS_LIMPIOS_SIN_APROBAR.glb | `7a6060b5245dcb829c670607ef4f800e5c53a16570265a4f1ee1611b7d019af3` | Retirada completa de primitiva GammaHead #24 (674 triángulos), más amplia que el recorte ocular. |
| G2-C22 | maniqui_G2C22_OJOS_CEJAS_AJUSTADOS_SIN_APROBAR.glb | `725f99c66d465510751764783ccfa50896c299d5fef22a72ccc8326dc0843422` | Último ensayo: ojos reducidos/elevados y cejas más finas/anguladas. |

## Origen y ramas
`G2-C8 → G2-C10 → G2-C11 → G2-C12 → G2-C13 → G2-C14 → G2-C15`.
Desde G2-C15 salen G2-C16 y G2-C17 como recreaciones, mientras el camino de recuperación es `G2-C15 → G2-C18 → G2-C19 → G2-C20 → G2-C21 → G2-C22`. El candidato G2-C22 no está aprobado; no equivale a ojos originales recuperados sin modificación.

## Límites y fallas pendientes
- Los caps y costuras visibles **no prueban que el rostro sea una única malla topológicamente soldada ni manifold**; hay superposiciones, posibles agujeros, normales sin QA exhaustivo y triangulación pobre de la glabela.
- Los ojos originales de la fuente aparecían con material gris en vistas Python; G2-C20 utilizó ojos recreados como overlay, y G2-C21 ocultó toda la primitiva texturizada GammaHead, no solamente su zona ocular.
- Los informes muestran 56 huesos y 29 *entradas* de animación, **sin validar íntegramente clips, deformación de rig ni importación nueva en Godot**. Las morph faciales de origen continúan sin rehabilitación acreditada.
- Las capturas son **proyecciones de los GLB con raster Python**, no capturas certificadas Blender o Godot. Likeness y sombras deben auditarse contra referencia real.
- Perfil cráneo/mandíbula/cuello, adhesión de orejas y línea subocular siguen pendientes.
- Scripts originales del laboratorio incluyen rutas absolutas `/mnt/data`. El paquete de código local debe adaptarse antes de usar en Codespaces.

## Respaldo, autorización y siguiente paso
En el chat se prepararon `COPOX_G2C10_G2C22_TODOS_LOS_GLB_2026-10-15.zip` (~161 MB) y `COPOX_G2C10_G2C22_CODIGO_CAPTURAS_2026-10-15.zip` (~5.1 MB), con manifiesto SHA256 y reporte. La subida a Drive/GitHub de BINARIOS aún necesita confirmación; no atribuirles enlaces inexistentes.

**Registro de cambios — 2026-10-15:** nueva rama documental independiente, se ingresaron descripción de los 13 ensayos y hashes de GLB; se actualizó en Gaston la memoria maestra «01 — COPOX · Memoria maestra integral». No se fusionó nada; no se borró ni sustituyó material.
