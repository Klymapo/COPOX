# ALTH-META · Ruta a calidad AAA (modelos, nube, animación)

*Elio para Admin · 20 oct 2026 · diseño aprobado por Admin el mismo día («Documenta todo, termina las herramientas, Actions está bien, no hagas pruebas piloto»). Herramientas hechas: §10.*

---

## 0. Resumen corto

- **La base está fuerte.** El cuerpo congelado de Adán, la cara con 46 morphs, el esqueleto de 148 huesos, unas 130 animaciones, el pelo con resortes, SENKU, CHXP V3, el catálogo y `crear-avatar` / `publicar` en un comando funcionan.
- **La brecha que queda es de técnica, no de esfuerzo.** Las referencias están hechas de **bloques con bisel**: caras planas, aristas redondeadas pero definidas, y paneles y pliegues como geometría. Nuestra ropa y nuestro pelo salen de **SDF → marching cubes → suavizado**, y eso produce formas blandas y borra las aristas.
- **Para cinemáticas faltan cuatro cosas de producción:**
  - topología con anillos en las articulaciones;
  - UVs;
  - horneado (oclusión y curvatura);
  - pesos de ropa que no se atraviesen en poses.
- **Todo puede vivir en la nube** y orquestarse desde el teléfono. El único hueco real es la **GPU**: sin ella quedan fuera las IA de imagen o video a 3D, y el render de cine se hace en CPU (más lento, pero gratis).
- **Animación:**
  - **Cuerpo:** IK nativo de Godot 4.6+, librería de mocap libre y retarget a proporción chibi.
  - **Cara:** video del celular → MediaPipe (52 blendshapes, CPU) → nuestros morphs; voz → Rhubarb (visemas, CPU).

---

## 1. Dónde estamos (medido el 20 oct)

| Pieza | Estado |
|---|---|
| **Theo** `THEO_VESTIDO_V4_2` | Cara buena. Pantalón débil («está bien por ahora»). |
| **Alastor** `ALASTOR_V11` | CHXP V3 PASS 15/0; el revisor lo dejó en UNA_CORRECCIÓN, con una ceja en 3/4 detrás del rizo. |
| **Malla Alastor** | 81 primitivas, de las cuales **69 sin UV**. ADAN_CUERPO tiene ~76 k tris y el total ~117 k (tope 160 k). Incluye piezas intercambiables ocultas (pies, manos, guía capilar). |
| **Rig** | 148 huesos (con 15 de dedo por mano), 46 morphs faciales, unos 130 clips (locomoción, gestos, emociones, manos, armas). |
| **Auditoría** | CHXP V3: 15 compuertas, más el revisor visual obligatorio. |

**Prueba en T-pose contra las referencias (hoy)**

*Theo*
- **Cara:** es lo que más se parece.
- **Pelo:** en la referencia son mechones grandes y limpios; el nuestro sale picado y ruidoso.
- **Chaleco:** a la referencia le sobran cosas que el nuestro no tiene: cuello en V con solapa, bolsillos con cartera y cinturón trasero con hebilla.
- **Pantalón:** el de la referencia es ancho, se angosta abajo, tiene raya y dobladillo grueso. El nuestro son dos tubos rectos con la pretina dentada.
- **Zapatos:** el de la referencia es una caja con escalón; el nuestro es redondeado y bajo.

*Alastor*
- **Lo bueno:** silueta, lentes, corbata y hebilla se leen bien.
- **Rizo de perfil:** sale como cuerno.
- **Abrigo:** en la referencia termina a media pierna y deja ver más pantalón. El nuestro es largo y recto, y le faltan bolsillos y botones.
- **Pelo:** en la referencia tiene más volumen y mechones más grandes.
- **Piel:** más pálida y amarilla que la de la referencia.

---

## 2. Causas raíz

