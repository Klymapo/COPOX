# tools/maniqui

Cadena Beta + Gamma → Alastor Delta → maniquí de la biblioteca. Python 3 + numpy + Pillow, sin Blender ni GPU.

```bash
bash tools/maniqui/run_pipeline.sh            # salida en build/maniqui/
```

Los scripts se importan entre sí por ruta relativa (`render.py`, `cuerpo.py`), así que se ejecutan **desde esta carpeta** (el `.sh` ya hace `cd`).

| Script | Entrada → salida | Parámetros clave |
|---|---|---|
| `wrap2.py beta gamma out [maxd_cm] [smooth] [corte]` | shrinkwrap por zonas + cabeza de Gamma | 9 cm, 5 pasadas, corte 0.55 |
| `wrap3.py it4c beta gamma out` | trasplante de faldones/pantalón/zapatos con copia de pesos | banda hasta 3.5 cm sobre el cinturón |
| `neck.py in out [y_cuello]` | cuello nuevo bajo la mandíbula | y = 0.47 |
| `maniqui.py delta_v1_1 it4c maniqui_out ropa_out beta` | quita pelo y lentes, cráneo de bola, archivo de ropa | ver comentarios |
| `huesos.py in out Hueso=factor…` | escala largos de huesos (Left/Right) y recalcula inverseBindMatrices; animaciones intactas | `UpperArm=0.85 LowerArm=0.85` |
| `cuerpo.py in out` | torso, pelvis, brazos superiores y piernas sobre el esqueleto, secciones superelipse (`P_BOX`) | perfiles en el código |
| `manos_pies.py in out` | antebrazo, palma, dedos y pies | radios en el código |
| `medir_cara.py ref.jpg out.json [--recorte x0,y0,x1,y1] [--vista lado] [--debug png]` | mide la referencia (numpy/scipy/Pillow): caja de la cara, llenado, mandíbula, ojos, cejas, nariz, boca, orejas, proporción con la altura | ver `rasgos/*.json` |
| `medir_gamma.py gamma.glb out.json [--debug png]` | mide la cara de Gamma en 3D (render sin luz + profundidad): cara, ojos, iris, cejas, nariz (perfil), boca, orejas | `rasgos/gamma.json` |
| `cabeza.py in out [rasgos.json]` | cabeza canónica ALTH: superelipsoide (cajón redondeado) con las proporciones del JSON, cuencas, nariz de bloque, boca, orejas de bloque + cuello recto; reemplaza Cabeza/Craneo/Cuello | `rasgos/alastor.json`, `rasgos/theo.json` |
| `headzoom.py in out [y_min]` / `facezoom.py in out` | acercamientos de cabeza (4 vistas) y cara (0/25/60°) | — |
| `render.py in.glb out.png [zup]` | 4 vistas, sombreado plano | — |
| `measure.py cand gamma beta prefijo` | IoU de silueta en 4 vistas + mapa de diferencias | — |
| `pose.py in.glb clip t out.png` | posa un clip (skinning en numpy) | clips: Wave, Sit-pose, Nod… |
| `retex.py in out tamaño` | reescala texturas embebidas | — |

Cada pieza nueva va etiquetada en `primitive.extras.pieza` (Cabeza, Craneo, Torso, PiernaL, DedoIndexL…).

## Continuación v0.3 del PR #34

`reconstruir_v03.py` genera hasta tres candidatos hermanos desde el SHA registrado de v0.3, sin sobrescribir destinos. `evaluar_v03.py` captura cuatro vistas, detalles y poses, y muestrea los 29 clips. `auditar_v03.py` verifica bytes de rig/animación y triángulos protegidos. Dependencias: numpy, scipy, pillow. Véanse comandos y límites en `docs/MANIQUI_V03_CONTINUACION_2026-10-14.md`. Resultado de esta campaña: PLATEAU, sin versión aprobada.
