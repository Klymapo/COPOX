# ALASTHEO · Auditoría para posible eliminación

Fecha: 2026-10-12. Esta auditoría no elimina el repositorio archivado.

## Contenido rescatado y comprobado

- La rama `main` de ALASTHEO tiene **19 blobs**. En `alth-meta` se verificó previamente que los 19 tienen rutas equivalentes: 9 idénticos en su ruta y 10 adaptados; la procedencia está en [alastheo-import.json](../alastheo-import.json).
- El libro de producción `.xlsx` importado coincide por SHA.
- La rama `assets/alpha-theo-alastor` incluye **dos archivos exclusivos**: `models/alpha/README.md` y `models/alpha/manifest.json`, preservados sin cambios en [legacy-alpha-branch/](../legacy-alpha-branch/).
- Entre las restantes variantes de rama se conservan aquí tres blobs documentales históricos: `structure-README.snapshot.txt`, `structure-assets-README.snapshot.txt`, `visual-methods-README.snapshot.txt`. Su SHA Git coincide exactamente con los originales.
- **Cuatro ramas:** `main`, `assets/alpha-theo-alastor`, `chore/repository-structure`, `docs/visual-references-and-methods`.
- **18 commits únicos accesibles** en esas ramas y metadatos de **2 Issues cerrados, 2 PR fusionados**, ambos sin comentarios, preservados en [HISTORY_INDEX.json](HISTORY_INDEX.json).
- Según la API al auditar: **sin releases, sin Pages y sin forks**; `has_wiki=true` pero el contenido de un posible Wiki no ha sido auditado y podría constituir información adicional.
- Todo el material documental incorporado es histórico; **no sustituye** el asset Theo Alpha ni su SHA actual.

## Límite de la copia

El índice preserva textos de tickets, mensajes/identificadores/relaciones de commits y snapshots de versiones importantes. **No es un espejo Git**: al eliminar ALASTHEO se perderían los objetos originales de commits y árboles, además de metadatos históricos accesibles desde las URLs del repositorio. No se han exportado posibles contenidos del Wiki.

### Puerta para borrado definitivo

- [x] Contenido del árbol principal incorporado/adaptado.
- [x] Archivos exclusivos de ramas y versiones documentales divergentes conservados.
- [x] Metadatos de ramas, commits, Issues y PRs conservados.
- [x] Sin releases, Pages ni forks registrados.
- [ ] Crear y verificar **bundle Git completo** de `ALASTHEO` con todos los refs de ramas/tags; guardarlo **fuera del repositorio que se borrará**.
- [ ] Comprobar el posible GitHub Wiki y exportarlo si contiene páginas.
- [ ] Confirmar el destino de enlaces externos a ALASTHEO y aceptar que URLs de commits/Issues/PR dejarán de funcionar.

**Dictamen:** documentación y contenido de trabajo rescatados. Borrado irreversible **pendiente de respaldo Git completo y revisión de Wiki**. No declarar la eliminación libre de riesgo antes de estas verificaciones.

## Respaldo restaurable sin instalar Git en tu laptop

Usando una terminal de GitHub Codespaces con sesión autorizada para leer este repositorio, ejecuta:

```bash
gh repo clone Klymapo/ALASTHEO ALASTHEO.git -- --mirror
git -C ALASTHEO.git bundle create ../ALASTHEO-2026-10-12.bundle --all
git -C ALASTHEO.git bundle verify ../ALASTHEO-2026-10-12.bundle
git -C ALASTHEO.git bundle list-heads ../ALASTHEO-2026-10-12.bundle
```

Descarga el archivo `.bundle` a un lugar seguro fuera del Codespace y prueba su restauración con `git clone ALASTHEO-2026-10-12.bundle ALASTHEO-restore-test`. Un bundle conserva los objetos Git alcanzables por refs, no Issues/PRs ni un posible Wiki; esos datos están tratados por separado. La posibilidad de iniciar Codespaces y de clonar desde él depende del acceso del usuario al repositorio.

Referencia: https://git-scm.com/docs/git-bundle
