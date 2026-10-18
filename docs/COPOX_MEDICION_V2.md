# COPOX · Motor de medición v2

17 oct 2026 · Elio (Claude) · Propuesta, sin fusionar.

## Para qué

Medir un personaje 3D contra sus referencias **imitando la pose y la cámara de cada render**. Las referencias no se corrigen: se reproducen. La meta es que el GLB, puesto igual y fotografiado igual, se vea como la referencia.

## Qué cambia frente a `alth_character_audit.py`

| Antes | Ahora (`copox/medicion`) |
|---|---|
| trimesh + scipy | Solo NumPy + Pillow |
| Malla en reposo; sin poses | Skin + morphs en cualquier clip/tiempo (`gltf.Modelo.posar`) |
| Escala por alto de la silueta (el pelo la descuadra) | Unidad **ED** = distancia entre ojos; anclas de ojos y de suelo |
| Ortográfica; 3/4 fijo a 45° | Cámara con yaw, elevación, roll y perspectiva opcional (`camara.Camara`) |
| Silueta binaria | Mapa por clases con la paleta ALTH (pelo, piel, claro, oscuro, azul), igual para referencia y modelo |
| Regiones en cajas fijas que presuponen proporciones | Perfiles de ancho por altura y puntos detectados (ojos, entrepierna, pies, cabeza) |
| Puntos del modelo por nombre de nodo | Puntos detectados en el render, igual que en la referencia |
| — | Búsqueda de pose + elevación + distancia que mejor imita la toma |

## Uso

```
python -m copox.medicion.comparar manifiesto.json --salida evidencia/ --base carpeta/
```

El manifiesto lista el GLB, las poses candidatas, elevaciones, distancias y referencias (imagen, recorte, yaw o lista de yaw, ancla). **Un manifiesto por hoja.** Las vistas de una misma hoja comparten escala, pose y línea de suelo; una imagen distinta va en otra corrida.

Salida:
- `reporte.json`: ajuste, búsqueda completa, IoU por clase, medidas y perfil de anchos por vista.
- `lamina_<vista>.png`: referencia | modelo | clases del modelo | diferencia.

## Pruebas

`python -m unittest tests.test_medicion_v2`: cámara, paleta, hueco encerrado, ojos contra ceja, perfiles y render de un cubo sintético.

## Límites

- La clasificación por color asume la paleta plana ALTH; en fotos reales no aplica.
- El ajuste de cámara es una búsqueda en rejilla (pocos valores), no una optimización continua.
- La referencia está vestida y el modelo base no: las brechas mezclan cuerpo, ropa y pelo. El reporte las separa por clase, pero la interpretación es humana.
- El rasterizador es CPU en Python: unos 4 min por hoja con búsqueda completa y unos 30 s con cámara fija.
- IoU y anchos no prueban parecido; la revisión de Admin sigue siendo el filtro final.

## Actualización · edición de proporciones (17 oct 2026, tarde)

- `copox/medicion/proporciones.py`: edita proporciones por huesos en un GLB con skin.
  - Mueve huesos y vértices con la mezcla de pesos.
  - Escala segmentos a lo largo de su eje (manos) y escala solo vértices (cuello).
  - Acorta piernas manteniendo los pies en el piso.
  - Recalcula traslaciones locales, inverseBindMatrices y normales.
  - Desplaza las claves de traslación animadas para que los clips sigan siendo válidos.
- `comparar.py`:
  - Margen de fondo alrededor de cada panel; antes el modelo se recortaba y la medida de la suela se pegaba al borde.
  - Ancla horizontal opcional `"ancla_x": "cara"` (punta de la cara) para perfiles; el centro de cabeza con pelo sesgaba la postura.
  - Guarda los mapas de clases (`clases_<vista>.npz`) y las anclas en el reporte.
- Recetas usadas con Adán: `docs/medicion/ediciones_v07.json`, `docs/medicion/ediciones_v08.json`. Manifiesto: `docs/medicion/manifiesto_hoja_theo.json`.
- Los GLB no se suben al repositorio público.

## Renderizador v1 y compactador (17 oct 2026, noche)

