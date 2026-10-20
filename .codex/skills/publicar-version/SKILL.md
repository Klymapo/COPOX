---
name: publicar-version
description: Publica una versión de un GLB de ALTH-META/COPOX en un paso (copox-modelos + SHA256SUMS + ULTIMA.txt + capturas + ficha + push + registro en Drive). Úsala cada vez que un modelo nuevo se entregue a Admin.
---

# Publicar versión (COPOX)

Antes eran ~8 pasos a mano por versión (≈44 versiones; ULTIMA.txt se corrigió 2 veces). Ahora:

1. `python -m copox.entorno` → debe dar `godot`, `xvfb_run` y `base_sha_ok: true`. Si falla, arréglalo antes.
2. Corre CHXP V3 completo (con GIF) sobre el GLB: `python -m copox.render.chxp3 GLB --tipo … --salida DIR …`.
   Para iterar usa `--rapido` (512 px, sin GIF, ~35 s); para entregar, completo.
3. Publica:
   ```
   python -m copox.publicar GLB --carpeta <adan|theo|personaje> --nombre <NOMBRE_VNN> \
       --nota "qué cambió" --pedido "lo que pidió Admin" --chxp DIR --push
   ```
   - Nunca sobrescribe: un archivo existente con otro SHA → error. Versión nueva = nombre nuevo.
   - La base congelada no se toca.
   - Estado por defecto **SIN APROBAR**. Sólo Admin aprueba; cuando lo haga, publica otra línea con
     `--estado "APROBADA (de momento)"` usando el mismo GLB (no cambia el archivo, sólo ULTIMA.txt y la ficha).
4. Copia el campo `drive_linea` de la salida al «Registro de cambios» de la Memoria maestra de Drive
   (`1SYG_u3faWWcYKXSAzUePnOwQAApLmrAVpDwXtWE_K28`) con `mcp__Google_Docs__update_doc` (`replaceAllText` anclado en
   la última línea del registro: insértala después).
5. Manda a Admin la HOJA, un acercamiento de la zona tocada, los GIF y el GLB (SendUserFile). Pide aprobación.

Prueba sin escribir nada: `--simular`.

## Revisión visual ANTES de mandar a Admin (obligatoria)
CHXP V3 deja `<nombre>_COMPARATIVA.png` (referencia vs render por región: cabeza, hombros y torso, cadera y piernas,
pies; frente y espalda). Lanza el agente `revisor-visual-alth` (solo lectura) con la COMPARATIVA, la HOJA y
`<nombre>_AUDITORIA.json`. Si devuelve UNA_CORRECCIÓN o REHACER, corrige (dentro del tope de 3 iteraciones) antes de
mandar; si mandas igual, dile a Admin exactamente qué bloqueos quedaron. Revisa tú también los acercamientos.