1. **Lenguaje de forma.** El SDF da superficies suaves y continuas, y el estilo pide planos y biseles. La prueba está en el propio repo: lo que más se parece a la referencia es lo que *no* salió del SDF.
   - el zapato y el pie, hechos con loft por secciones (V46);
   - el rizo, hecho con barrido de sección superelíptica.
2. **Diseño de prendas incompleto.** Faltan piezas: bolsillos, carteras, botones, raya del pantalón, dobladillo, solapas del chaleco y cinturón trasero.
3. **Topología no apta para primeros planos.** Marching cubes deja una sopa de triángulos sin anillos de aristas en codos y rodillas, y la deformación se ve mal de cerca.
4. **Sin UV ni horneado.** Sin UV no hay mapa de normales, no hay oclusión horneada ni texturas pintadas. Es justo el «acabado» que tienen las referencias.
5. **Pesos de ropa por cercanía.** Las capas se atraviesan en poses (PLATEAU desde Theo) y aparecen picos como los del abrigo (V04–V06).
6. **Render de comparación distinto.** Las referencias tienen luz global suave y oclusión ambiental. CHXP usa el renderer Compatibility de Godot sin GPU. Parte de la diferencia es luz, no modelo.
7. **Métricas ciegas a «lo blando».** Nada mide la nitidez de las aristas, por eso un abrigo inflado pasa 15/0.

---

## 3. Cómo lo hace el gremio (personaje estilizado para juego)

Flujo estándar:
1. **Bloque de formas grandes.** Manda las proporciones; el detalle no arregla formas malas.
2. **Esculpido con bisel por *creasing*.** La diferencia entre el nivel de subdivisión y el de pliegue controla qué tan suave se ve la arista.
3. **Retopología.** Malla de baja limpia, con anillos en las articulaciones.
4. **UV.** Las piezas espejo comparten UV.
5. **Horneado.** Normales primero, luego oclusión y curvatura, pieza por pieza para que la sombra no se mezcle.
6. **Textura.** Color base pintado más capas sutiles de desgaste y rugosidad, solo donde hay interés.
7. **Rig y pesos.**
8. **Presentación.** Luz de estudio y, opcionalmente, contorno con casco invertido.

Lo que ya tenemos: 1 (SENKU) y 7 (base de Adán). **Nos faltan 2, 3, 4, 5 y 6**, y todos se pueden hacer por código en Blender sin interfaz.

---

## 4. Herramientas: qué mejorar y qué crear

### 4.1 NUEVA · «Tallador» de prendas y pelo (prioridad 1)
- **Idea:** generalizar el loft del zapato y el barrido del rizo, sin pasar por SDF.
  - Cada prenda es una cadena de **secciones poligonales de 8 a 12 lados** que siguen al cuerpo (como `ropa_tubos`, pero sin malla implícita).
  - Las aristas se marcan como «duras» o «suaves».
  - Al final, **bisel en las aristas marcadas** y **normales ponderadas** (*weighted normals*: el truco estándar para que las caras planas se vean limpias).
- **Detalles como piezas propias:** bolsillo con cartera, botón, raya del pantalón, dobladillo grueso, solapa y cinturón trasero. Serían módulos del catálogo con parámetros.
- **Pelo:** mechones grandes tallados, cada uno con un barrido de sección biselada, siguiendo las masas que ya medimos con SENKU.
- **De regalo:**
  - **anillos en las articulaciones**, porque las secciones ya están ordenadas;
  - **UV casi gratis**: las secciones se desenvuelven como cilindros;
  - menos triángulos con más forma.
- **Cómo:** Blender como módulo (`alth-python`) con `bmesh.ops` (bevel, bridge, weighted normals), sin operadores de interfaz, como pide el CLAUDE.md.
- **Regla:** técnica geométrica nueva, así que va **research brief antes** (skill `investigar-referencias`). Piloto en **una** prenda, con **3 intentos máximo**.

