# COPOX · Renderizador para IA (Elio = Claude, Argos = ChatGPT)

Render de modelos GLB del proyecto ALTH-META para comparar contra referencias y medir con el motor (`copox/medicion`). Solo usa **Python 3.10+, NumPy y Pillow**: sin internet, sin GPU, sin Blender.

## Qué necesitas

- La carpeta `copox/` completa (usa `copox/render` y `copox/medicion`).
- El GLB del modelo. **Los GLB no están en el repo**: Admin te los sube.
- Si no puedes clonar el repo, pide a Admin el zip de `copox/` o descárgalo desde GitHub (Code → Download ZIP) y súbelo.

## Uso desde Python (recomendado: el modelo queda cargado)

```python
import sys; sys.path.insert(0, "RUTA/AL/REPO")
from copox.render import Sesion
s = Sesion("THEO_V03_ROSTRO.glb")
r = s.render("cara_34;modo=arcilla", autor="argos")
r.guardar("capturas/2026-10-18/THEO_V03_ROSTRO/argos/cara_34_arcilla_512.png")
r.clases      # mapa de clases ALTH (0 fondo, 1 pelo, 2 piel, 3 claro, 4 oscuro, 5 azul)
```

Láminas:
```python
from copox.render.lamina import lamina_ref, lamina_ab
img, info = lamina_ref(s, "frente", "hoja.png", recorte=(0, 40, 334, 705), autor="argos")
img, info = lamina_ab(Sesion("A.glb"), Sesion("B.glb"), "cara_34;modo=arcilla", autor="argos")
```

## Uso desde terminal

```
python -m copox.render vistas
python -m copox.render vista  MODELO.glb "cara_34;modo=arcilla" --autor argos
python -m copox.render hoja   MODELO.glb --modo arcilla
python -m copox.render ref    MODELO.glb "frente" hoja.png --recorte 0,40,334,705
python -m copox.render ab     A.glb B.glb "cara_34;modo=arcilla"
python -m copox.render servidor        # opcional: deja modelos en memoria; luego agrega --servidor
```

## Códigos de vista (compartidos entre Elio y Argos)

Texto `clave=valor;…`. Puede empezar con una vista guardada:

| Vista | Qué es |
|---|---|
| `frente`, `tres_cuartos`, `perfil_izq`, `perfil_der`, `espalda`, `tres_cuartos_espalda` | Cuerpo completo, encuadre fijo |
| `cara_frente`, `cara_34`, `cara_perfil`, `cara_espalda` | Cabeza, encuadre fijo |
| `mano_izq`, `mano_der`, `pies` | Encuadre automático a la región |

Claves: `yaw elev roll` (grados) · `dist` (`orto` o distancia en unidades) · `region` · `enc` (`auto` o `alto,cx,cy`) · `clip` y `t` (0–1; `reposo` = sin animación) · `modo` · `tam` · `sombreado` (`suave`/`facetas`) · `ocultar` (nodos separados por coma, p. ej. `CAPA_GUIA_CAPILAR`) · `mostrar` (nodos que el GLB marca ocultos con `KHR_node_visibility` y que sí quieres ver, p. ej. `MANO_PUNO_L,MANO_PUNO_R`; sin esta clave, lo oculto en el archivo no se dibuja, igual que en Godot).

El sello de cada captura imprime el código completo: cópialo para repetir exactamente la toma.

## Modos

| Modo | Para qué |
|---|---|
| `color` | Color ALTH con luz de estudio de 3 puntos y oclusión ambiental |
| `arcilla` | Gris: forma, bultos y escalones |
| `malla` | Arcilla con aristas: topología |
| `normales` | Orientación de caras (rojo = derecha, verde = arriba, azul = hacia cámara) |
| `curvatura` | Rojo convexo, azul cóncavo |
| `quiebres` | Mapa de calor de cambios bruscos de forma (curvatura menos su promedio local): escalones, "U", piquitos. Escala fija (comparable entre versiones) |
| `clases` | Paleta ALTH por píxel (lo que mide el motor) |
| `clases_tri` | Clase por triángulo, idéntico al render anterior del motor |

Luz: `luz=estudio` (por defecto) o `luz=juego` = el sol del visor de Godot (rotación −40, −30, 0) con sombras proyectadas y normales del archivo. Úsala para ver lo que se verá en el juego: desniveles que la luz de estudio aplana (p. ej. la "U" bajo la boca de Adán V29). Medida SENKU equivalente: `copox/medicion/quiebres.py`.

Láminas: `ref` = referencia | modelo | superposición | diferencia (rojo = solo modelo, azul = solo referencia, amarillo = clase distinta) con IoU por clase. `ab` = lo mismo entre dos versiones con el mismo encuadre.

## Reglas del proyecto

- **Resolución:** 512 para iterar, 1024 para láminas finales.
- **Capturas:** `capturas/AAAA-MM-DD/<modelo>/<autor>/<vista>_<modo>_<tam>.png`, en la rama `capturas` del repo (no en `main`).
- **No subas GLB al repo** (es público).
- Cada quien sube lo suyo; Admin compara.
- Igual que Godot, se descartan las caras traseras (salvo materiales `doubleSided`).

## Límites conocidos

- Luz aproximada (Lambert + oclusión en pantalla): sirve para forma y color plano, no imita el render original al 100%.
- Sin sombras proyectadas ni transparencia parcial (solo alfa MASK).
- `curvatura` invierte el color en piezas con caras invertidas (ver reporte de Adán: brazos, piernas, manos y short).
