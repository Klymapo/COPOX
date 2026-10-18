# COPOX G2-C5 · Entrega integral y trazabilidad

**Actualizado:** 14 oct 2026 · **Estado:** EXPERIMENTAL / SIN APROBACIÓN · **PR:** [#48](https://github.com/Klymapo/COPOX/pull/48) · **Base:** [G2-C4 #47](https://github.com/Klymapo/COPOX/pull/47).

Se conserva el trabajo nuevo de Codex como punto de partida (A + B2 + C), con una reparación parcial de piel detrás de la oreja derecha. **No reemplaza V3 ni se fusionó**, ni alcanza aprobación artística. Se mantuvieron dos variantes hermanas.

## Archivos accesibles en Drive
**[Carpeta G2-C5 completa](https://drive.google.com/drive/folders/1YTraae668CcWm2UspltPUvMRa8E4RCTB)** dentro de Gaston → APPS → COPOX.

| Entregable | Descarga | SHA256 |
|---|---|---|
| GLB conservador, referencia regional provisional | [GLB](https://drive.google.com/file/d/1SOqMVaRCxMckgMw5lyUo6-gVZ-m3Ks0p/view) | `34ccc30b0f5565204c2b16395daff8d6303da869dbf432ef51b8db6080e8e070` |
| GLB con relleno óptico NO APROBADO | [GLB](https://drive.google.com/file/d/1hmWrMCvS_87aZIcdSo1lR0bBUEnV58Jj/view) | `908aef0e812c4997e6e241691fdfebbb7e4caeb844e310da88a962414a278342` |
| Paquete integral (ambos GLB, 5 scripts, reportes y capturas) | [ZIP](https://drive.google.com/file/d/1U7DHoUNE4w-t6jJHMR6Yc_74Uu1YNq39/view) | `fd8ab683dee93f10ac7b12ad1ee97c2a255463fc5450e3815e5ce8ab780cc8b7` |
| Código, reportes, hashes en ZIP pequeño | [ZIP](https://drive.google.com/file/d/1CzOnJGoPDsgGLLGyJpy0W8oDxLy0xdFY/view) | `7d943484d2cd954057ae7ac9c8e2f414949fde3ebec10e6870d5b5aa4e318cff` |
| Comparación 6 vistas | [PNG](https://drive.google.com/file/d/1UpBo-WkR-DKC639G_2nc16HN3S215-H3/view) | `6f71a84ec731e9c0b0f0df11acc9b958d189e5814ca3efc6789d5e70ec8f7542` |
| Acercamiento ojos | [PNG](https://drive.google.com/file/d/1nxNerH4TWLDZ15P6FXS0tQtotHZ26QDv/view) | `def406c2dd93fceeb21730e693fa533d7308c7fec7a627c438491a2f56302c4e` |
| Lámina final 4 vistas | [PNG](https://drive.google.com/file/d/1WYZe4MEFW7aBaEHWellGr-zv_dcNXTsb/view) | `e02f0a783430ca438b8499165b51c8e20e19e36ba97431ff3503d5aee9279f38` |

## Contenido versionado en este PR
- **Código original del laboratorio:** `tools/maniqui/g2c5_lab/{build_g2c5,build_safe,glbutils,inspect_geometry,preview}.py`
- **Reportes y hashes:** `docs/maniqui/g2c5/COPOX_G2C5_{EVALUACION.md,REPORTE.json,CONSERVADOR_REPORTE.json}` y `MANIFIESTO_SHA256.json`
- **Imágenes reales:** `docs/maniqui/g2c5/imagenes/` (seis vistas, cuatro vistas, culling, ojos y lámina).
- **Fuentes empaquetadas:** `docs/maniqui/g2c5/G2C5_CODIGO_REPORTES_SHA256.zip`.
- **Bitácora:** `REGISTRO_CAMBIOS.md` y memoria maestra en [Gaston](https://docs.google.com/document/d/1SYG_u3faWWcYKXSAzUePnOwQAApLmrAVpDwXtWE_K28/edit).

Los **GLB binarios grandes** residen completos y persistentemente en Drive, con hashes para verificar integridad. No están añadidos a los objetos Git de la rama: esto evita inflar el historial con múltiples candidatos **aún no aprobados**. Las fuentes y evidencia sí son navegables en GitHub.

## Qué se hizo exactamente
**Conservador:** combina 71 triángulos de montura B2 eliminados, mandíbula C (rechazada anatómicamente y retenida únicamente por petición de conservar lo nuevo), y reconstrucción localizada de 120 de 156 triángulos tras oreja derecha. Mantiene 36 caras de residuos rapadas; suaviza 84 vértices internos y protege 19 de borde. No se detectaron inversiones entre las 120 caras restituidas. **Sigue visible un hueco lateral.**

**Experimental óptico:** agrega 2,196 caras de fondo facial y 240 submandibulares, **no soldadas al borde original**. Produce bordes visuales no aceptables alrededor de ojos. **RECHAZADO como modelo final**, únicamente testigo de experimento.

**QA comprobado:** lectura de GLB en `trimesh` con 34 geometrías, 56 huesos y 29 clips nominales, primitivas ajenas a Cabeza sin cambios. Renders reales del rasterizador con culling de caras posteriores en 6 vistas. **No se ejecutó Godot en G2-C5**, no se validó deformación facial ni glTF completo; no afirmar cuello riggeado ni soldadura manifold.

## Reproducción / precauciones
El ZIP pequeño conserva los scripts sin cambios, incluidos sus paths originales de laboratorio `/mnt/data`. **No son portables tal como están**, se debe parametrizar la entrada/salida para Codespaces y descargar primero los modelos V3/A/B2/C del [paquete maestro G2-C4](https://drive.google.com/file/d/1fuBX1l3qRNI8AAWupchJhiHqvzXRq6P-/view). Aplicar de nuevo máscaras de protección, exportación, validación en Godot y revisión visual antes de usar cualquier resultado. Ver `MANIFIESTO_SHA256.json` para hashes y tamaños de salida.

## REGISTRO DE CAMBIOS
14-oct-2026 — Tras autorización de conservar los cambios nuevos, se hicieron dos candidatos y se rechazó el relleno óptico como acabado. Se creó un respaldo específico G2-C5 en Drive, se subieron por separado los GLB/capturas y se versionó **el código real + JSON + comparativas** en GitHub PR #48. SHA verificados localmente. Sin merge ni sustitución de modelos, B2 y V3 preservados.
