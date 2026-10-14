# Maniquí v0.4 — cierre de la ronda de nuca y patillas (2026-10-14)

**Estado: PLATEAU ARTÍSTICO · ninguna variante aprobada · PR #36 en borrador.**

## Qué se ejecutó
- Baseline auténtico: `assets/maniqui/maniqui_v0_3_r3.glb` (SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`).
- Script `tools/maniqui/nuca_patillas_v04.py`: tres variantes hermanas i1/i2/i3, banda posterior de cúpula y zonas de patillas, con pruebas de recorte conservador condicionado a protección de rasgos.
- Runner gratuito GitHub Actions `38595892866`, **success**. Sin actualizaciones de `main`, sin sustitución de GLB históricos.
- Evidencia real: `assets/maniqui/experimental/v04/previews/i{1,2,3}/`. Por variante, hoja de cuatro vistas y cuatro acercamientos, poses Wave/Sit-pose/HeadShake/Nod y 87 muestras de animación. Auditar `docs/maniqui/v04/auditoria_v04.json` y resumen `RESUMEN_V04.json`.

## Resultados
| Variante | Máximo desplazamiento del cráneo | Recortes seguros de Cara | IoU mínimo vs r3 | Veredicto |
|---|---:|---:|---:|---|
| i1 | 10.05 mm | 0 | 99.980% | Rechazada, cambio casi imperceptible |
| i2 | 18.25 mm | 0 | 99.964% | Rechazada, sin reparación real |
| i3 | 18.25 mm | 0 | 99.964% | Rechazada, sin reparación real |

Para i1/i2/i3: 56 huesos, 29 clips, 1357 triángulos de facciones y 481 de orejas protegidos, 0 pérdidas, 0 triángulos degenerados y 0 aristas no manifold nuevas en la cúpula. **Pero** 128 aristas del borde craneal siguen abiertas y la unión cara/cráneo sigue siendo solape, no una soldadura topológica.

## Inspección visual
Comparadas `base_detalle.png` y `candidato_detalle.png` de i3 en frente, 3/4, perfil y espalda. Se aprecia sólo un descenso mínimo del borde posterior; persisten las placas en nuca, las puntas de las patillas y la fragmentación facial, igual que en r3. El IoU de 99.9% indica que no deformamos la silueta, pero **no demuestra mejora artística**.

La máscara de seguridad no encontró ningún triángulo de Cara que pudiera recortarse preservando todos los rasgos con el criterio actual. Por eso **0 recortes**, y las tres variantes se parecen visualmente a la base. No se debe aflojar ciegamente la máscara: arriesgaría orejas, mandíbula o párpados.

## Cambio de método propuesto
1. Extraer el contorno de borde real de Cara por geometría (deduplicar separaciones UV sin destruir islas).
2. Separar manualmente regiones anatómicas: frente, cejas, ojos, orejas, patillas, nuca, mandíbula y cuello; detectar placas de Gamma por conectividad y orientación, **no sólo por `xyz` ni proximidad**.
3. Construir un contorno de correspondencia entre cara y cúpula; *retopología local y soldadura real* con índices compartidos cuando proceda, o bordes compatibles sin romper el skinning.
4. Cambiar la métrica: comparación focalizada de cráneo + rostro, continuidad de normales, aristas abiertas, autointersecciones; IoU global como guardarraíl, no como puntuación principal.
5. Hacer auditoría rápida de los tres candidatos antes de las 87 poses profundas. Ejecutar la batería completa sólo sobre un finalista que supere la inspección visual.
6. Prueba final en Godot antes de aprobar para la biblioteca.

Esto requiere una nueva estrategia o una auditoría puntual en Work, no una cuarta variante basada en los mismos desplazamientos. Mantener `i1/i2/i3` como evidencia descartada y **no fusionar #36** sin aprobación.

## Registro de cambios
- 2026-10-14: creada rama `experimentos/maniqui-v04-nuca-patillas`, PR borrador #36, script y workflow.
- 2026-10-14: generados tres GLB y capturas/poses originales; ejecución 38595892866 concluida con éxito.
- 2026-10-14: auditados rig, facciones, orejas, cifras de IoU y topología. Resultado: PLATEAU sin promoción. Se requiere nueva estrategia.
