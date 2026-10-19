# COPOX · Renderizador para IA (Elio = Claude, Argos = ChatGPT)

## CHXP V2 — lo primero que usas (19 oct 2026)

**Qué es:** el render de revisión con **Godot real** (lo mismo que verá el juego), por lotes: un solo proceso hace todas
las vistas y GIF de un asset. Escena estándar: luz ALTH (clave cálida con sombra, relleno frío, contraluz), piso con
rejilla en unidades ALTH (cuadro fino 0.05 u, línea fuerte 0.25 u), silueta de Adán a escala al lado, sombra de
contacto (AO) y referencia lado a lado.

**Necesitas:** Godot 4.7 (`GODOT_BIN`), `xvfb-run`, Python 3.10+ con numpy, scipy y Pillow. Sin GPU. Sin internet.

```bash
python -m copox.render.chxp2 MODELO.glb --salida SALIDA/ \
    --silueta ADAN_V49.glb \                      # silueta a escala (opcional)
    --ref refs/personajes/adan/adan-cuerpo-4-vistas.jpg --ref-2x2 \   # hoja 2x2: frente, perfil / espalda, 3/4
    --vistas personaje|objeto|edificio \           # edificio agrega vista cenital
    --visible CAPA_SHORT=0,PIES_TENIS=1 \          # piezas intercambiables por nombre de nodo
    --gif Idle-loop,Walk-loop,Run-loop
```

**Te entrega** (todo en `SALIDA/`):
- `NOMBRE_HOJA.png` — hoja vertical: referencia | render por vista, con SHA, altura, triángulos y tira de paleta.
- `NOMBRE_<vista>.png` y `NOMBRE_<vista>_mascara.png` (vista previa de la máscara por pieza).
- `NOMBRE_<clip>.gif` — 16 cuadros por clip, vista 3/4.
- `NOMBRE_REPORTE.json` — `alto_u`, `caja_u`, `triangulos_visibles`, piezas visibles/ocultas, `cobertura_px` por vista
  y pieza, `colores_fuera_de_paleta` (ΔE contra `spec/alth_spec.json`), tiempos.
- `_crudo/` — pasadas de Godot (color, normal, profundidad, máscara) y `ids` por vista en `.npy` para medir IoU.

**Cómo leerlo:** primero el REPORTE (números), luego la HOJA (imagen). Si una pieza que pediste oculta aparece en
`cobertura_px`, o falta una visible, la visibilidad está mal. Un color con ΔE > 6 se propone antes de usarlo.
**Tiempo:** ~15 s para 4 vistas; ~2–3 min con 3 GIF (calidad primero, 1024 px).

**Límites conocidos:** sin GPU, Godot usa el renderer Compatibility (sin SSAO propio); la sombra de contacto la calcula
Python desde la profundidad. Las pasadas sin luz salen con una curva ~v^1.15 (corregida al decodificar).

**Fabricar más rápido (19 oct 2026):** las mallas implícitas (pelo, ropa, pelvis, tenis) ahora se calculan en dos
niveles (`copox/medicion/malla_rapida.py`): rejilla gruesa y solo la banda cerca de la superficie en fino.
- `ALTH_CALIDAD=borrador` → rejilla 2× más gruesa y sin simplificar: para iterar forma (V49 completa ~1 min).
- Sin variable → calidad final (V49 completa ~3.5 min; antes ~12 min; pelo por mechones 60 s, antes 9.5 min).
- `ALTH_MALLA=exacta` → evalúa todo como antes (para reproducir bit a bit un GLB publicado con receta vieja).

El CHXP de abajo (numpy) queda para diagnóstico de curvatura, normales y clases; para revisar cómo se ve, usa V2.

---

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