- `copox/render/`: renderizador para Elio y Argos (NumPy + Pillow). Instrucciones: `copox/render/LEEME_IA.md`.
  - Rasterizador vectorizado con capas por píxel; modos color, arcilla, malla, normales, curvatura, clases y clases_tri.
  - Vistas guardadas y códigos de vista; sello con modelo, hash, vista, modo, autor, fecha y código.
  - Láminas contra referencia (ancla ojos → suela) y A/B entre versiones.
  - Descarta caras traseras como Godot.
  - Medido en Theo V03 (≈90 mil triángulos): 0.1–0.3 s en `clases`, 0.6–1.1 s en modos con luz a 512 px, 2–4.5 s a 1024 px. El render anterior tardaba ≈6.5 s por vista en `clases`.
  - Concordancia con el render anterior (`clases_tri`, sin descarte de caras): 100% de píxeles iguales en 6 vistas de Adán V10 y 6 de Theo V03.
- `copox/medicion/compactar.py`: quita datos huérfanos que dejan las ediciones. Adán V10 24.0 → 7.9 MB; Theo V03 35.2 → 7.9 MB; 112 clips × 5 tiempos idénticos (diferencia 0.0) y texturas iguales.
- Pruebas: `python -m unittest tests.test_render`.

## Nombres y likeness de rostro (17 oct 2026, noche)

- Nombres de Admin: **CHXP** = renderizador (`copox/render`); **SENKU** = motor matemático (`copox/medicion`).
- `copox/medicion/orientar.py`: detecta piezas con caras invertidas (volumen con signo) y las voltea (orden de triángulos y normales). En Adán: 22 piezas de brazos, piernas y manos, más 2 del short. Se excluyen la cavidad de la boca y las placas doubleSided.
- `copox/render/rostro.py`: render del rostro en el marco de SENKU (ojos en u = ±0.5 ED, 40 px/ED) y lámina contra los parches de referencia `R_*/P_*`.
- `ocultar` en los códigos de vista acepta también nombres de material.
- Receta `docs/medicion/receta_theo_v05.py`:
  - Ojos: forma ancha, iris alto y oscuro, brillo único y párpado grueso.
  - Cejas: barra levemente inclinada, 0.08 ED más abajo.
  - Nariz: ×0.72 de ancho y ×0.65 de saliente.
  - Rasgos de Theo: cara baja −9 % y media sonrisa.
  - Con `--solo-estilo` aplica solo el canon de estilo (para Adán).
- IoU de rasgos en el marco SENKU (oscuro: ojos, cejas, boca), Theo V03 → V05:
  - R_15: 0.415 → 0.482
  - R_1: 0.352 → 0.439
  - R_0: 0.345 → 0.443
  - Esclerótica (claro): de ~0.09 a ~0.28.

## Rostro y cabeza, segunda pasada (Theo V06, Adán V13)

- CHXP:
  - `sombreado=archivo` usa las normales guardadas en el GLB, como Godot.
  - Lee `COLOR_0` (multiplica el color base en espacio lineal).
  - `render_rostro(..., px=)` permite el marco SENKU a más resolución.
- Hallazgo con `sombreado=archivo`: desde V09 (Adán) y V01 (Theo), las ediciones de rostro dejaban normales viejas. ~3,800 vértices de la cara con más de 45° de error; en Godot se verían "labios fantasma" y pliegues falsos.
  - `Editor.recalcular_normales` las rehace con el mismo criterio que el original.
  - V06/V13: 0 vértices con error.
- `Editor.color_vertices`: rubor en mejillas y nariz más rosada con `COLOR_0`. Hay que verificar en Godot que el material use el color de vértice.
- Receta `docs/medicion/receta_theo_v06.py` (sobre V05; `--solo-estilo` para Adán):
  - Boca: +0.05 ED arriba y ×1.12 de ancho, con labios e interior movidos por el mismo campo.
  - Sonrisa de lado.
  - Cara baja aplanada, sin papada.
  - Fondo negro de la boca y materiales de dos caras (boca y gorro de pelo).
  - Rubor y normales.
- Se probaron y descartaron por medición:
  - Cejas más gruesas: IoU de rasgos 0.453 → 0.441.
  - Costados de la cabeza más angostos: IoU de piel de la cara baja 0.738 → 0.718.
- Theo V06 contra R_15, R_1, R_0 y el acercamiento de la Hoja (media de las 4):
  - Rasgos oscuros: 0.453 (V03 0.365).
  - Esclerótica: 0.283 (V03 0.089).
  - Piel de la cara baja: 0.738.
- Huecos visibles en 48 tomas de cabeza: de 7,420 px (V05) a 944 (V06); 0 en la boca.

## Pómulos y orejas (Theo V07, Adán V14)