### 4.2 Transferencia robusta de pesos (prioridad 2)
- **Qué es:** «Robust Skin Weights Transfer via Weight Inpainting» (SIGGRAPH Asia 2023). Copia los pesos del cuerpo a la ropa solo donde la correspondencia es confiable y **rellena** el resto con suavidad.
- **Disponible como:** código abierto más un add-on gratuito de Blender.
- **Resuelve:** las capas que se atraviesan y los picos de bajos y faldas.
- **Pendiente:** verificar la licencia antes de integrarlo.
- **Mientras tanto:** lo de V11 (soldar duplicados y alisar pesos) queda como paso estándar de toda prenda.

### 4.3 UV + horneado (prioridad 3)
- **UV:** desenvolver por secciones (sale del tallador) o UV inteligente para piezas sueltas.
- **Horneado:** oclusión ambiental y curvatura con **Cycles en CPU** (sin interfaz, gratis), a textura o a color de vértice.
- **Resultado:** sombreado suave en pliegues y uniones, sin depender de la GPU al jugar.
- **Cuerpo de Adán:** no se toca la base congelada. Se hace una **versión nueva** con UV y horneado que Admin aprueba y congela.

### 4.4 CHXP «de cine» (prioridad 2, en paralelo)
- **Lámina T-pose contra referencia, oficial.** Lo de hoy, como vista estándar.
- **Render de comparación** con luz parecida a la referencia (Blender Cycles en CPU): luz suave, oclusión, sombra de contacto. Así se compara modelo con modelo y no luz con luz.
- **Primeros planos fijos:** cara, manos, bajo de prendas y una cámara cinematográfica (lente de 50–85 mm).
- **Métrica nueva «nitidez de aristas»:** histograma de normales y bordes de sombreado contra la referencia. Detecta lo «blando» que hoy pasa en verde.
- **Gate de capas en las 130 animaciones:** no solo en 3 GIF; muestreo de cuadros en todos los clips.

### 4.5 SENKU (ajuste menor)
- Medir **anchos por región de prenda**: abertura del pantalón, largo del abrigo, alto del dobladillo. Que la ficha traiga esos números y no solo colores.

---

## 5. Todo en la nube, orquestado desde el teléfono

### 5.1 Arquitectura propuesta (gratis)

| Capa | Dónde | Para qué |
|---|---|---|
| **Mando** | Esta sesión de Claude (nube) desde el celular | Pides, revisas láminas, apruebas («Lápiz/Martillo»). |
| **Taller** | Contenedor de la sesión (CPU, Blender + Godot) | Recetas, tallador, CHXP, horneado. Es lo que ya usamos. |
| **Cola larga** | GitHub Actions | Renders de cine por cuadros repartidos en varios jobs, regresión de 130 clips, corridas nocturnas. |
| **Estado** | `copox-modelos` (privado) + rama `capturas` | GLB, SHA, evidencia. |
| **Memoria** | Drive de Gaston (Memoria maestra) | Registro de cambios. |
| **Vista en el celular** | Láminas PNG/GIF y video MP4 en el chat; opcional, una página de revisión | Revisar desde el teléfono. |

### 5.2 Límites reales (para decidir)
- **Sin GPU gratis y sin cuota.**
  - GitHub Actions gratis es solo CPU (4 núcleos, 16 GB, 6 h por job).
  - Kaggle da GPU T4 con **cuota semanal**. Choca con la regla «sin usos diarios», así que lo decides tú.
- **Cycles en CPU es lento pero viable.**
  - Un cuadro de cine puede tardar minutos. Para 10 s a 24 fps (240 cuadros), se reparten los cuadros en varios jobs de Actions en paralelo.
  - Los repos **privados** tienen minutos limitados por mes y los **públicos** no, pero en un repo público la evidencia queda visible. Hay que cuidar no exponer los GLB privados.
- **Godot de alta calidad** (Forward+ con luz global) pide Vulkan y GPU. En la nube se puede emular por software, pero es muy lento. **Recomendación:**
  - **juego:** Godot;
  - **cinemáticas finales:** Blender Cycles en CPU en la nube, con el mismo GLB, la misma animación y la misma cámara.
