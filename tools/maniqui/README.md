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
| `cuerpo.py in out` | torso, brazos superiores y piernas sobre el esqueleto | perfiles en el código |
| `manos_pies.py in out` | antebrazo, palma, dedos y pies | radios en el código |
| `render.py in.glb out.png [zup]` | 4 vistas, sombreado plano | — |
| `measure.py cand gamma beta prefijo` | IoU de silueta en 4 vistas + mapa de diferencias | — |
| `pose.py in.glb clip t out.png` | posa un clip (skinning en numpy) | clips: Wave, Sit-pose, Nod… |
| `retex.py in out tamaño` | reescala texturas embebidas | — |

Cada pieza nueva va etiquetada en `primitive.extras.pieza` (Cabeza, Craneo, Torso, PiernaL, DedoIndexL…).