- Pedido de Admin: «pómulos muy marcados, orejas sumidas». Receta `docs/medicion/receta_theo_v07.py`:
  - Costados del cráneo y pómulos: ancho máximo de 1.28 a 1.12 ED en v −0.2…0.6, para costados rectos como en las referencias.
  - Frente de las mejillas hacia una superficie suave, más suavizado laplaciano.
  - Orejas: misma posición externa, cara interna estirada hasta el cráneo. Sobresalen ≈0.33 ED en vez de ≈0.17, y llevan un panel interior más oscuro (COLOR_0).
  - Mandíbula ×1.08 (solo Theo).
- Theo V07: rasgos oscuros 0.460 (V06 0.453); piel de la cara baja 0.731 (V06 0.738).
- Techo realista: las referencias entre sí coinciden en piel 0.75–0.93 y en rasgos 0.53–0.78 (R_15 vs R_1/R_0). Un IoU de 1.0 contra todas a la vez no es alcanzable; la meta útil es acercarse a ese techo.

## Cráneo, contorno de ojos y boca (Theo V08, Adán V15)

- Receta `docs/medicion/receta_theo_v08.py`.
- Cráneo: el cráneo real es el gorro de pelo + la máscara de la cara (la piel no cubre la parte de arriba).
  - Antes era una "bala": punta estrecha (0.78 ED en v −1.5), ancho máximo de 1.33 y pellizco en las sienes (1.13).
  - Ahora es una caja redondeada: 1.24 ED de v −1.0 a −0.5, bajada suave a 1.14 y parte alta más llena.
- Contorno de ojos: el marco venía de dos cosas.
  - Las cuencas con borde en la máscara: se rellenaron.
  - Los 4 párpados con morph de parpadeo asomaban por la placa. Abiertos quedan bajo la placa y se suma lo bajado a su morph, así el parpadeo cerrado no cambia.
  - Las placas de ojo y ceja se apoyan sobre la cara (ceja: superficie suave, nunca bajo la piel).
- Boca sumida: la zona se lleva a la superficie suave de la cara baja conservando el 35 % del detalle de los labios. El interior y el fondo se mueven igual.
- Pendiente aparte: el morph de ceja enojada (p. ej. G25_3_Amenazante) dentea la ceja. Ya venía así desde antes; es del morph original de la placa.
- Medición: rasgos 0.453, piel 0.730, Hoja sin pelo 0.718 (sin cambio). Son arreglos de forma que el IoU frontal no ve.

## Pulido (Theo V09, Adán V16)

- Receta `docs/medicion/receta_theo_v09.py`. Imperfecciones detectadas con CHXP (barrido de huecos en 90 tomas de cabeza, detector de picos por laplaciano, acercamientos):
  - Astillas en la nariz y picos en sienes y barbilla: 436 picos suavizados; se protegen los bordes abiertos y la boca.
  - Ceja dentada en gestos: se suavizan los deltas de sus 3 morphs.
  - Línea del pelo dentada:
    - Se suaviza el borde del gorro.
    - El relleno entra 1.5 mm y el contorno sale 0.8 mm.
    - El borde superior de la máscara de la cara queda bajo la tira de contorno.
  - Huecos (la cabeza es una cáscara abierta): la piel pasa a ser de dos caras y el fondo de la boca se ensancha. Theo pasa de 2,926 px a 161, Adán de 1,160 a 155. Se probó un relleno interior con elipsoide y se descartó.
  - `rostro_edicion`: `agregar_malla` y `elipsoide`.
- Mediciones sin cambio (rasgos 0.453, piel 0.730): es pulido, no forma.

## Zonas lisas (Theo V10, Adán V17)

- Receta `docs/medicion/receta_theo_v10.py`: suavizado Taubin (conserva volumen) sobre la malla soldada, pesado por zona.
  - Zonas: boca, ojos (incluye ojeras), nariz, orejas y una pasada suave de toda la cara.
  - Protegidos: bordes abiertos y la abertura de la boca.
- Rugosidad mediana (laplaciano / arista media), antes → después:
  - Ojos: 0.146 → 0.055
  - Boca: 0.101 → 0.072
  - Nariz: 0.160 → 0.094
  - Orejas: 0.090 → 0.066
  - Cara: 0.087 → 0.056
- Desplazamiento máximo: 4.3 mm.
- Se probó rehacer la nariz como bloque ideal (`nariz_limpia`): deformaba el puente y se descartó.
- Mediciones de parecido sin cambio (rasgos 0.453, piel 0.730). Huecos: 163 px en 90 tomas.

## Auditoría artística aplicada (Theo V11, Adán V18)

