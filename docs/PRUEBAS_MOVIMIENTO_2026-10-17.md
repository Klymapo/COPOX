# Pruebas de movimiento · Adán Alpha con gestos (Adán V22 HABLA)

- **Fecha:** 17 oct 2026 · Elio (Claude) para Admin.
- **Modelo:** `ADAN_V22_HABLA.glb`, SHA-256 `df8d4b96800cc7a05b05400b456df22529733bc66353259b82c265f6168e9748` (no se sube al repo).
- **Motor:** Godot 4.7.2 oficial (Compatibilidad, llvmpipe) + SENKU (`copox/medicion`) + CHXP (`copox/render`).
- **Capturas:** rama `capturas`, carpeta `capturas/2026-10-17/ADAN_V22_HABLA/elio/movimiento/`.

## Herramientas nuevas

| Pieza | Dónde | Qué hace |
|---|---|---|
| `BancoMovimiento` | `copox/godot/movimiento/banco_movimiento.gd` | AnimationTree por capas: cuerpo (máquina de estados con fundido 0.3 s), cara (máquina de estados, solo morphs, fundido 0.2 s), parpadeo automático (one-shot filtrado a `parpado_L/R`) y mirada (`OjosALTH`). Los gestos de una sola vez regresan solos a `Idle`. Sirve tal cual para el juego. |
| Banco de pruebas | `copox/godot/movimiento/prueba_movimiento.tscn` | Modos `secuencia` (escena guionada → frames), `clips` (n frames de cada clip, varias vistas) y `caras` (primer plano de cada expresión). |
| SENKU · movimiento | `copox/movimiento/analizar.py` | Por clip y por frame: huesos activos, clips vacíos, estiramiento de aristas, mano dentro de cabeza o torso, y piso. |
| Láminas | `copox/movimiento/laminas.py` | Hojas de contacto y GIF a partir de los frames. |

Uso rápido:

```
cp ADAN_V22_HABLA.glb copox/godot/theo.glb
godot --headless --path copox/godot --import
xvfb-run -a godot --path copox/godot res://movimiento/prueba_movimiento.tscn -- modo=secuencia salida=/tmp/sec
python -m copox.movimiento.laminas gif /tmp/sec escena.gif
python -m copox.movimiento.analizar ADAN_V22_HABLA.glb analisis.json
```

En el juego:

```gdscript
var banco := BancoMovimiento.new()
add_child(banco)
banco.montar($Adan)
banco.gesto("Wave", "G23_1_Saludo")
banco.mirada = Vector2(0.3, 0.0)
```

## Inventario de clips (112)

| Grupo | Cuántos | Estado |
|---|---|---|
| Gestos de cuerpo (`Idle`, `IdlePockets`, `HandsBehind`, `TalkGesture`, `GlassesPush`, `TieAdjust`, `Think`, `Shrug`, `Nod`, `HeadShake`, `Laugh`, `Point`, `Wave`) + `Sit-pose` | 14 | Funcionan, 45–51 huesos activos. |
| `*Face` de cada gesto | 13 | **Vacíos**: solo traen `Root` sin moverse. El banco los omite y usa en su lugar las expresiones G*. |
| Expresiones G23–G26 | 20 | Funcionan (morphs + giro leve de cabeza y cuello). |
| `Talk-loop`, `Blink`, V04 (ojos) | 5 | Funcionan. |
| Poses de autor P15–P20 | 30 | Poses fijas de 0.3 s (4–14 huesos). |
| Manos M31–M36 | 30 | Poses de dedos de 0.3 s. |

No hay caminar, correr, saltar ni girar. Para moverse por el mundo hacen falta clips nuevos.

## Hallazgos (ordenados por impacto)

1. **Párpado entrecerrado o cerrado.** El párpado es una placa color piel que tapa el ojo, sin línea de pestaña. Cerrado se ve como un parche; a medias deja el iris recortado y en Godot aparece ruido de pixeles en el borde (las dos superficies quedan casi en el mismo plano). Se ve igual en CHXP, así que es del modelo, no del motor. Afecta a 9 de las 20 expresiones G (Observador, Sospecha, Frío, Desafiante, Desprecio, Dominante, Concentrado, Fastidio) y a los guiños (RespuestaAmable, RisaContenida, V04).
2. **Boca casi muda.** En casi todas las expresiones la boca apenas cambia; la emoción la cargan las cejas. Ya se sabía de `boca_o` y `boca_soplar`.
3. **Poses heredadas del detective.** `GlassesPush` lleva la mano a unos lentes que Adán no tiene y `TieAdjust` a una corbata que no tiene. Con la cabeza chibi, `P18_3_Duda` y `P19_2_Observador` meten la mano en la cara.
4. **Hombro con el brazo muy arriba.** Con el brazo arriba de ~110° se colapsan aristas del hombro (SENKU: hasta ×90 en `P15_3_Timido`, ×57 en `P15_2_Curioso` y `P19_2_Observador`, ×26 en `Think`). Visualmente se nota como hombro aplastado contra el pecho.
5. **Inclinaciones exageradas.** `P15_2_Curioso`, `P15_3_Timido`, `P17_5_Cansado` y `P18_5_Verguenza` doblan tanto el cuello que la cabeza grande parece desprenderse. `P16_1_Feliz` y `P16_5_Jugueton` levantan una pierna sin equilibrio.
6. **Manos.** El pulgar se separa en pedazos en los puños (`M31_3_Puno`, `M33_5_Afirmar`). `M31_4_Senalar` no extiende el índice (sale casi puño). Hay un aro oscuro en la muñeca.
7. **Gestos de cabeza tímidos.** `Nod`, `HeadShake` y `Laugh` se notan muy poco con la cabeza grande; necesitan más amplitud.
8. **Lo que está bien.** No hay pies que se hundan (piso estable, ±0.2 % del alto); `Wave`, `Point`, `Think`, `Shrug` y `TalkGesture` se leen claros; el fundido entre gestos no salta; la mirada con shader funciona junto con el parpadeo.
9. **`Sit-pose`** sube el cuerpo 8.6 % del alto: está pensada para una silla, no es error.

## Cifras de SENKU

`estira` = mayor razón de largo de arista contra el reposo (1.0 = igual). En las caras la cifra es alta por diseño (el párpado se cierra) y no se usa para juzgar.

| Clip | Huesos | Estira máx (hueso) | Mano en torso |
|---|---|---|---|
| Idle | 51 | 4.4 (LeftHand) | 0 |
| IdlePockets | 51 | 6.0 (RightLowerLeg) | 9 vértices (manos sobre el short) |
| HandsBehind | 51 | 6.7 (RightShoulder) | 0 |
| TieAdjust | 47 | 8.4 (RightShoulder) | 0 |
| Think | 47 | 26.3 (RightShoulder) | 0 |
| Wave | 46 | 4.7 (RightHand) | 0 |
| P15_3_Timido | 12 | 90.3 (LeftShoulder) | 0 |

El JSON completo queda junto a las capturas (`analisis_v22.json`).

## Siguiente paso propuesto (lo decide Admin)

1. Rehacer el párpado: línea de pestaña oscura que baja, sin placa de piel.
2. Clips de locomoción: caminar, correr, girar y detenerse.
3. Limpiar o rehacer las `*Face` vacías, y quitar o adaptar `GlassesPush` y `TieAdjust`.
4. Corregir hombro, pulgar y `Senalar`; subir amplitud de `Nod`, `HeadShake` y `Laugh`.
