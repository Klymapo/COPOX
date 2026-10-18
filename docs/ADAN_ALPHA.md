# ADÁN ALPHA

17 oct 2026 · Elio (Claude) · nombre dado por Admin.

**Adán Alpha** es la base universal de personajes ALTH-META aprobada como hito: el cuerpo de Adán con el rostro y la cabeza en canon ALTH (sin rasgos de un personaje). Su derivado de identidad es **Theo Alpha**. El pelo con mechones queda para después (decisión de Admin: «el pelo al final»).

| Archivo | Equivale a | SHA-256 | Tamaño |
|---|---|---|---|
| `ADAN_ALPHA.glb` | Adán V21 | `bf6ec14004b6390fc485136436ab89673e765955aad5da918ecac87bbb44cfc1` | 8.6 MB |
| `THEO_ALPHA.glb` | Theo V14 | `6dcf8acdd6ee85f2a09ba063b76b0b1257975b580695632c44735c8f7c0a309e` | 8.6 MB |

Los GLB **no se suben a este repo** (es público). Tampoco al Drive automáticamente: el respaldo lo hace Admin. El maestro V04 (`a1936eb9…`) nunca se modificó.

## Qué tiene

- **Esqueleto:** 56 huesos y 112 clips (Godot importa `Idle-loop` como `Idle`).
- **18 gestos de cara:**
  - Boca: `boca_soplar`, `abrir`, `sonrisa`, `triste`, `o`, `tensa`, `lado_L` y `lado_R`.
  - Cejas: `ceja_arriba`, `ceno` y `triste`, L/R.
  - Ojos: `parpado` L/R y `alegre` L/R.
- **Proporciones** (desde V08): ojos→suela 4.60 ED, envergadura 6.65 ED, cabeza ≈2.5 cabezas sin pelo.
- **Cabeza y rostro:**
  - Ojos: placa con forma ancha, iris alto oscuro, un brillo y párpado grueso.
  - Cejas: bloques con grosor y gestos.
  - Nariz: cubo biselado rosado.
  - Orejas: bloques con ranura en C.
  - Boca: de malla, línea fina con sonrisa leve (no es calcomanía, por decisión de Admin).
  - Piel de la cabeza: superficie lisa ajustada.
  - Rubor por color de vértice.
- **Calidad:**
  - Caras orientadas hacia afuera y normales recalculadas.
  - Piel, boca y gorro de dos caras.
  - Huecos visibles en 90 tomas de cabeza: ≈110 px.
  - Pasa la prueba de carga en Godot 4.7.2.
- **Pendiente:**
  - Pelo con mechones (≤2,000 triángulos, móviles).
  - Pupilas con shader en Godot (decidido).
  - Ropa por capas.
  - `boca_o` y `boca_soplar` abren poco.

## Cómo se reconstruye

Todo es reproducible con las recetas de `docs/medicion/`. La parte V10 → Alpha se verificó y dio un archivo **bit a bit idéntico** (`construir_adan_alpha.sh`, ~30 s).

| Paso | Versión | Receta | Qué hace |
|---|---|---|---|
| 0 | V04 | — | Maestro (Alpha, Beta, Gamma, Delta, Epsilon → Adán) |
| 1 | V05 | `receta_adan_v05_limpieza.py` (+ `glb.py`) | Limpieza: 51.6 → 8.2 MB, sin cambios de forma |
| 2 | V06 | `receta_adan_v06_neutro.py` | Rostro neutro, capas, boca en línea |
| 3 | V07–V08 | `copox.medicion.proporciones` + `ediciones_v07/08.json` | Proporciones medidas contra la Hoja |
| 4 | V09–V10 | `receta_adan_v09.py`, `receta_adan_v10.py` | Cejas en barra, orejas en bloque, nariz cúbica, cara baja plana |
| 5 | V10c | `python -m copox.medicion.compactar` | Quita datos huérfanos |
| 6 | V11 | `python -m copox.medicion.orientar` | 24 piezas con caras invertidas, volteadas |
| 7 | V12 | `receta_theo_v05.py --solo-estilo` | Ojos, cejas, nariz y párpado (canon de estilo) |
| 8 | V13 | `receta_theo_v06.py --solo-estilo` | Normales recalculadas, rubor, boca y gorro de dos caras |
| 9 | V14 | `receta_theo_v07.py --solo-estilo` | Pómulos y orejas |
| 10 | V15 | `receta_theo_v08.py --solo-estilo` | Cráneo en caja redondeada, cuencas, párpados bajo la placa, boca no sumida |
| 11 | V16 | `receta_theo_v09.py --solo-estilo` | Pulido: picos, ceja en gestos, línea del pelo, huecos |
| 12 | V17 | `receta_theo_v10.py --solo-estilo` | Zonas lisas (boca, ojos, nariz, orejas) |
| 13 | V18 | `receta_theo_v11.py --solo-estilo` | Nuca, nariz en bloque, cejas en bloque, cara baja, ranura en las orejas |
| 14 | V19 | `receta_theo_v12.py --solo-estilo` | Sin partes sumidas |
| 15 | V20 | `receta_theo_v13.py --solo-estilo` | Cabeza lisa (superficie ajustada, grado 12) |
| 16 | V21 = **Alpha** | `receta_theo_v14.py --solo-estilo` | Parpadeo correcto con la placa nueva |

**Theo Alpha** sale de la misma cadena sin `--solo-estilo`, partiendo de Theo V03:
- Theo V01–V03 (`receta_theo_v01..03.py`) es el rostro de Theo sobre Adán V08–V10.
- Después vienen los mismos pasos 5–16. Los rasgos propios de Theo son mandíbula, sonrisa de lado y cara baja.

## Herramientas

- **SENKU** (`copox/medicion`): motor matemático.
  - Lectura de GLB, poses y paleta.
  - Medición contra la Hoja y en el marco de rostro (ED).
  - Edición de proporciones y de rostro, compactación y orientación.
- **CHXP** (`copox/render`, `LEEME_IA.md`): renderizador para Elio y Argos.
  - Modos: color, arcilla, malla, normales, curvatura y clases.
  - Sombreado `archivo` (normales como en Godot).
  - Gestos (`morph=`), láminas contra referencia y A/B, sello con código de vista.
- **Visor Godot** (`copox/godot/`): Godot 4.7.2 oficial con Xvfb y llvmpipe. Muestra el modelo como lo verá el juego.

## Medidas de Theo Alpha

1.0 = idéntico a la referencia.

| Medida | Theo V03 | Theo Alpha |
|---|---|---|
| Rasgos (ojos, cejas, boca) vs R_15/R_1/R_0/acercamiento | 0.365 | 0.466 |
| Esclerótica | 0.089 | 0.288 |
| Piel de la cara baja | — | 0.73 |
| Perfil vs Hoja (silueta) | 0.804 | 0.832 |

Techo entre las propias referencias: piel 0.75–0.93 y rasgos 0.53–0.78.