- **IA de imagen o video a 3D** (TRELLIS.2, captura de movimiento por video): requiere GPU. Sin ella, opciones solo de CPU (sección 6).

### 5.3 Flujo desde el celular (ejemplo)
1. «Martillo, pantalón de Theo con el tallador».
2. La sesión construye y corre CHXP.
3. Te llegan la lámina T-pose contra referencia, los primeros planos y el GIF.
4. Apruebas o corriges con texto o con una foto marcada.
5. Se publica: copox-modelos, ULTIMA, Drive.
6. Para una cinemática: «render escena 3» → Actions reparte los cuadros → llega el MP4 al chat.

---

## 6. Animación y movimiento

### 6.1 Cuerpo

**Lo que hay:** unos 130 clips y locomoción con IK en código. El chibi tiene cabeza grande y brazos cortos: las manos no alcanzan la cara igual que en un humano, y los clips humanos «tal cual» atraviesan la cabeza y el torso.

**Opciones, de menor a mayor costo:**
1. **IK nativo de Godot (4.6+, usamos 4.7.2).** Se puede pasar el IK de código a modificadores nativos:
   - `TwoBoneIK3D` para piernas y brazos: pies anclados al piso, manos a objetos.
   - `LookAtModifier3D` para que la cabeza y los ojos sigan objetivos.
   - `SplineIK3D` y `FABRIK3D` para colas, corbatas y cadenas.
   - `BoneTwistDisperser3D` para que el antebrazo no se tuerza como envoltura de dulce.
   - `LimitAngularVelocityModifier3D` para suavizar.
   - `RetargetModifier3D` para retargetear conservando el reposo de los huesos.
   - `SpringBoneSimulator3D` (ya lo usamos en el pelo) también sirve para corbata, faldón del abrigo y mechones.
2. **Librería de mocap libre + retarget a proporción chibi.**
   - **CMU Motion Capture Database:** gratis y de uso libre.
   - **Mixamo:** gratis con cuenta de Adobe y usable en juegos, pero se descarga a mano desde la web. No es automatizable ni CC0.
   - **Paso clave:** un **corrector chibi** después del retarget.
     - escala de zancada al largo de pierna;
     - offset de manos para no atravesar la cabeza y el torso;
     - contacto de pies con IK;
     - exageración de poses: el chibi lee mejor con poses más marcadas, *squash & stretch* moderado y anticipación.
3. **Video del celular → movimiento** (actúas tú o un actor):
   - **CPU:** MediaPipe Pose. Gratis y rápido, pero el 3D es ruidoso. Sirve para bloquear poses, no para cine.
   - **GPU:** GVHMR (SIGGRAPH Asia 2024) y similares. Calidad mucho mejor, pero necesita GPU y usa el modelo corporal **SMPL, cuya licencia es de investigación y no comercial**. **No apto** para un juego comercial sin licencia aparte.
4. **Texto → movimiento** (MoMask y similares). Interesante para prototipos, pero requiere GPU y los modelos entrenados con datos SMPL o HumanML3D arrastran las mismas restricciones. **No recomendado por ahora.**

**Recomendación (cuerpo):** IK nativo + corrector chibi + CMU (y Mixamo a mano si hace falta). Para cine, **animación por capas**: base (mocap o clip) + capa de actuación a mano por código (poses clave) + IK de contacto + resortes secundarios.

### 6.2 Cara

**Lo que hay:** 46 morphs (cejas, párpados, boca, comisuras, emociones P15–P20 y G23–G26), parpadeo y ojos con pupila.

**Opciones:**
1. **Video del celular → cara (CPU, gratis).**
   - **MediaPipe Face Landmarker** (Apache 2.0) da **52 blendshapes tipo ARKit** por cuadro, en CPU.
   - Grabas tu cara en el teléfono, lo subes al chat y sale la curva de cada blendshape.
   - Hace falta una **tabla de 52 → nuestros 46 morphs**, con los faltantes creados en una versión nueva de la cara. Faltarían, por ejemplo, `jawOpen`, `mouthPucker`, `mouthFunnel`, `cheekPuff`, `tongueOut` y las miradas.
