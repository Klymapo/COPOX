# Entregables G2-C4 · 14 de octubre de 2026

Todos los ensayos son experimentales. B2 conserva la limpieza regional
confirmada; A/A2 y C están rechazados. No existe ABC ni aprobación global.

- [GLB maestros: V3 intacta y A, A2, B, B2, C](https://drive.google.com/file/d/1fuBX1l3qRNI8AAWupchJhiHqvzXRq6P-/view).
  27.550.784 bytes. SHA256 `d8fc40ad1abeaf85f35c201fbaf2f8a6c51365087d3ec4b27590e212683e7556`.
- [Copias para importar en Godot4.7.2, con limitaciones faciales](https://drive.google.com/file/d/1_EcGNvYcMgz0DFgJh0mJqJOSAbjftHs7/view).
  27.532.955 bytes. SHA256 `a3e348f09697668db45dc0571505d22fae1cd696a7cbca14679398ea3cfaa108`.
- [Capturas reales, láminas, galería HTML, código e informes](https://drive.google.com/file/d/1Z9KjQSnC_zA87aUQHSjSHakCFmcHVAM8/view).
  50.043.281 bytes. SHA256 `4a1f2c9fcbc2c6b9d6737ca863faa75a55738ccdadc568f5d67b4d120b0e9321`.
  Extraer el ZIP y abrir `index.html`. Los originales de cada captura están
  en `godot/captures_v3`; `laminas_finales` contiene las comparativas.
  Las carpetas previas se conservan como diagnóstico histórico.

Las copias compatibles se distinguen de los maestros: su saneamiento
omite referencias faciales vacías para importar, pero no restaura las
expresiones ni logra conformidad glTF completa. Ver
[registro técnico](REGISTRO_CAMBIOS.md), [resultados](RESUMEN.json) y
[reproducción](REPRODUCIR.md).

## GLB B2 conservado para revisión

`modelos/maniqui_G2C4_B2_SIN_APROBAR.glb`

SHA256 `daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec`.
Retira 71 triángulos identificados de montura; cero vértices movidos.
No sustituye V3. Los huecos faciales y las expresiones no funcionales
siguen siendo limitaciones heredadas.