- Receta `docs/medicion/receta_theo_v11.py`:
  - Nuca ×1.15 en profundidad.
  - Entrecejo plano y nariz vieja fundida en la cara.
  - Nariz nueva: cubo biselado rosado de 0.26×0.24 ED que sale 0.14 ED.
  - Cejas en bloque: 10 tramos que siguen la frente, material `CEJA_BLOQUE`. Los gestos se copian de la placa vieja, que queda escondida.
  - Cara baja hacia una superficie simétrica de 4.º orden.
  - Orejas con ranura en C.
- Theo V11:
  - Rasgos oscuros: 0.469 (V10 0.453).
  - Perfil contra la Hoja: silueta 0.832 (0.804) y sin pelo 0.653 (0.634).
  - Huecos: 129 px.
- Pendiente de decisión de Admin: boca como calcomanía. Hoy la boca se anima con 8 morphs (boca_soplar, abrir, sonrisa, triste, o, tensa, lado_L y lado_R); con calcomanía se cambiaría por texturas.
- Pelo: al final, por pedido de Admin.

## Sin partes sumidas (Theo V12, Adán V19)

- Receta `docs/medicion/receta_theo_v12.py`:
  - Relleno de hundidos: el laplaciano solo se aplica hacia afuera, así llena cuencas sin rebajar bultos.
  - Después, Taubin suave en toda la piel de la cabeza.
  - Protegidos: la boca y los bordes. Nariz, cejas, ojos y orejas ya son piezas aparte.
- Vértices cóncavos fuera de la boca: 2.6 % → 0.2 %. Desplazamiento máximo 4.9 mm.
- Rasgos 0.470, piel 0.730. Huecos: 130 px.
- Decisión de Admin: la boca NO será calcomanía (se queda de malla con sus 8 morphs).
- Pupilas: hoy no se mueven. No hay huesos de ojo, y los morphs de las placas de ojo son solo `alegre_L/R`; el iris está pintado en la textura.

## Cabeza lisa (Theo V13, Adán V20)

- Receta `docs/medicion/receta_theo_v13.py`: la piel de la cabeza y el gorro de pelo se reemplazan por una superficie ajustada.
  - Ajuste: radio por dirección desde el centro de la cabeza, con un polinomio de grado 12 (piel) y 10 (gorro).
  - Se conserva el detalle solo en la boca, en las caras interiores y junto a los bordes.
  - Las piezas pegadas a la cara (ojos, párpados, cejas, nariz, orejas) siguen a la piel nueva.
- Movimiento de la piel: mediana 0.28 mm, p95 1.3 mm, máximo 4.8 mm.
- Se probó una relajación tangencial con reproyección: movía hasta 9 mm y empeoraba las uniones; se descartó.

## Gestos y Godot (Theo V14, Adán V21)

- CHXP: clave `morph=nombre:peso,...` en los códigos de vista (`Modelo.posar(morphs=...)`).
- Revisión de los 18 gestos (`tools`: lámina por gesto con base, frente, 3/4 y arcilla; huecos 0 en todos):
  - Roto: parpadeo. El párpado cerrado quedaba detrás de la placa y se veía un aro blanco.
  - Receta `docs/medicion/receta_theo_v14.py`: el párpado cerrado queda 1 mm delante de la placa y la placa se encoge al 80 % y se mete 3 mm al cerrar.
  - Débiles pero no rotos: `boca_o` y `boca_soplar` abren poco, porque la boca de Theo es una línea fina.
- Godot 4.7.2 (oficial, descargado de GitHub) corre en el entorno de Elio con Xvfb + Mesa llvmpipe (Compatibilidad; sin Vulkan). Visor mínimo en `copox/godot/`.
  - Confirmado en Godot: skin y 112 clips, morphs, color de vértice (rubor, nariz, orejas), materiales de dos caras y tamaño.
  - Godot quita el sufijo `-loop` de los clips.

## ADÁN ALPHA (17 oct 2026)

- Admin nombra **Adán Alpha** a la versión Adán V21 (sha `bf6ec140…`); Theo Alpha = Theo V14 (sha `6dcf8acd…`).
- Documentación completa y cadena de reconstrucción: `docs/ADAN_ALPHA.md`. Reconstrucción V10 → Alpha verificada bit a bit (`docs/medicion/construir_adan_alpha.sh`).
- Se agregan al repo las recetas que faltaban (hallazgo de la auditoría): `receta_adan_v05_limpieza.py`, `receta_adan_v06_neutro.py` y `glb.py`.