2. **Voz → boca (CPU, gratis).**
   - **Rhubarb Lip Sync:** línea de comandos, multihilo, local. Da visemas A–F más G, H y X opcionales.
   - Su reconocedor bueno es **solo en inglés**. Para **español** usa el reconocedor *fonético*, que es menos preciso pero sirve.
   - Mapear los visemas a los morphs de boca y mezclar con la emoción de la escena.
3. **Voz → cara completa (GPU).**
   - **NVIDIA Audio2Face 3D** se liberó como código abierto (sep 2025): modelos, SDK y marco de entrenamiento.
   - **Pendiente verificar:** licencia exacta, requisitos de GPU (casi seguro NVIDIA) y si exporta blendshapes compatibles.
   - Opción futura si hay GPU.
4. **Estilo chibi.**
   - Además de morphs suaves, las caras chibi de calidad usan **expresiones «de golpe»**: ojos cerrados en arco, ojos de sorpresa, gota de sudor, rubor. Se pueden hacer como **piezas intercambiables** con KHR_node_visibility, que ya usamos.
   - **Ojos vivos:** micro-sácadas, parpadeo con ritmo natural y que los ojos se adelanten un poco al giro de la cabeza (`LookAtModifier3D`).

**Recomendación (cara):** MediaPipe (actuación desde el celular) + Rhubarb (diálogo) + capa de emoción a mano, todo en CPU. Antes: **cara V nueva con los blendshapes ARKit que faltan**, aprobada y congelada por Admin.

### 6.3 Cinemáticas (cómo se arma una escena)
1. **Guion de escena** (texto): planos, cámara, diálogo, emociones.
2. **Por personaje:** clip base o mocap → corrector chibi → IK de contacto → capa de actuación → cara (MediaPipe o Rhubarb + emoción) → resortes.
3. **Cámara:** lente, movimiento y profundidad de campo, todo en un JSON de escena.
4. **Previa** en Godot (rápida, CPU) → **final** en Cycles (CPU repartido en Actions) → MP4 al chat.

---

## 7. Plan por fases

| Fase | Qué | Sale | Riesgo |
|---|---|---|---|
| **F0** (Lápiz) | Este documento; Admin decide en la sección 8 | Decisiones | — |
| **F1** | Research brief: tallador con bisel + pesos robustos | `docs/investigacion/tallador.md`, `pesos_robustos.md` | Bajo |
| **F2** | Piloto del tallador en el **pantalón de Theo** (3 intentos máximo) | Theo V5 con lámina T-pose contra referencia | Medio |
| **F3** | Extender a chaleco → zapatos → abrigo (más corto, con bolsillos y botones) → pelo (Theo y Alastor) | Theo V6, Alastor V12+ | Medio |
| **F4** | CHXP de cine: render Cycles, primeros planos, métrica de aristas, regresión de 130 clips | CHXP V4 | Bajo |
| **F5** | UV + horneado + pesos robustos; Adán con UV como versión nueva para aprobar | Adán V51 (propuesta) | Medio |
| **F6** | Cara: blendshapes ARKit + MediaPipe + Rhubarb | Cara nueva + skill `actuar-cara` | Medio |
| **F7** | Cuerpo: IK nativo + corrector chibi + CMU | Skill `animar-escena` | Medio |
| **F8** | Primera cinemática corta (10–15 s) desde el celular | MP4 | Alto (tiempo de CPU) |

Cada fase pasa por CHXP, el revisor visual y tu aprobación. Nada se congela sin ti.

---

## 8. Decisiones de Admin (20 oct 2026)

