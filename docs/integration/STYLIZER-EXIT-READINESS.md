# Stylizer · verificación de consolidación y respaldo privado

**Fecha de corte:** 2026-10-12  
**Destino vivo:** `Klymapo/alth-meta/tools/stylizer/`  
**Origen independiente:** `Klymapo/stylizer` (privado; aún no eliminado)  
**Estado:** prototipo experimental, no modelo final ni pipeline aprobado.

## Lo que se consolidó

- El código reutilizable, las pruebas, configuración publicable, el puente `alth_bridge.py` y la investigación STYLIZED seleccionada están dentro de `tools/stylizer/` (PR #25).
- Un cubo GLB generado sin dependencias de pago y el cuaderno de experimentos sirven para reanudar pruebas (PR #27).
- Los modelos originales `model.glb` y `sample.glb`, `output_agnes.png`, la configuración de hosting de pago, las credenciales y el historial sin filtrar **no** se publicaron en ALTH-META.
- El puente solo registra candidatos `UNREVIEWED`: no modifica archivos GLB, no aprueba modelos ni promueve assets al juego.
- Las ejecuciones de CI **Stylizer · Python y contrato ALTH** y **Auditoría · integración ALTH / AlasTheo** posteriores al PR #27 terminaron correctamente el 12 de octubre.

## Respaldo privado original: completado y restaurado

El workflow `Klymapo/stylizer/.github/workflows/export-stylizer-history.yml` creó un **Git bundle --all** con el historial del repositorio privado y produjo el artifact `stylizer-full-private-history-2026-10-12` en la ejecución 38302547690. La ejecución finalizó correctamente.

Verificación adicional realizada fuera del workflow sobre el ZIP descargado:

| Control | Resultado |
| --- | --- |
| Archivo ZIP | `stylizer-historial-completo-2026-10-12.zip` |
| Tamaño ZIP | 20,439,564 bytes |
| Bundle interior | `stylizer-2026-10-12.bundle` (20,447,702 bytes) |
| SHA-256 del bundle | `d59b114c3ae32e400360d09757d2f2f947b11b7ab95e75b2bfcba6613f1bc9a6` |
| Comparación SHA-256 con archivo del ZIP | **PASS** |
| Clonación con `git clone --mirror` desde bundle | **PASS** |
| `git fsck --full` de repositorio restaurado | **PASS** |
| Referencias comparadas con `heads.txt` | **25/25 coincidentes** |
| Ramas `refs/heads/*` de ese conjunto | **12/12** |

**Copia permanente adicional:** ZIP íntegro almacenado como archivo no compartido en la cuenta creativa de Google Drive, dentro de `ALTH-META · Bitácora de modelado procedural GLB / Respaldos GitHub · ALTH-META/`. Comprobada la existencia y tamaño (20,439,564 bytes) mediante metadatos de Drive. Se omite el enlace del almacenamiento privado en este repositorio público deliberadamente.

**Advertencia:** el artifact temporal de GitHub Actions vence según la retención de GitHub; la copia privada de Drive es la que evita depender de la existencia del repositorio Stylizer original. El ZIP del bundle puede contener binarios y documentación históricos de procedencia/licencia no auditadas. No hacerlo público automáticamente.

## Preparación para retirar el repositorio independiente

- [x] Código y experimentos aprovechables integrados sin alteración de los assets aprobados.
- [x] Ejemplo abierto reproducible y pruebas de integración.
- [x] Historial Git original `--all` y binarios históricos conservados en un bundle privado.
- [x] Clonación, integridad y referencias verificadas.
- [x] Copia fuera del repositorio original en Google Drive privado verificada.
- [ ] Revisar enlaces y referencias activas que aún apunten al repo original; actualizarlas si deben seguir funcionando tras el borrado.
- [ ] Aceptar que Issues/PR antiguos, URLs GitHub y configuración administrativa de ese repo no se restituyen automáticamente a partir del bundle.
- [ ] Ejecutar un borrado administrativo **solo bajo decisión expresa**, sin automatizarlo en CI.

**Dictamen:** el contenido Git del repositorio Stylizer está respaldado y es restaurable; su parte reutilizable ya vive en ALTH-META. No hay necesidad técnica de mantener otro repositorio para el desarrollo normal del prototipo. No se ha borrado ni desarchivado nada. 
