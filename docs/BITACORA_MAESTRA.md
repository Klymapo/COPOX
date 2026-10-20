# BITÁCORA MAESTRA · ALTH-META / COPOX

**Del primer bloque de Blender (26 sep 2026) al 19 oct 2026.** La escribió Elio el 19 oct 2026, por pedido de Admin.

**Fuentes:**
- Historia completa del repo Klymapo/COPOX: 977 commits en todas las ramas.
- `copox-modelos`, con sus archivos ULTIMA.txt y SHA256SUMS.
- Rama `capturas`.
- Drive de Gaston: la Memoria maestra integral (`1SYG_u3f…`), Bitácoras 001–003, el Reporte completo del 13 oct, las bitácoras de shrinkwrap y maniquí, y la carpeta INVESTIGACIONES.

Las lecciones están en `docs/LECCIONES.md`. Si un dato no aparece en las fuentes, se marca como «sin fuente».

---

## 0. Estado vigente (19 oct 2026, noche)

| Qué | Archivo | SHA-256 | Estado |
|---|---|---|---|
| **Cuerpo base** | `copox-modelos/adan/ADAN_BASE_CONGELADA.glb` (= ADAN_V50_1) | `0422ae54…4f43` | **CONGELADO por Admin**. Todo personaje nuevo parte de aquí. |
| Última versión de Adán aprobada completa | ADAN_V30 | `98454d28…d29a` | Aprobada el 18 oct a las 09:28 |
| Aprobadas «de momento» | ADAN_V48_3 (pelo PeloOrilla) · ADAN_V49_PELO_THEO (pelo de Theo, arco v2) | `14595da2…` · `baf56aca…` | Aprobadas de momento |
| Theo vestido vigente | `copox-modelos/theo/THEO_VESTIDO_V4_1.glb` | `74fc6240…` | **Variante B elegida, sin aprobación final.** CHXP V3 da FAIL 16/2 |
| Theo protegido | `assets/joven_rubio/theo_alpha.glb` | `ed2b04ec…580b` | Intocable (CLAUDE.md) |
| Maestro histórico de Adán | ADAN_FINAL_BASE_V04_SHORT_AZUL | `a1936eb…` | Inmutable (15 oct) |
| Herramientas | CHXP V3 (`python -m copox.render.chxp3`), SENKU (`copox/medicion/senku_ref.py`), Godot 4.7.2 | — | Vigentes |
| Código | Rama `propuesta/pruebas-movimiento` (PR #54, sin fusionar) | — | `main` sigue en `334b132` (14 oct) |

**Pendiente con Alastor:** Admin decidió esperar.

---

## 1. Cronología

### Fase 1 · Primeros bloques y estilo (26 sep – 1 oct)

- **26 sep, el primer bloque.**
  - Commits: `ac3eb8e`, `ac231fc`.
  - Contenido: andamiaje del repo, spec ALTH (`spec/alth_spec.json`), librería `alth/` e instalador de Blender como módulo de Python.
- **26 sep, primeros assets aprobados.**
  - Objetos: manzana v6, lata v5, taza, vaso y vaso de café.
  - Técnica: `alth/` + calcomanías.
  - Ese mismo día: verificación automática y comando `/asset` (`6b9f2fd`).
  - Escala v1.0 congelada con foto de familia y maniquí de escala (`10cfcd0`).
- **27 sep.**
  - joven_rubio (Theo), vueltas 4–6, con `alth/pelo.py` (casco + cuñas).
  - `tools/bucle.py`: bucle de comparación de silueta (IoU) con IA gratis o copiar/pegar.
  - CHSP-X (antes «El Taller»).
- **28 sep:** pruebas con SAM 3D (11 reconstrucciones) y Teacher3D local, como referencia.
- **30 sep.**
  - COPOX Loop Engine (PR #7): cassettes, unanimidad de auditores, scheduler.
  - **Theo Alpha** (SAM3D, `ed2b04ec…`) queda como baseline protegido.
- **30 sep – 1 oct.**
  - Madurez M0–M5 y campañas de dedos por micro-valles: 0/3 aceptados, MESH_INTEGRITY_FAILED.
  - Research gate.
  - Línea única T0–T6.
  - Spec v2 (s0 = 0.05316).
  - Kaggle TripoSG.

### Fase 2 · Laboratorio GLB sin Blender (8 oct)

- Tres entregas el mismo día:
  - **Bitácora 001:** `cubo.glb` de 12 triángulos, generado con Python puro y con capturas.
  - **Bitácora 002:** 14 vóxeles de 3 colores, quitando las caras internas.
  - **Bitácora 003:** casa voxel 2D de 16×17.
- Commit `a830469`.
- Lección: se puede fabricar el GLB a mano, sin depender de Blender.
- 9 oct: Admin pide apagar el scheduler. Desde entonces solo corre en manual.

### Fase 3 · Rescate y orden (12–13 oct)

- Auditoría de 54 ramas.
- Se respaldan 43 GLB y se recupera el rig v3.3. La gabardina sentada **no está aprobada**.
- Reporte completo del 13 oct: 5 objetos aprobados, personajes completos sin salir y dedos en PLATEAU.

### Fase 4 · Alastor Delta, maniquí y la era G2 (14–15 oct)

- **Alastor Delta.**
  - Rig Beta (56 huesos, 29 clips) más malla Gamma (Hunyuan3D).
  - Shrinkwrap por zonas, con máximo de 95 % en la vista 3/4.
  - Luego trasplante de cabeza, faldones y zapatos, con el cuello en 0.55.
  - IoU medio 97.8 %.
  - Las Notas para Argos lo dan por aprobado; el plan v2 lo trata solo como referencia (ver §3).
- **Maniquí.**
  - v0.2: loft sobre huesos.
  - v0.3 r1–r3: PLATEAU. Aun así se fusionó a `main` con el PR #34.
  - v0.4: nuca y patillas.
  - v0.7→v0.26: cabeza de superelipse, 30 posturas, 30 manos y 18 morphs. En la v0.16 Admin rechazó la cara: «no se parece nada».
- **G2-C1 a G2-C22.**
  - Nuca, limpieza facial, nariz, likeness, piel y transferencia de rig.
  - **Todo sin aprobar. Más de 20 rondas acabaron en PLATEAU.**
  - Causa de fondo: se parchaban mallas heredadas, sin piel debajo, con aristas abiertas y morphs vacíos.
- **Modelos Épsilon:** rig de v0.26 sobre G2-C22. Épsilon híbrido v01–v04 (Argos): superficie soldada, orejas simétricas y boca con cavidad.
- **15 oct, nace Adán.** Admin declara final a Épsilon v04: `ADAN_FINAL_BASE_V04_SHORT_AZUL` (`a1936eb…`), inmutable.

### Fase 5 · Adán como base, SENKU y CHXP (16–17 oct)

- **16 oct.**
  - Skills de anatomía, rig y vestuario (v0.1→v1.0).
  - Pruebas P01–P03.
  - La corrección de hombros se descartó porque arreglaba 2 clips y rompía 6.
  - Adán P04 (Godot 4.5.1) detenido por Admin.
- **17 oct.**
  - **Plan de diseño v2**: Adán es la base universal y se usa Godot 4.7.x.
  - Medición v2, que después se llamó **SENKU** (unidad ED, cámara imitada).
  - **CHXP v1** (render NumPy).
  - Adán V05–V21 y Theo V01–V14: rostro, ojos, cejas en bloque y nariz cúbica.
  - Hitos: **ADÁN ALPHA = V21** (`bf6ec140…`) y Theo V14 (`6dcf8acd…`), entonces llamado «Theo Alpha»; desde el 19 oct se llama **THEO_ROSTRO_V14**.
  - **Decisión:** mandan las referencias renderizadas; el PDF de 95 mm queda como histórico.
  - **Adán V22 HABLA:** 8 visemas, Talk/Blink y shader de mirada. Es el inicio de la cadena de recetas.
  - Drive ordenado: carpetas EXPERIMENTOS G2 y SKILLS creadas, 80 carpetas renombradas a MAYÚSCULAS.

### Fase 6 · El cuerpo pieza por pieza (18 oct)

- **Mañana.**
  - Repo privado `copox-modelos`.
  - V23 párpados, V24 sin LOD de Godot, V25 boca, dientes, lengua y orejas medidas con SENKU.
  - La tarea nocturna perdió **7 de 7 corridas** porque no tenía acceso a `copox-modelos`.
- **V26–V29:** repesado por cadena; clips Walk, Run, Jump y Punch con IK por código; boca plana.
- **V30 APROBADA** (09:28): se quitó el escalón de la quijada (relleno biarmónico) y CHXP pasó a `luz=juego`.
- **V31–V45**, rediseño del cuerpo:
  - V31 brazos y V32 manos.
  - **V33 cabeza afilada: APROBADA.**
  - V34–V38 manos implícitas, agarre y antebrazo; meshoptimizer vía Godot.
  - V39 proporciones; V40 manos de bloques intercambiables («así van»).
  - V41 short de una pieza (`short_geo`); V42 piernas y pies de bloques.
  - V43 cadera; V44 manos; V45 «liso y plano».

### Fase 7 · Cabeza, pelo y CHXP con Godot (19 oct, mañana)

- Auditoría de V45 con visual-critic: veredicto UNA_CORRECCIÓN.
- V46–V47: pie por secciones (loft) y mano al 85 %.
- V48 cabeza caja: **NO APROBADA**. V48.1 descartada. V48.2: **NO APROBADA**.
- **V48.3: pelo implícito Fibonacci + PeloOrilla. APROBADA DE MOMENTO** (11:14).
- V49: pelvis, cuero cabelludo, tenis y pelos intercambiables (KHR_node_visibility).
- **CHXP V2:** render con Godot real por lotes. También fabricación rápida con `ALTH_CALIDAD=borrador`.
- **Pelo de Theo:** cuñas (PLATEAU) → bloques → resortes (SpringBoneSimulator3D) → arco SENKU v1/v2, con IoU de 0.79 a 0.93. **ADAN_V49_PELO_THEO aprobada de momento.**

### Fase 8 · Auditoría con veto, pelvis, zapato y ropa (19 oct, tarde y noche)

- **CHXP V3:** auditoría con veto, inventario de 25 skills y 188 reglas, topes de 160k/60k triángulos y `rubio_miel #DFBA86`.
- Skill `investigar-referencias` y briefs de pelvis, ropa por capas y zapato.
- Theo vestido V1 (ropa ajustada): **NO APROBADO**, se veía pintado.
- **Adán V50:** pelvis anatómica (la V inguinal, tomada del boceto de Admin) y zapato de Theo. A Admin le gustaron cadera y zapatos.
- **Theo vestido V2:** por capas (vóxeles), CHXP FAIL 16/1.
- **Theo vestido V3:** técnica del short (`ropa_tubos`), FAIL 15/2.
- **Adán V50_1 + Theo vestido V4:**
  - Zapato 10 % menor, con empeine, suela visible y tacón separado.
  - Ropa más holgada; camisa con textura sutil; corbata con volumen.
  - FAIL 16/1.
- **Theo vestido V4_1:**
  - El chaleco cubre el hombro, con el tirante medido desde la articulación.
  - Gate nuevo `hombro_cubierto`.
  - PLATEAU. Admin elige la **variante B**.
- **Adán V50_1 queda congelado como `ADAN_BASE_CONGELADA.glb`.**

---

## 2. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Código, recetas y briefs | GitHub `Klymapo/COPOX`, rama `propuesta/pruebas-movimiento`: `docs/medicion/`, `copox/`, `docs/investigacion/` |
| Fichas por versión | `docs/ADAN_ALPHA.md`, `docs/ADAN_V23.md`…`ADAN_V49.md` |
| GLB (privado) | `Klymapo/copox-modelos`: `adan/`, `theo/`, con ULTIMA.txt y SHA256SUMS |
| Capturas | Rama `capturas`, en `capturas/AAAA-MM-DD/<asset>/` |
| Registro de cambios | Drive: «01 — COPOX · Memoria maestra integral» (`1SYG_u3faWWcYKXSAzUePnOwQAApLmrAVpDwXtWE_K28`) |
| Investigaciones del 16–17 oct | Drive: carpeta INVESTIGACIONES (`1OsV2sjHuQdp5vwAHD2DHvo_ojWeQgM_l`) |
| Skills | Drive: carpeta SKILLS (`1xPDsHWVpVqv0yNRBL8_-lt_WWPkhAvAQ`); repo `.claude/skills/` |
| Bitácoras 001–003 | Drive: `1PvQkq4g5cWAyz2LxTkwAQVVGxoejHH5x` |
| Shrinkwrap / maniquí | Drive: `1r2LWCyNPfv_W5Hs2I-VVCweuY1wTgPJF` |

**Huecos de documentación** (sin ficha propia; solo están en commits, en ULTIMA.txt y en esta bitácora):
- ADAN_V50 y V50_1.
- Theo vestido V1–V4_1.
- Pelo de Theo.
- Adán V01–V04: solo aparece el maestro V04.

---

## 3. Contradicciones detectadas (sin resolver; las decide Admin)

1. ~~Dos «Theo Alpha»~~ **Resuelto (19 oct):** el protegido `ed2b04ec…` conserva el nombre; la V14 `6dcf8acd…` pasa a THEO_ROSTRO_V14.
2. ~~Escala~~ **Resuelto (19 oct):** CLAUDE.md documenta la convención vigente (metros, Y arriba, frente +Z, Adán como medida base); mm/Z-arriba, 0.0559 y el PDF de 95 mm quedan como históricos.
3. **Topes de triángulos:** el reporte del 13 oct dice 6k/40k; el spec del 19 oct dice 160k/60k (este último es el vigente).
4. ~~Ramas `copox/state/*`~~ **Resuelto (19 oct):** se quita la mención de CLAUDE.md; el estado vive en `copox-modelos`.
5. **PR #34** (maniquí v0.3, PLATEAU) se fusionó a `main`, en contra de la regla de no fusionar sin aprobación.
6. **Alastor Delta:** «aprobado como base» según las Notas para Argos; «solo referencia» según el plan v2.
7. **Theo:** el 18 oct se escribió «quedó como prueba y ya no se usa», pero el 19 oct se trabajó en él.
8. **Hash de Adán V25:** `cf0e60d5…` es erróneo; el válido es `b36c73dd…`.
9. **Docs desactualizados:**
   - Obsoletos: `GUIA_RAPIDA`, `NAMING`, `STRUCTURE`, `CHSP-X`, la skill `finalizar-personaje` (usa `bucle.py`) y el MANIFIESTO de Drive (cita carpetas que no existen).
   - Godot: P04 se probó en 4.5.1; la versión vigente es 4.7.x.

---

## 4. Registro de esta bitácora

- 19 oct 2026: creación (Elio). Fuentes cotejadas: commits de todas las ramas, `copox-modelos` y la Memoria maestra.