1. **GPU:** Kaggle es gratis pero con cuota semanal (≈ 30 h reportadas por usuarios; Kaggle no publica el número; sesiones de 12 h; GPU T4 de 16 GB, insuficiente para TRELLIS.2). **Queda fuera por ahora**: todo en CPU.
2. **Motor de cinemáticas:** **Blender** (Cycles CPU) en GitHub Actions.
3. **Nube:** **Actions está bien.** Cine en el repo COPOX (público, minutos ilimitados; los GLB privados sólo con el secreto `MODELOS_TOKEN`, nunca se suben como artifact). Animación con material de Admin (video/voz) en `copox-modelos` (privado).
4. **Arranque:** herramientas sí; **pruebas piloto no** (no se fabricó ninguna versión nueva de Theo ni de Alastor con las herramientas nuevas).
5. **Pendiente de Admin:** colores de la base fuera de paleta (CEJA_BLOQUE #57351A, BOCA_INTERIOR_NEGRO, LENGUA_ALTH); Mixamo como fuente manual; crear el secreto `MODELOS_TOKEN` para cine con GLB privados.

---

## 9. Licencias y riesgos

| Herramienta | Licencia | Uso |
|---|---|---|
| Blender, Godot | Libres | Sí. |
| MediaPipe | Apache 2.0 | Sí. |
| Rhubarb | Licencia propia (LICENSE.md); se descarga en el workflow, no se redistribuye | Revisar antes de distribuir. |
| Robust Weights Transfer | **MIT** (verificado 20 oct); implementación propia en numpy/scipy | Sí. |
| TRELLIS.2 | MIT | Pide GPU de 24 GB y no está afinado a estética. |
| GVHMR, MoMask | Ligados a SMPL o HumanML3D (no comercial) | **Evitar para el juego.** |
| Audio2Face | Licencia por verificar | — |

**Riesgos de proceso:**
- **Tiempo de CPU en cine:** mitigar con previa en Godot y final repartido en jobs.
- **Cambio de técnica:** puede tardar 2–3 versiones en igualar lo que ya tenemos. Por eso se pilotea en una sola prenda.

---

## 10. Herramientas hechas (20 oct 2026)

| Herramienta | Archivo | Qué hace | Probada con |
|---|---|---|---|
| Tallador | `copox/medicion/tallador.py` | Perfiles 2D con bisel y aristas duras → secciones → quads; normales ponderadas por área con suavizado por ángulo y costuras; UV por sección; escalón (dobladillo/pretina); barrido por curva con marcos de transporte paralelo; `a_prim` → primitiva glTF | `tests/test_tallador.py` (10 pruebas sintéticas) |
| Pesos robustos | `copox/medicion/pesos_robustos.py` | Punto más cercano en superficie + baricéntricas, confiables por distancia/ángulo, relleno con Q = −L + L M⁻¹ L (cotangente), soldado de costuras, top-4 | `tests/test_pesos_robustos.py`; escala real: abrigo de Alastor (2.7 k vértices) en 0.1 s |
| CHXP T-pose | `copox/render/chxp3.py` (`tpose`, `--cerca`, `--sin-tpose`) | `<nombre>_TPOSE.png` (reposo del esqueleto, 4 vistas contra la referencia) en todo personaje/ropa/pelo; `<nombre>_CERCA.png` primeros planos | ALASTOR_V11 (lámina sin publicar) |
| Nitidez de aristas | `copox/render/aristas.py` + compuerta `nitidez_aristas` (informativa) | Densidad de bordes de sombreado dentro de la silueta, render ÷ referencia | ALASTOR_V11: frente 0.69, 3/4 0.60 (V06: 0.56) |
| Cine | `copox/cine/` + `.github/workflows/alth-cine.yml` | Escena JSON (cámara por cuadros clave, relativa al alto), Blender Cycles CPU repartido en jobs, MP4; AO por vértice → `.npz` → `aplicar_ao` (COLOR_0 de un GLB nuevo) | Actions: `assets/alastor_delta/alastor_delta.glb`, clip Wave, 24 cuadros en 3 jobs → MP4 en la rama `capturas` (`cine/2026-10-20/`); AO horneado OK (Blender 5.0.1) |
| Instalador de Blender en CI | `tools/blender_ci.sh` | `ensure_blender.sh` y, si falla, bpy sin versión fija; errores como anotaciones | Actions |
| Cara desde video | `copox/movimiento/cara_arkit.py` | MediaPipe (52 ARKit) → morphs ALTH con calibración neutral, One Euro, espejo; mirada como curva; lista de ARKit que faltan en la cara | `tests/test_animacion_alth.py` |
| Labios | `copox/movimiento/labios.py` | Rhubarb fonético (español) → vis_A…vis_FV con coarticulación | pruebas sintéticas |
| Mocap | `copox/movimiento/bvh.py` | BVH (CMU/Mixamo) → rig de Adán por rotaciones de mundo, giro de frente automático, raíz escalada a la pierna chibi, manos fuera de la cabeza, pies sobre el piso | BVH sintético `tests/fixtures/mini_tpose.bvh` |
| Clips en GLB | `copox/movimiento/clip_gltf.py` | Escribe clips de huesos y de morphs | — |
| IK nativo | `copox/godot/movimiento/ik_nativo.gd` (`IKNativoALTH`) | TwoBoneIK3D (piernas, brazos, con polos), LookAtModifier3D (cabeza), pies sobre el piso | Godot 4.7.2 headless: mano a 2 cm del objetivo |
| Animación privada | `copox-modelos/.github/workflows/alth-animacion.yml` + `entradas/` | Cara/labios/mocap en Actions privado → GLB nuevo como artifact privado | Actions privado: BVH sintético → GLB con clip en la rama `resultados-animacion` |

Lo que NO se hizo (por decisión de Admin): ninguna prenda o personaje nuevo con el tallador ni con pesos robustos; ninguna cara con blendshapes ARKit nuevos. Son los siguientes pasos cuando Admin dé «Martillo».

---

## Fuentes
- [Flujo de personaje estilizado, del bloque al render (80.lv)](https://80.lv/articles/001agt-stylized-character-art-workflow-from-blockout-to-render)
- [Modelado de personaje estilizado para juegos (Gnomon)](https://katunsworth.artstation.com/projects/29lzOg)
- [Robust Skin Weights Transfer, código](https://github.com/rin-23/RobustSkinWeightsTransferCode) · [proyecto, U. de Toronto](https://dgp.toronto.edu/~rinat/projects/RobustSkinWeightsTransfer/index.html) · [add-on de Blender (80.lv)](https://80.lv/articles/grab-this-one-click-blender-tool-for-effortless-weight-transfers/)
- [TRELLIS.2-4B, ficha del modelo](https://huggingface.co/microsoft/TRELLIS.2-4B/blob/main/README.md)
- [Godot 4.6: el IK regresa (nodos de modificadores)](https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/)
- [GVHMR, código](https://github.com/zju3dv/GVHMR) · [artículo](https://arxiv.org/html/2409.06662v1)
- [MoMask, código](https://github.com/EricGuo5513/momask-codes)
- [Rhubarb Lip Sync (resumen del repo)](https://awesome.ecosyste.ms/projects/github.com%2Fdanielswolf%2Frhubarb-lip-sync)
- [NVIDIA libera Audio2Face (OpenSourceForU)](https://www.opensourceforu.com/2025/09/nvidia-moves-audio2face-technology-to-open-source/) · [modelo en Hugging Face](https://huggingface.co/nvidia/Audio2Face-3D-v3.0/commit/03aba3375b39dd6efd473602d42f4eb4661d43ad)
- [MediaPipe Face Mesh / blendshapes (documentación del paquete)](https://pub.dev/documentation/mediapipe_face_mesh/2.9.0/)
- Investigación previa del proyecto: `claude/investigacion-meshy-tripo-plan.md` (1 oct 2026)
