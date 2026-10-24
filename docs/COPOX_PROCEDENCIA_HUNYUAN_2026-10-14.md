# COPOX: procedencia de activos y reconstrucción independiente
Fecha: 2026-10-14. Nota técnica, no asesoría legal.

## Linaje confirmado en el repositorio
- Beta: `models/source/alastor/alastor_beta_juego.glb` aporta rig y 29 clips; falta verificar titularidad de cada componente.
- Gamma: `models/source/alastor/alastor_gamma_30k_2k.glb` fue generado con Hunyuan3D, según `docs/MANIQUI_HIBRIDO_2026-10-14.md`.
- Los scripts `tools/maniqui/wrap2.py`, `wrap3.py` y `maniqui.py` incorporaron la geometría Gamma a Delta y Maniquí. El rostro de r3 conserva esa procedencia.
- Los scripts geométricos propios pueden ejecutarse sin Hunyuan. Ello no cambia automáticamente el origen de modelos anteriores.

## Licencias: puntos a verificar
**No está confirmada la versión exacta de Hunyuan y el contrato del servicio usado para Gamma.** La licencia 2.1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/hy3dshape/LICENSE distingue los Outputs de las modificaciones del modelo IA (1g-1h), declara que Tencent no reclama derechos sobre los Outputs (6d), pero contiene restricciones de uso territorial (5c), condiciones y avisos en ciertas distribuciones (3), prohibición de usar outputs para mejorar otros modelos IA (5b), y condiciones comerciales para grandes usuarios (4). La licencia 2.0 y términos del servicio o API pueden diferir. Verificar contrato concreto y fecha antes de distribuir.

En México el artículo 78 de la Ley Federal del Derecho de Autor regula obras derivadas protegidas: https://www.diputados.gob.mx/LeyesBiblio/pdf/LFDA.pdf . Su aplicación a outputs generativos requiere valoración profesional; no afirmar que Tencent posea automáticamente copyright sobre los outputs ni que su modificación elimine obligaciones contractuales.

## Plan separado
**Carril histórico, origen mixto:** conservar fuentes y GLBs con hashes para experimentos y trazabilidad. Revisar si la distribución pública exige avisos o precauciones según los términos realmente aplicables. No reemplazar ni borrar históricos.

**Carril nuevo, con fuentes verificadas:**
1. Partir de diseños/referencias propios de Admin o materiales CC0 correctamente documentados; no utilizar geometría o texturas de Gamma/r3 como base técnica de una supuesta creación independiente.
2. Generar cabeza, facciones, cabello, cuerpo y ropa íntegramente desde medidas de esas referencias con funciones matemáticas originales.
3. Reutilizar Beta para rig/animaciones únicamente si su procedencia y permisos están documentados; de lo contrario elaborar rig y clips propios.
4. Guardar manifiestos de procedencia por pieza, fuentes, hashes y versión de scripts; construir desde cero reproduciblemente en GitHub Actions.
5. Exigir aprobación legal de procedencia y auditoría artística por separado antes de distribución definitiva.

Clasificaciones: VERIFICADO_PROPIO, TERCERO_CONDICIONES, ORIGEN_MIXTO, SIN_VERIFICAR. El porcentaje de polígonos nuevos no demuestra titularidad ni independencia.

## Registro de cambios
- 2026-10-14: auditoría documental de cadena Beta/Gamma -> Delta -> Maniquí/r3/v0.4 y plan de nueva generación sin dependencia de Gamma. Sin cambios a modelos ni promoción automática.
