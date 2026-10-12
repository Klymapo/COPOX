# ALASTHEO · Auditoría para posible eliminación

Fecha: 2026-10-12. Esta auditoría no elimina el repositorio archivado.

## Contenido rescatado y comprobado

- La rama `main` de ALASTHEO tiene **19 blobs**. En `alth-meta` se verificó previamente que los 19 tienen rutas equivalentes: 9 idénticos en su ruta y 10 adaptados; la procedencia está en [alastheo-import.json](../alastheo-import.json).
- El libro de producción `.xlsx` importado coincide por SHA.
- La rama `assets/alpha-theo-alastor` incluye **dos archivos exclusivos**: `models/alpha/README.md` y `models/alpha/manifest.json`, preservados sin cambios en [legacy-alpha-branch/](../legacy-alpha-branch/).
- Entre las restantes variantes de rama se conservan aquí tres blobs documentales históricos: `structure-README.snapshot.txt`, `structure-assets-README.snapshot.txt`, `visual-methods-README.snapshot.txt`. Su SHA Git coincide exactamente con los originales.
- **Cuatro ramas:** `main`, `assets/alpha-theo-alastor`, `chore/repository-structure`, `docs/visual-references-and-methods`.
- **18 commits únicos accesibles** en esas ramas y metadatos de **2 Issues cerrados, 2 PR fusionados**, ambos sin comentarios, preservados en [HISTORY_INDEX.json](HISTORY_INDEX.json).
- Según la API al auditar: **sin releases, sin Pages y sin forks**. El indicador `has_wiki=true` solo señalaba la función habilitada; el **12 de octubre de 2026**, el propietario abrió `https://github.com/Klymapo/ALASTHEO/wiki` en su navegador autenticado y aportó captura que muestra la pantalla predeterminada «¡Bienvenidos a la wiki de ALASTHEO!» sin lista de páginas. El workflow de respaldo también encontró inaccesible/no inicializado el repositorio `.wiki.git`. **Conclusión operativa: Wiki sin páginas publicadas y sin contenido propio identificado para exportar.**
- Todo el material documental incorporado es histórico; **no sustituye** el asset Theo Alpha ni su SHA actual.

## Respaldo Git original completado ✅

El archivo [ALASTHEO-2026-10-12.bundle](../git-backups/ALASTHEO-2026-10-12.bundle) se generó mediante GitHub Actions, se comprobó con `git bundle verify`, se clonó para probar su restauración y se verificaron los encabezados de las ramas. La [lista de refs](../git-backups/ALASTHEO-refs.txt) conserva todas las ramas históricas, incluidos los refs de PR que ofreció el servidor. La [suma SHA-256](../git-backups/ALASTHEO-2026-10-12.bundle.sha256) acompaña al respaldo.

**El bundle ya está almacenado en el repositorio superviviente `alth-meta`**, además de haber sido generado como artifact de una ejecución de Actions. Un artifact por sí solo puede caducar; el archivo versionado en `main` es la copia persistente.

### Checklist de eliminación

- [x] Contenido actual del árbol principal y modelos Alpha documentales consolidados.
- [x] Variantes documentales exclusivas preservadas y verificadas por SHA.
- [x] Índice de 18 commits y 2 Issues + 2 PR con sus descripciones preservado.
- [x] Bundle Git **auténtico** completo de los refs accesibles, verificado y restaurado.
- [x] Enlaces del dashboard del perfil redirigidos a la documentación conservada en ALTH-META.
- [x] Wiki revisada visualmente por el propietario (captura del 2026-10-12): pantalla de bienvenida predeterminada sin páginas; no hay contenido Wiki identificado que falte respaldar.
- [ ] Aceptar que URLs antiguas de Issues y PR, estrellas y ajustes del repositorio no se preservan íntegramente en el bundle.

**Dictamen:** los contenidos Git, las ramas y el historial recuperable están respaldados. La Wiki ya fue revisada y el repositorio archivado `ALASTHEO` es técnicamente prescindible para recuperar el contenido Git. Resta únicamente la decisión del propietario de aceptar la pérdida de URLs/metadatos de GitHub antes de borrarlo. No se ha efectuado el borrado administrativo.

Consulta oficial: https://git-scm.com/docs/git-bundle
