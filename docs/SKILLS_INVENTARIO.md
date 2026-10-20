# Inventario de skills ALTH-META / COPOX para gates CHXP

Generado el 2026-10-19, en modo de solo lectura (Drive y GitHub sin cambios). El JSON equivalente está en `copox/render/skills_reglas.json`.

## Fuentes revisadas

- **Drive** (Drive SKILLS (1xPDsHWVpVqv0yNRBL8_-lt_WWPkhAvAQ)): 3 Google Docs (VESTUARIO Y CABELLO, MOVIMIENTO Y RIG, ANATOMIA 3D) y 3 zips (`alth-meta-vestuario-cabello`, `alth-meta-rig-motion-design`, `alth-anatomia-estilizada`). Cada Doc es la investigación de la que sale su zip, así que se fusionan en una sola skill.
- **GitHub** (Klymapo/COPOX, 68 ramas remotas): `.claude/skills`, `.codex/skills`, `.claude/agents`, `.claude/commands`. Las copias `.claude` y `.codex` son byte a byte iguales. Si había varias versiones de una skill, se usó la más grande; en todos los casos las versiones menores eran subconjuntos (comprobado con `comm`).
- **Repo actual** (`propuesta/pruebas-movimiento`): `finalizar-personaje`, `revisar-alth`, `/asset` y el agente `revisor-visual-alth`. Son idénticos a sus versiones en origin.
- `revisar-alth` (skill) y `revisor-visual-alth` (agente) tienen el mismo contenido, así que aquí cuentan como una sola entrada.

**Totales:** 25 skills, 188 reglas: **155 medibles** y **33 checklist**.

Convenciones: *medible* significa que se puede comprobar con código sobre el GLB o sobre renders/máscaras. *checklist* significa que requiere juicio visual humano. «a definir» indica que la fuente no fija un número. Los umbrales con número citan el texto original; varios están marcados en la fuente como «propuesto / no medido».

## Resumen por skill

| Skill | Fuente(s) | Propósito | Medibles | Checklist |
|---|---|---|---|---|
| `alth-meta-vestuario-cabello` | Drive Doc «COPOX - SKILL VESTUARIO Y CABELLO - ADAN» (`1xSfPGebjS…`, v0.1-v0.3 research (R1-R3))<br>Drive zip «alth-meta-vestuario-cabello.zip» (`1BZXLAHeL_…`, 1.0.0-beta) | Planear ropa, cabello estilizado y física secundaria exportable a GLB como módulos separados, sin tocar el personaje base aprobado. | 21 | 4 |
| `alth-meta-rig-motion-design` | Drive Doc «COPOX - SKILL MOVIMIENTO Y RIG - ADAN» (`1U8TDY8MUj…`, v1.0-research (R1-R4))<br>Drive zip «alth-meta-rig-motion-design.zip» (`1LfUvcJ1Cl…`, 1.0.0-beta) | Diseñar y auditar rig corporal, manos de cinco dedos, rostro L/R y locomoción exportables a GLB sin alterar el original. | 16 | 2 |
| `alth-anatomia-estilizada` | Drive Doc «COPOX - SKILL ANATOMIA 3D - ADAN» (`14vYO8z793…`, v1.0-research (R1-R4))<br>Drive zip «alth-anatomia-estilizada.zip» (`1aQ8I5gWng…`, 1.0.0-beta) | Diagnosticar y planear correcciones anatómicas locales (manos, pies, rostro, párpados, orejas, cuello) sin sustituir el GLB aprobado. | 12 | 3 |
| `asset` | GitHub `.claude/commands/asset.md` — 64 ramas: assets/theo-v10, avatares-chibi, bucle/joven_rubio-11 … (+61)<br>Repo local `/home/claude/alth-meta/.claude/commands/asset.md` (versión 9978310 (60 ramas); variante d71b3aa en 4 ramas claude/* sin alturas_ancla) | Crear un asset ALTH-META completo (spec, build, renders, verificación, GLB) con ciclo de vueltas topado. | 7 | 2 |
| `revisar-alth` | GitHub `.codex/skills/revisar-alth/SKILL.md` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)<br>GitHub `.claude/agents/revisor-visual-alth.md` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)<br>Repo local `/home/claude/alth-meta/.codex/skills/revisar-alth/SKILL.md y .claude/agents/revisor-visual-alth.md` (mismo contenido; deduplicados) | Revisión de solo lectura de una hoja de 4 vistas con veredicto APROBABLE / UNA_CORRECCIÓN / REHACER. | 2 | 3 |
| `finalizar-personaje` | GitHub `.claude/skills/finalizar-personaje/SKILL.md (= .codex)` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)<br>Repo local `/home/claude/alth-meta/.claude/skills/finalizar-personaje/SKILL.md` | Cerrar un personaje con una ronda integral, pruebas deterministas, evidencia y parada para aprobación humana. | 2 | 1 |
| `copox-auditoria-3d` | GitHub `.claude/skills/copox-auditoria-3d/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Auditoría por niveles de costo de GLB COPOX: filtro barato, preflight gate, 4 vistas y pruebas profundas solo en finalistas. | 11 | 1 |
| `copox-geometria` | GitHub `.claude/skills/copox-geometria/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Construir/reparar superficies por ajuste elipsoidal, bucles de borde y puentes de contorno, sin IA generativa. | 4 | 0 |
| `copox-procedencia-3d` | GitHub `.claude/skills/copox-procedencia-3d/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Revisar origen, licencias y trazabilidad de GLB, texturas y referencias antes de afirmar independencia comercial. | 0 | 3 |
| `anatomic-cut` | GitHub `.claude/skills/anatomic-cut/SKILL.md (= .codex; versión e7506de más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Recortar geometría defectuosa por regiones anatómicas sin perder facciones, normales, UV ni pesos. | 5 | 1 |
| `contour-extractor` | GitHub `.claude/skills/contour-extractor/SKILL.md (= .codex; versión a6046da más completa)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7) | Extraer y validar bucles topológicos de borde reales antes de coser, cortar o hacer loft. | 4 | 1 |
| `surface-stitch` | GitHub `.claude/skills/surface-stitch/SKILL.md (= .codex; versión 356f53d más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Unir dos superficies con bordes abiertos compatibles en una sola topología conservando atributos. | 6 | 0 |
| `stitch-advancing-front` | GitHub `.claude/skills/stitch-advancing-front/SKILL.md (= .codex)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7) | Triangulación de frente de avance entre dos bucles reales de longitud diferente, con validación y rechazo de exportaciones inseguras. | 6 | 0 |
| `scully` | GitHub `.claude/skills/scully/SKILL.md (= .codex; versión 0e4559f más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12) | Esculpir matemáticamente regiones sanas (aplanar frente, redondear nuca) con ROI, falloff y presupuesto de desplazamiento. | 4 | 1 |
| `gltf-rig-guardian` | GitHub `.claude/skills/gltf-rig-guardian/SKILL.md (= .codex; versión 0446cf0 más completa)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7) | Auditar preservación de glTF: skeleton, atributos, materiales, UV, morphs y canales animados; gates de import Godot. | 9 | 0 |
| `rig-architect` | GitHub `.claude/skills/rig-architect/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Diseñar y validar esqueletos, bind poses, pesos y límites articulares preservando animaciones. | 7 | 1 |
| `motion-lab` | GitHub `.claude/skills/motion-lab/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Crear y corregir animaciones con biomecánica, contactos, trayectoria y timing contra referencias de vídeo/pose. | 7 | 1 |
| `facial-acting` | GitHub `.claude/skills/facial-acting/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Gestualidad facial (parpadeo, mirada, mandíbula, labios, visemas) validada contra todas las referencias faciales. | 5 | 1 |
| `cloth-dynamics` | GitHub `.claude/skills/cloth-dynamics/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Movimiento de tela (gabardinas, faldones) con colisiones al caminar/sentarse y comparación contra referencias. | 5 | 2 |
| `visual-critic` | GitHub `.claude/skills/visual-critic/SKILL.md (= .codex; versión be20d55 más completa)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Comparación cruzada obligatoria contra TODAS las referencias/vistas/poses, sin promedios que oculten discrepancias. | 6 | 3 |
| `regional-cassettes` | GitHub `.claude/skills/regional-cassettes/SKILL.md (= .codex)` — 8 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+5) | Evaluar y versionar por región (nuca, ojos, manos, ropa...) sin vetos globales por fallos ajenos ni daños a datos compartidos. | 4 | 1 |
| `regional-asset-qa` | GitHub `.claude/skills/regional-asset-qa/SKILL.md (= .codex)` — 1 ramas: experimentos/maniqui-g2c2-contorno-facial | Orquestar QA por regiones independientes con auditor de seguridad global obligatorio. | 2 | 1 |
| `regional-model-auditor` | GitHub `.claude/skills/regional-model-auditor/SKILL.md (= .codex)` — 1 ramas: experimentos/maniqui-g2c2-contorno-facial | RegionVerdict por ROI; defecto nuevo en vecino → BLOCKED_INTEGRATION del candidato responsable. | 3 | 0 |
| `geometry-profiler` | GitHub `.claude/skills/geometry-profiler/SKILL.md (= .codex)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7) | Perfilado determinista del motor geométrico; optimización nunca equivale a aprobación. | 2 | 0 |
| `scene-director` | GitHub `.claude/skills/scene-director/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11) | Escenas Godot: iluminación, cámaras, composición, props y navegación contrastadas con referencias de encuadre. | 5 | 1 |

## `alth-meta-vestuario-cabello`: alth-meta-vestuario-cabello (VESTUARIO Y CABELLO)

**Propósito:** Planear ropa, cabello estilizado y física secundaria exportable a GLB como módulos separados, sin tocar el personaje base aprobado.

**Fuentes:**
- Drive Doc «COPOX - SKILL VESTUARIO Y CABELLO - ADAN» (`1xSfPGebjS…`, v0.1-v0.3 research (R1-R3))
- Drive zip «alth-meta-vestuario-cabello.zip» (`1BZXLAHeL_…`, 1.0.0-beta)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `vestuario.base_inmutable` | El GLB base (Adán v04) no se modifica: prenda/peinado se construye como módulo hijo separado. | medible | personaje, ropa, pelo, calzado | SHA-256 del GLB base == aprobado; POSITION/índices de la malla base idénticos byte a byte en el candidato | igualdad exacta (SHA a1936eb9...2ac14) | "No tocar Adán aprobado: fabricar vestuario como asset hijo/accesorio separado" (doc §6) |
| `vestuario.rig_base_preservado` | Preservar 56 huesos / 18 morphs / 112 clips del base salvo aprobación de ampliación. | medible | ropa, pelo, calzado, personaje | conteo joints de skin, targets por malla, nº animaciones vs base | joints=56, morphs cuerpo=18 (Face=16), clips=112; sin pérdidas | "Preservar 56 huesos / 18 morphs / 112 clips del Adán de referencia salvo aprobación explícita" (doc §6) |
| `vestuario.paleta` | Colores de prendas/pelo solo de la paleta ALTH (spec/alth_spec.json). | medible | ropa, pelo, calzado | baseColor de cada material ∈ spec.paleta | 100 % de materiales en paleta | "Mantener paleta y medidas de spec/alth_spec.json" (doc §1) |
| `vestuario.material_mate` | Material mate PBR simple, roughness alta, normales suaves. | medible | ropa, pelo, calzado | roughnessFactor de cada material de prenda | a definir (texto: 'roughness alta') | "usar material mate PBR simple, roughness alta, normales suaves" (doc §3d) |
| `vestuario.sin_clipping_poses_extremas` | Sin penetración prenda-cuerpo en poses extremas, no solo en T-pose. | medible | ropa, calzado, animacion | distancia firmada mínima prenda→cuerpo/proxy en poses extremas y clips (vértices dentro del cuerpo) | a definir (texto: márgenes 'pequeños pero positivos') | "Resolver clipping en el espacio de las poses extremas, no solo en T-pose" (doc §3e); "deformaciones extremas sin clipping" (§7) |
| `vestuario.sin_interseccion_inicial` | La prenda no empieza intersectando el cuerpo/proxies en pose de reposo. | medible | ropa, calzado | nº de vértices de prenda dentro del cuerpo en rest pose | 0 | "Evitar comenzar con intersecciones" (doc §13.4) |
| `vestuario.proxy_colision_separado` | Proxy de colisión distinto de la malla render, de bajo poligonaje. | medible | ropa, pelo | existe malla/nodo proxy separado; tris(proxy) < tris(render) | a definir | "Proxy de colisión distinto de malla render ... bajo número de polígonos" (doc §13.4) |
| `vestuario.pesos_normalizados` | Pesos transferidos a la prenda normalizados por vértice. | medible | ropa, pelo, calzado | \|Σ WEIGHTS_0 − 1\| por vértice | a definir (tolerancia numérica) | "transferencia espacial de pesos ... y NORMALIZAR por vértice" (doc §13.2) |
| `vestuario.solo_datos_gltf` | Exportar solo datos glTF: meshes, bones, morphs, clips TRS/weights, PBR; nada que dependa de Cloth vivo. | medible | ropa, pelo, animacion | rutas de canal ∈ {translation, rotation, scale, weights}; sin extensiones no estándar requeridas | 100 % | "Exportar solo datos soportados por glTF (meshes, bones, morphs, clips, PBR)" (doc §7.6) |
| `vestuario.normales_no_invertidas` | Sin normales invertidas en la prenda. | medible | ropa, pelo, calzado | fracción de caras con winding/normal inconsistente | 0 | "ausencia de inversión de normales" (doc §13 VALIDACIONES FUTURAS) |
| `vestuario.cierre_manifold` | Malla manifold donde se espera cierre; bordes libres solo en aperturas (cuello, sisa, puños, dobladillo). | medible | ropa, calzado | aristas non-manifold; bucles de borde fuera de aperturas declaradas | 0 / 0 | "malla no manifold donde se espera cierre"; aperturas "cuello, sisa, cintura, puños, dobladillos" (doc §13, §3a) |
| `vestuario.triangulos_no_alargados` | Evitar triángulos alargados (falda/paneles). | medible | ropa | aspect ratio máximo por triángulo | a definir | "evitar triángulos alargados y solapes iniciales" (doc §12 Falda) |
| `vestuario.entrepierna_sin_polo` | Pantalón: no concentrar todas las costuras en un único vértice de entrepierna. | medible | ropa | valencia máxima de vértice en región entrepierna | a definir | "evitar un único vértice concentrando todas las costuras en la entrepierna" (doc §12) |
| `vestuario.silueta_4_vistas` | Silueta de la prenda fiel a la referencia en frente, lateral, espalda y 3/4. | medible | ropa, pelo, calzado | IoU de máscara por vista vs referencia | a definir | "silhouette 4 vistas" (doc §7.7); "Validar silueta en cuatro vistas" (zip SKILL.md) |
| `vestuario.presupuesto` | Respetar presupuesto de triángulos y de huesos secundarios. | medible | ropa, pelo | tris y nº huesos añadidos | a definir (zip: 'presupuesto quedan por medir') | "presupuesto de triángulos/rig" (doc §7.7) |
| `vestuario.capa_sentada_sin_atravesar` | Capa al sentarse se despliega sobre el asiento sin atravesarlo. | medible | ropa, animacion | penetración tela↔asiento/respaldo/muslos por frame del clip Sit | a definir | "la tela debe desplegarse sobre asiento y conservar pliegues sin atravesarlo" (doc §4) |
| `cabello.raices_ancladas` | Raíces de mechones soldadas/ocultas en la guía capilar; raíces estables al moverse. | medible | pelo | distancia raíz→cuero cabelludo; desplazamiento de raíz durante clips | a definir | "raíces soldadas/ocultas en guía capilar" (doc §5); "estabilidad de raíces" (R3) |
| `cabello.segmentos_por_mechon` | Mechones Theo: 1–3 segmentos deformables; rizos Alastor: 1–2 huesos secundarios por grupo. | medible | pelo | longitud de cadena de huesos secundarios por mechón/grupo | Theo 1–3; Alastor 1–2 (orientativo, 'NO validadas') | "1–3 segmentos deformables por mechón" (doc §5); "1-2 huesos secundarios por grupo, cifras orientativas NO validadas" (R3) |
| `cabello.sin_atravesar_cara` | En sacudida/viento el pelo no atraviesa cara, ojos, orejas ni hombros. | medible | pelo, animacion | nº de intersecciones pelo↔cara/ojos/orejas/hombros por frame | 0 | "comprobar que no atraviese cara, ojos, hombros" (doc §5) |
| `cabello.sin_bolas_sueltas` | Rizos como masas continuas: sin esferas/bolitas sueltas. | medible | pelo | componentes conexos flotantes (no unidos a la masa ni al cráneo) | 0 | "evitar partículas finas y malla de esferas sueltas" (doc §5); "evitar bolitas separadas" (R3) |
| `cabello.sin_escalado_esqueleto` | Cadenas de pelo sin escalado de esqueleto (SpringBone). | medible | pelo | escala de huesos secundarios en rest y canales scale | 1.0 | "evitar escalado del esqueleto" (R3, SpringBoneSimulator3D) |
| `vestuario.estilo_chibi_soft` | Lectura chibi-soft: masas amplias, bloques de color, sin realismo fotográfico ni hebras. | checklist | ropa, pelo, calzado | revisión visual | - | "NO imponer realismo fotográfico ni simular miles de hebras" (doc §1) |
| `vestuario.no_aumentar_volumen` | No aumentar el volumen corporal del personaje sin autorización. | checklist | ropa | revisión visual (apoyo: bbox de cuerpo base sin cambio) | - | "No aumentar volumen corporal sin autorización" (doc §3d) |
| `vestuario.densidad_flexion` | Densidad de malla suficiente en axila, codo, rodilla, falda y capa. | checklist | ropa | revisión de topología | - | "densidad suficiente donde doblan (axila, codo, rodilla, falda, capa)" (doc §3b) |
| `vestuario.no_validado_sin_evidencia` | Sin pruebas reales el estado es NO VALIDADO / NO PROBADO. | checklist | ropa, pelo | estado del reporte | - | "Si no hay evidencia, estado NO VALIDADO" (doc §7.7) |

## `alth-meta-rig-motion-design`: alth-meta-rig-motion-design (MOVIMIENTO Y RIG)

**Propósito:** Diseñar y auditar rig corporal, manos de cinco dedos, rostro L/R y locomoción exportables a GLB sin alterar el original.

**Fuentes:**
- Drive Doc «COPOX - SKILL MOVIMIENTO Y RIG - ADAN» (`1U8TDY8MUj…`, v1.0-research (R1-R4))
- Drive zip «alth-meta-rig-motion-design.zip» (`1LfUvcJ1Cl…`, 1.0.0-beta)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `rig.sha_base` | Verificar SHA del GLB aprobado antes de cualquier mutación; el original nunca se reescribe. | medible | personaje, animacion | SHA-256 | == a1936eb9...2ac14 (Adán) | "Pedir/encontrar GLB aprobado real y verificar SHA antes de cualquier mutación" (zip paso 1) |
| `rig.sin_perdida_clips_targets` | 0 pérdida de clips o morph targets respecto del base. | medible | personaje, animacion | nº clips y nombres; nº targets por malla y nombres | 0 pérdidas (base: 112 clips; 18 cuerpo; 16 Face) | "QA propuesto, NO medido: 0 pérdida de clips o targets" (doc R4) |
| `rig.matrices_finitas` | Matrices (nodos, inverseBindMatrices) finitas. | medible | personaje, animacion | NaN/Inf en matrices y TRS | 0 | "matrices finitas" (doc R4 QA; §3 Capa 5) |
| `rig.pesos_normalizados` | Pesos de piel normalizados y sin vértices sin influencia. | medible | personaje, ropa | \|Σw−1\| por vértice; vértices con Σw=0 | a definir / 0 | "pesos normalizados y sin vértices sin influencia" (doc §2C) |
| `rig.cinco_dedos` | Cinco dedos independientes por mano, cada uno con 3 segmentos (pulgar CMC/MCP/IP; resto MCP/PIP/DIP). | medible | personaje | joints de dedo por mano (nombres + jerarquía) | 15 por mano (30 total; auditoría Adán) | "CINCO dedos independientes por mano" (doc R4); "estructura de 30 joints de dedos" (zip auditoria-adan-real.md) |
| `rig.morph_topologia_estable` | No alterar orden de vértices ni índices/nombres de morph targets del aprobado. | medible | personaje | nº vértices por primitiva, nº/orden/nombres de targets vs base | igualdad exacta | "No alterar orden de vértices ni targets del modelo aprobado" (doc R3) |
| `rig.morph_consistencia` | Mismo nº de targets en todas las primitivas de una malla; mesh.weights coincide. | medible | personaje | targets por primitiva; len(mesh.weights) | consistente | glb_audit.py: "cuenta inconsistente de morph targets" / "weights no coincide con targets" (zip anatomía, citado por skill rig) |
| `rig.canales_exportables` | Animación exportada solo como TRS y morph weights horneados (sin IK/drivers vivos). | medible | animacion | rutas de canal ∈ {translation, rotation, scale, weights} | 100 % | "Exportar solo TRS y morphs horneados" (doc R2) |
| `rig.jerarquia_retarget` | Retarget: nombre, padre, rest matrix, orientación y longitud verificados hueso por hueso. | medible | personaje, animacion | diff nombre/padre/rest por joint vs perfil/base | 0 diferencias no autorizadas | "Retargeting exige verificar nombre, padre, rest matrix, orientación local y longitud relativa" (doc R4) |
| `rig.facial_LR` | Controles faciales independientes izquierda/derecha (blink, squint, cheek, brow, mirada). | medible | personaje | pares _L/_R (o Left/Right) en morphs/huesos faciales | a definir (cobertura; canales propuestos, 'NO asumir presentes') | "facial independiente izquierda/derecha" (doc §3 criterio) |
| `rig.mezcla_sin_sobrescritura` | Combinar expresiones sin sobrescribir weights ni sumar desplazamientos excesivos. | medible | animacion, personaje | clips que escriben los mismos índices de weights; desplazamiento máx. combinado por región | a definir | "mezcla simultánea sin sobrescritura de weights" (zip P3); "límites por región" (doc R3) |
| `rig.foot_sliding` | Pie de apoyo sin deslizar. | medible | animacion | desplazamiento del pie en fase de apoyo / longitud del pie | < 2 % (propuesto, sujeto a calibración) | "desplazamiento de pie en apoyo inferior al 2% de longitud del pie" (doc R4 QA) |
| `rig.contacto_agarre` | Agarre: punta de dedo en su punto de contacto. | medible | animacion, personaje | distancia punta→contacto / ancho de palma | < 5 % (umbral preliminar de diseño) | "distancia punta-contacto inferior al 5 % del ancho de palma" (doc R3/R4) |
| `rig.sin_penetraciones_graves` | Poses extremas, gestos y manos entrelazadas sin autointersecciones importantes. | medible | animacion, personaje | pares de triángulos intersectados en poses/frames | a definir | "poses extremas sin autointersecciones importantes" (doc §3) |
| `rig.continuidad_velocidad` | Sin discontinuidades de velocidad ni teleport del centro de masa entre fases/transiciones. | medible | animacion | salto de velocidad angular/lineal entre frames y en bordes de transición | a definir | "Evitar deslizamiento de pies, discontinuidades de velocidad" (doc R3); "no teleportar el centro de masa" (R4) |
| `rig.root_motion_declarado` | Root motion vs in-place decidido explícitamente por clip. | medible | animacion | canal translation del root presente/ausente == declaración del manifest | coincidencia | "decidir root motion vs in-place explícitamente" (zip paso 6) |
| `rig.sin_colapso_articulaciones` | Sin colapso de hombros, codos, rodillas, muñecas o comisuras; sin torsión severa. | checklist | personaje, animacion | revisión visual de poses (posible métrica: pérdida de volumen local) | - | "sin colapso de hombros, codos, rodillas, muñecas o comisuras" (doc §3) |
| `rig.expresiones_compuestas` | Guiño = blink unilateral + squint + cheekRaise; soplar, silbar, bizco, ojos en blanco legibles. | checklist | personaje, animacion | hoja de expresiones | - | "Guiño = blink unilateral + squint + cheekRaise del mismo lado" (doc R4) |

## `alth-anatomia-estilizada`: alth-anatomia-estilizada (ANATOMIA 3D)

**Propósito:** Diagnosticar y planear correcciones anatómicas locales (manos, pies, rostro, párpados, orejas, cuello) sin sustituir el GLB aprobado.

**Fuentes:**
- Drive Doc «COPOX - SKILL ANATOMIA 3D - ADAN» (`14vYO8z793…`, v1.0-research (R1-R4))
- Drive zip «alth-anatomia-estilizada.zip» (`1aQ8I5gWng…`, 1.0.0-beta)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `anat.glb_estructural` | GLB estructuralmente válido: cabecera, chunks, accessors/bufferViews en rango, skins sin joints repetidos. | medible | todos | glb_audit.py → structural_status | NO_STRUCTURAL_ISSUES_FOUND | scripts/glb_audit.py (zip) |
| `anat.sha_base` | Sin ID/hash inequívoco no se muta; original nunca se sobrescribe. | medible | personaje | SHA-256 vs esperado | igualdad | "Identificar baseline exacta. Sin ID/hash inequívoco no mutar" (doc skill v0.1) |
| `anat.fuera_de_mascara_identico` | Mismo contorno y geometría fuera del parche/máscara. | medible | personaje | desplazamiento máx. de vértices fuera de la máscara | 0 | "Aceptación: mismo contorno fuera del parche"; "Rechazar cambios fuera de máscara" (doc) |
| `anat.cinco_dedos_separados` | Cinco dedos separados por mano (y pie); dedos fusionados = rechazo. | medible | personaje | nº de dedos separables geométricamente por mano/pie (componentes al cortar a nivel MCP) | 5 | "cinco dedos separados, pulgar correcto"; RECHAZO: "dedos fusionados" (doc) |
| `anat.parpados_sin_interseccion` | Párpados no atraviesan el globo ocular, también con morph de cierre. | medible | personaje | intersecciones párpado↔globo en rest y con blink=1 | 0 | "párpados sin intersección"; "mirar también cierre + morph" (doc/zip) |
| `anat.ojos_no_flotantes` | Sin ojos flotantes ni huecos faciales. | medible | personaje | hueco globo↔cuenca; componentes flotantes en cabeza | a definir | "Evitar ojos flotantes, huecos faciales" (doc §3) |
| `anat.manifold_por_pieza` | Manifold auditado por pieza; aberturas intencionales y piezas separadas (ojos, pelo, accesorios) declaradas. | medible | personaje, objeto | aristas non-manifold y bordes abiertos no declarados por pieza | 0 | "Auditar manifold por pieza y distinguir ojos/accesorios separados intencionalmente" (doc R4) |
| `anat.topologia_limpia` | Sin caras internas, T-junctions, vértices aislados, normales invertidas ni autointersecciones. | medible | personaje, objeto | conteo de cada defecto | 0 | "Evitar poles en pliegues, T-junctions, caras internas, auto-intersecciones y normales invertidas" (doc §3) |
| `anat.preservar_uv_pesos_morphs` | Preservar UV, pesos, materiales y morphs; pérdida de rig/morphs = rechazo. | medible | personaje | presencia y conteo de TEXCOORD_0, JOINTS_0/WEIGHTS_0, targets vs base | sin pérdidas | RECHAZO: "pérdida de rig/morphs" (doc) |
| `anat.paleta` | Paleta sin cambios. | medible | personaje | baseColor de materiales vs base/spec | igualdad | RECHAZO: "paleta cambiada" (doc) |
| `anat.landmarks_altura_cabeza` | Landmarks (ojos, nariz, mandíbula, hombros, nudillos, pelvis, rodillas, pies) normalizados por altura de cabeza Hc. | medible | personaje | posición relativa landmark / Hc (mentón-coronilla sin pelo) | a definir (texto: 'sin tolerancias inventadas', calibrar con Adán) | "medir desde GLB base cabeza Hc ... No imponer proporciones de adulto ni tolerancias arbitrarias" (doc R2) |
| `anat.simetria_regional` | Simetría razonable por región, respetando asimetrías aprobadas. | medible | personaje | distancia espejo X por región | a definir | "simetría razonable" (doc v0.1); "Simetría regional, respetando asimetrías aprobadas" (R4) |
| `anat.membranas_U` | Membranas interdigitales curvas en U, no gruesas en V; palma no cuadrada. | checklist | personaje | revisión visual (posible métrica: perfil del valle interdigital) | - | "concavidad interdigital en U ... evitar membrana triangular en V, palma cuadrada" (doc R2) |
| `anat.cuello_no_cilindrico` | Cuello orgánico continuo con mandíbula/clavícula, no cilindro incrustado. | checklist | personaje | revisión visual | - | RECHAZO: "cuello cilíndrico" (doc) |
| `anat.silueta_multivista` | Contornos coherentes en frente, perfil, espalda y 3/4; revisión humana aprobada. | checklist | personaje | revisión visual | - | "contornos coherentes multivista; revisión visual humana aprobada" (doc) |

## `asset`: /asset (comando)

**Propósito:** Crear un asset ALTH-META completo (spec, build, renders, verificación, GLB) con ciclo de vueltas topado.

**Fuentes:**
- GitHub `.claude/commands/asset.md` — 64 ramas: assets/theo-v10, avatares-chibi, bucle/joven_rubio-11 … (+61)
- Repo local `/home/claude/alth-meta/.claude/commands/asset.md` (versión 9978310 (60 ramas); variante d71b3aa en 4 ramas claude/* sin alturas_ancla)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `asset.cotas` | Cada cota de spec.json (por pieza, ejes W=X, D=Y, H=Z) se cumple. | medible | objeto, edificio, personaje, ropa, calzado | \|medida_bbox − mm_spec\| / mm_spec por pieza y eje | ±2 % (o 'tolerancia' por cota) | "tolerancia ±2 %, o \"tolerancia\" por cota" (asset.md §3) |
| `asset.triangulos` | Triángulos dentro del tope por tipo. | medible | personaje, objeto, edificio | nº triángulos totales | spec.geometria.tris_max: personaje 6000, objeto_mano 500, mueble 1500 (calcomanía ≤530) | "Verificación OK (cotas, triángulos, paleta, flotantes, apoyo)" (asset.md §6) + spec |
| `asset.paleta` | Colores solo de spec.paleta; color nuevo se propone, no se usa. | medible | todos | baseColor ∈ spec.paleta | 100 % | "Colores: solo de la paleta" (asset.md §3) |
| `asset.sin_flotantes` | Sin piezas flotantes salvo 'permitir_flotantes' declarado. | medible | todos | componentes sin contacto con el resto/suelo | 0 (excepto lista permitir_flotantes) | "permitir_flotantes: solo si una pieza flota a propósito" (asset.md §3) |
| `asset.apoyo_suelo` | Apoyo en el suelo (Z=0 en Blender; Y=0 en GLB Y-up). | medible | todos | mín. coordenada vertical del asset | = 0 (tolerancia a definir) | "Verificación OK (... apoyo)" (asset.md §6); CLAUDE.md: pies en Z=0 |
| `asset.nombres_pieza` | Nombres de pieza `<Nombre>_<parte>` coincidentes con las cotas. | medible | todos | regex de nombres de nodo vs piezas de cotas | 100 % coincidencia | "Nombres de pieza <Nombre>_<parte> (coinciden con cotas)" (asset.md §4) |
| `asset.alturas_ancla` | Muebles/objetos anclados al cuerpo a altura de ancla del maniquí. | medible | objeto, edificio | altura de la superficie funcional (mm) | asiento=rodilla 21; escritorio=cadera 33; barra=cintura 38.8 (tolerancia a definir) | "asiento = rodilla 21, escritorio = cadera 33, barra = cintura 38.8" (asset.md §4) |
| `asset.reconocible` | Se reconoce qué es sin leer el nombre; coincide en silueta, proporciones y colores. | checklist | todos | revisión visual | - | "se reconoce qué es sin leer el nombre" (asset.md §6) |
| `asset.legible_frente_34` | Detalles legibles de frente y 3/4 a 400 px. | checklist | todos | revisión visual | - | "No gastes vueltas en detalles que no se ven en 400 px" (asset.md §5) |

## `revisar-alth`: revisar-alth + agente revisor-visual-alth

**Propósito:** Revisión de solo lectura de una hoja de 4 vistas con veredicto APROBABLE / UNA_CORRECCIÓN / REHACER.

**Fuentes:**
- GitHub `.codex/skills/revisar-alth/SKILL.md` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)
- GitHub `.claude/agents/revisor-visual-alth.md` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)
- Repo local `/home/claude/alth-meta/.codex/skills/revisar-alth/SKILL.md y .claude/agents/revisor-visual-alth.md` (mismo contenido; deduplicados)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `rev.verificacion_ok` | APROBABLE exige verificación técnica OK (reporte.json) y cero bloqueos. | medible | todos | estado de reporte.json (cotas, tris, paleta, flotantes, apoyo) | OK + 0 bloqueos | "Usa APROBABLE sólo cuando no queden bloqueos visibles y la verificación sea OK" (agente) |
| `rev.hoja_4_vistas` | Existe lectura de frente, lateral, espalda y 3/4. | medible | todos | presencia de las 4 vistas en la hoja | 4/4 | "LECTURA POR VISTA: Frente, Lateral, Espalda, 3/4" (agente) |
| `rev.identidad` | Identidad/semejanza reconocible es la prioridad 1; fallo de identidad = REHACER. | checklist | personaje | revisión visual | - | "Usa REHACER cuando falle la identidad" (agente) |
| `rev.silueta_proporciones` | Silueta y proporciones correctas en las cuatro vistas; luego cara, pelo, vestuario. | checklist | personaje, pelo, ropa | revisión visual | - | "silueta y proporciones en las cuatro vistas; cara, pelo y vestuario" (agente) |
| `rev.iou_no_aprueba` | VERIFICACION OK e IoU son evidencia, no aprobación artística. | checklist | todos | - | - | "VERIFICACION OK e IoU son evidencia, no aprobación artística" (agente) |

## `finalizar-personaje`: finalizar-personaje

**Propósito:** Cerrar un personaje con una ronda integral, pruebas deterministas, evidencia y parada para aprobación humana.

**Fuentes:**
- GitHub `.claude/skills/finalizar-personaje/SKILL.md (= .codex)` — 47 ramas: assets/theo-v10, avatares-chibi, claude/sam3d-proporciones-modeling-hbjhka … (+44)
- Repo local `/home/claude/alth-meta/.claude/skills/finalizar-personaje/SKILL.md`

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `fin.evidencia_completa` | La ronda entrega hoja, reporte y manifest al revisor visual. | medible | personaje | existencia de hoja.png, reporte.json, manifest | 3/3 | "Entregar hoja, reporte, manifest y cambios al revisor visual" (paso 6) |
| `fin.sin_final_sin_aprobacion` | No se genera 'final' ni GLB aprobado sin decisión humana. | medible | personaje | ausencia de export final/GLB en la ronda candidata | 0 exports finales | "No generar final, GLB ni commit aprobado por cuenta propia" (paso 7) |
| `fin.brief_contrato` | Theo: brief_final.md es contrato obligatorio de la ronda. | checklist | personaje | revisión contra brief | - | "tratarlo como contrato obligatorio de la ronda" |

## `copox-auditoria-3d`: copox-auditoria-3d

**Propósito:** Auditoría por niveles de costo de GLB COPOX: filtro barato, preflight gate, 4 vistas y pruebas profundas solo en finalistas.

**Fuentes:**
- GitHub `.claude/skills/copox-auditoria-3d/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `aud.sha_ejes_procedencia` | SHA de baseline, ejes/unidades y procedencia presentes; si falta → RESEARCH_REQUIRED. | medible | todos | campos sha256, ejes, unidades, procedencia en manifest/reference config | todos presentes | "Validar SHA de baseline, ejes/unidades y procedencia ... RESEARCH_REQUIRED" (paso 2) |
| `aud.esquema_indices` | Esquema glTF válido e índices en rango. | medible | todos | validación de esquema; max(index) < nº vértices | 0 errores | "esquemas glTF, mallas, índices" (paso 3) |
| `aud.nan` | Sin NaN en atributos. | medible | todos | NaN/Inf en POSITION/NORMAL/UV/WEIGHTS | 0 | "NaN" (paso 3) |
| `aud.areas_degeneradas` | Sin triángulos de área nula. | medible | todos | triángulos con área ≤ ε | 0 (ε a definir) | "áreas" (paso 3) |
| `aud.normales` | Normales válidas/consistentes. | medible | todos | normales no unitarias o invertidas | 0 | "normales" (paso 3) |
| `aud.self_intersection` | Autointersecciones medidas si hay herramienta. | medible | todos | pares de triángulos intersectados | a definir | "self-intersection si disponible" (paso 3) |
| `aud.skin_animaciones` | Skin y animaciones presentes e íntegras. | medible | personaje, animacion | skins/joints/animaciones vs baseline | sin pérdidas | "comprobar skin/animaciones" (paso 3) |
| `aud.triangulos_protegidos` | Triángulos protegidos intactos. | medible | personaje | hash de caras protegidas antes/después | igualdad | "triangulos protegidos" (paso 3) |
| `aud.preflight_gate` | Métricas focales realmente medidas pasan por preflight_gate; REJECTED_EARLY detiene; DEEP_ELIGIBLE ≠ aprobado. | medible | todos | copox/geometry/preflight_gate.py (seam_connected, target_improvement_pp...) | umbrales de config del gate (no valores por defecto) | "No inventar seam_connected, target_improvement_pp ni usar un valor fijo por defecto" (paso 4-5) |
| `aud.cuatro_vistas_iou` | 4 vistas + acercamiento con cámaras idénticas; IoU global como control de regresión. | medible | todos | IoU por vista candidato vs referencia/baseline (cámara idéntica) | a definir | "IoU global es control de regresión, no criterio artístico único" (paso 6) |
| `aud.poses_finalistas` | Finalistas: poses Wave/Sit/Nod/HeadShake, los 29 clips si existen, import Godot, morphs/UV/pesos. | medible | personaje, animacion | clips presentes y reproducibles; import Godot OK | 29 clips si aplica; Godot OK | "validar poses Wave/Sit/Nod/HeadShake, los 29 clips si existen, importación Godot" (paso 7) |
| `aud.comparacion_artistica` | Comparar contra referencia artística aprobada; promoción solo con Admin. | checklist | todos | revisión visual | - | (paso 6, 8) |

## `copox-geometria`: copox-geometria

**Propósito:** Construir/reparar superficies por ajuste elipsoidal, bucles de borde y puentes de contorno, sin IA generativa.

**Fuentes:**
- GitHub `.claude/skills/copox-geometria/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `geo.bridge_requisitos` | bridge_equal_loops solo con DOS bordes auténticos en UNA malla indexada y misma cardinalidad. | medible | personaje, objeto | nº bucles, misma primitiva, \|loopA\| == \|loopB\| | 2 / misma / igual | "requiere DOS bordes auténticos en UNA malla indexada y con igual conteo de vértices" (paso 5) |
| `geo.no_interpolar_sin_modulo` | No interpolar skin, morphs ni UV sin módulo y pruebas explícitas. | medible | personaje | si cambia nº de vértices y hay morphs/skin sin adaptador → FAIL | veto | "No interpolar skin, morphs ni UV sin un módulo y pruebas explícitas" (paso 6) |
| `geo.max_tres_hermanos` | Máximo tres candidatos hermanos; salida nueva por versión. | medible | todos | nº candidatos por generación; sha nuevo por candidato | ≤ 3 | "Tres candidatos hermanos como máximo" (paso 7) |
| `geo.renders_4_vistas` | PNG reales frente/perfil/trasera/3-4 + detalle antes de pedir aprobación. | medible | todos | presencia de los 5 renders | 5/5 | "Mostrar PNG reales frente/perfil/trasera/3-4, detalle y comparación" (paso 8) |

## `copox-procedencia-3d`: copox-procedencia-3d

**Propósito:** Revisar origen, licencias y trazabilidad de GLB, texturas y referencias antes de afirmar independencia comercial.

**Fuentes:**
- GitHub `.claude/skills/copox-procedencia-3d/SKILL.md (= .codex)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `proc.clasificacion` | Cada componente (malla, textura, material, rig, animación) clasificado VERIFICADO_PROPIO / TERCERO_CONDICIONES / SIN_VERIFICAR / ORIGEN_MIXTO con SHA/URL/fecha. | checklist | todos | manifest de procedencia (verificable por código solo como presencia de campos) | - | (pasos 2-3) |
| `proc.no_independencia_por_cambio` | Nunca deducir independencia por % de cambio o distancia de silueta. | checklist | todos | - | - | (paso 3) |
| `proc.no_desbloquea_promocion` | La revisión de procedencia no sustituye QA artístico ni Godot. | checklist | todos | - | - | (paso 8) |

## `anatomic-cut`: anatomic-cut

**Propósito:** Recortar geometría defectuosa por regiones anatómicas sin perder facciones, normales, UV ni pesos.

**Fuentes:**
- GitHub `.claude/skills/anatomic-cut/SKILL.md (= .codex; versión e7506de más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `cut.triangulos_protegidos` | Triángulos protegidos (ojos, orejas, labios, regiones congeladas) intactos. | medible | personaje | hash/igualdad de caras protegidas antes/después | igualdad | "Clasificar triángulos protected_faces ANTES de operar" (paso 2) |
| `cut.atributos_preservados` | POSITION, NORMAL, TEXCOORD_0, JOINTS_0, WEIGHTS_0 presentes si estaban. | medible | personaje, objeto | set de atributos candidato ⊇ fuente | igualdad de conjunto | (paso 3) |
| `cut.morphs_bloquean` | Morph targets, atributos custom o skin >4 influencias sin adaptador → bloquear. | medible | personaje | presencia de targets / JOINTS_1 / atributos _CUSTOM en región cortada | veto si presentes | "no están cubiertos: bloquear" (paso 4) |
| `cut.bordes_abiertos_nuevos` | Bordes abiertos nuevos se reportan; borde objetivo abierto → Surface Stitch, no superposición. | medible | personaje, objeto | nuevas aristas de incidencia 1 | 0 para aprobar | "Si aparece un borde objetivo abierto, enviarlo a Surface Stitch" (paso 6) |
| `cut.candidato_hermano` | Candidato hermano con hash nuevo; fuentes intactas. | medible | todos | sha candidato ≠ sha fuente; fuente sin cambios | - | (paso 6) |
| `cut.no_por_una_silueta` | No eliminar facciones por una única silueta lateral; comparar todas las vistas/poses. | checklist | personaje | revisión visual | - | (Enlace con Visual Critic) |

## `contour-extractor`: contour-extractor

**Propósito:** Extraer y validar bucles topológicos de borde reales antes de coser, cortar o hacer loft.

**Fuentes:**
- GitHub `.claude/skills/contour-extractor/SKILL.md (= .codex; versión a6046da más completa)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `contour.borde_por_incidencia` | Borde = arista con incidencia en exactamente 1 cara (no edges_unique_length). | medible | todos | conteo de incidencia arista→caras | definición exacta | "extraer aristas con incidencia en exactamente 1 cara" (paso 2) |
| `contour.seams_uv_no_agujeros` | Distinguir seams por UV duplicadas de agujeros físicos. | medible | todos | bucles de borde tras soldar por posición (diagnóstico) vs topología indexada | clasificación explícita | (paso 3) |
| `contour.gate_dos_bucles` | GATE: exactamente dos bucles reales no ramificados. | medible | personaje, objeto | nº bucles; grado de vértices de borde == 2 | 2 y sin ramas | "GATE: exactamente dos bucles reales no ramificados" (paso 6) |
| `contour.sin_lentes_alastor` | Alastor: sin primitiva/pieza 'Lentes' (montura, cristales, puente, patillas). | medible | personaje | nodos/primitivas con pieza/nombre Lentes | 0 | "El objetivo de la cabeza es SIN montura, cristales, puente ni patillas" (G2-C2) |
| `contour.residuo_lentes` | Rastros de patillas/montura fusionados con la cara revisados en todas las vistas. | checklist | personaje | revisión visual | - | (G2-C2) |

## `surface-stitch`: surface-stitch

**Propósito:** Unir dos superficies con bordes abiertos compatibles en una sola topología conservando atributos.

**Fuentes:**
- GitHub `.claude/skills/surface-stitch/SKILL.md (= .codex; versión 356f53d más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `ss.cardinalidad_sentido` | Contornos de igual cantidad de puntos y sentido consistente (kernel igual-longitud). | medible | personaje, objeto | \|loopA\|==\|loopB\|; winding | igual | (paso 2) |
| `ss.reusa_vertices` | La banda usa IDs de vértices existentes; UV, pesos y normales originales intactos; sin morph interpolado. | medible | personaje, objeto | nº vértices sin cambio; arrays de atributos idénticos | igualdad | (paso 4) |
| `ss.material_por_cara` | Material de la banda registrado por cara. | medible | personaje, objeto | material id por cara nueva | 100 % asignado | (paso 4) |
| `ss.calidad_topologica` | Conectividad, manifold, winding, distancias, degenerados y autointersecciones comprobados; si falta alguno → RESEARCH_REQUIRED. | medible | personaje, objeto | non-manifold, winding inconsistente, degenerados, intersecciones | 0 | (paso 5) |
| `ss.reimportacion` | Conectividad conservada tras export GLB y reimportación. | medible | personaje, objeto | bucles de borde en la unión tras reimport | 0 (igual que en RAM) | "Se requiere un exportador glTF/GLB validado, prueba de reimportación" (paso 6) |
| `ss.overlap_no_es_cierre` | Un overlap visualmente limpio no es un cierre topológico. | medible | personaje, objeto | conectividad por índices, no proximidad | - | (Enlace con Visual Critic) |

## `stitch-advancing-front`: stitch-advancing-front

**Propósito:** Triangulación de frente de avance entre dos bucles reales de longitud diferente, con validación y rechazo de exportaciones inseguras.

**Fuentes:**
- GitHub `.claude/skills/stitch-advancing-front/SKILL.md (= .codex)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `saf.caras_N_mas_M` | La banda consume una arista por triángulo: N+M caras. | medible | personaje, objeto | nº caras banda | = N+M | "greedy consume exactamente una arista de un anillo por triángulo (N+M caras)" |
| `saf.gap_maximo` | Máximo gap de todas las conexiones cruzadas validado. | medible | personaje, objeto | longitud máx. de arista cruzada | a definir | "valida máximo gap de TODAS las conexiones cruzadas" |
| `saf.ratio_aristas` | Ratio de aristas acotado. | medible | personaje, objeto | ratio arista máx/mín por triángulo | a definir | "ratio de aristas" |
| `saf.no_degenerados_winding` | Área no degenerada, winding consistente, sin non-manifold ni bucles restantes. | medible | personaje, objeto | conteos | 0 | "área no degenerada, winding, nonmanifold y ausencia de bucles restantes" |
| `saf.flags_promocion` | No promover si self_intersections_checked, exported_glb_verified o artistic_references_approved = false. | medible | personaje, objeto | flags del reporte | las 3 = true | "No promover variantes mientras self_intersections_checked=false ..." |
| `saf.determinismo` | Mismos arrays → mismos índices de triángulo. | medible | todos | hash de índices en dos corridas | igualdad | (Determinismo) |

## `scully`: scully (Surface Sculpt)

**Propósito:** Esculpir matemáticamente regiones sanas (aplanar frente, redondear nuca) con ROI, falloff y presupuesto de desplazamiento.

**Fuentes:**
- GitHub `.claude/skills/scully/SKILL.md (= .codex; versión 0e4559f más completa)` — 15 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+12)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `scully.presupuesto_desplazamiento` | Desplazamiento máximo ≤ límite del plan; si se excede, rechazar sin recortar. | medible | personaje, objeto | desplazamiento máx. medido (mm) | ≤ límite declarado en geometry_plan.json | "Si el presupuesto se excede, rechazar sin recortar silenciosamente" (paso 4) |
| `scully.mascara_facciones` | Vértices de ojos, boca, orejas y piezas congeladas sin desplazamiento. | medible | personaje | desplazamiento en máscara congelada | 0 | (paso 3) |
| `scully.exceso_medido` | Requiere signed_excess_mm positivo medido y trazable antes de aplicar. | medible | personaje, objeto | signed_excess_mm | > 0 | "medición positiva signed_excess_mm" (Enlace) |
| `scully.coordenadas` | Coordenadas declaradas (glTF Y-up/m Maniquí; Z-up/mm otros). | medible | todos | ejes/unidades en manifest | declarados | (paso 2) |
| `scully.cambio_no_es_mejora` | Cambio visible ≠ mejora; contrastar con todas las referencias. | checklist | personaje, objeto | revisión visual | - | (paso 6) |

## `gltf-rig-guardian`: gltf-rig-guardian

**Propósito:** Auditar preservación de glTF: skeleton, atributos, materiales, UV, morphs y canales animados; gates de import Godot.

**Fuentes:**
- GitHub `.claude/skills/gltf-rig-guardian/SKILL.md (= .codex; versión 0446cf0 más completa)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `grg.joints_ibm_nombres` | Preservar joints, inverseBindMatrices, nombres y pistas de animación válidas. | medible | personaje, animacion | diff vs fuente | sin pérdidas | (Invariante 2) |
| `grg.joints_weights_finitos` | JOINTS_0 y WEIGHTS_0 juntos y finitos; pesos normalizados. | medible | personaje, ropa, pelo | presencia conjunta; NaN/Inf; \|Σw−1\| | juntos / 0 / a definir | "JOINTS_0/WEIGHTS_0 juntos y finitos" (Invariante 2) |
| `grg.atributos_materiales_morphs` | UV, materiales, texturas y morph targets preservados; materiales por cara intactos. | medible | todos | diff fuente/candidato | sin pérdidas | (Invariantes 2, 5) |
| `grg.claves_variables` | Un clip definido no prueba movimiento: contar claves variables por clip. | medible | animacion | canales con valores no constantes por clip | > 0 por clip declarado | "La definición de 29 clips no prueba 29 movimientos" (Invariante 3) |
| `grg.canales_malla_vacia` | Canales faciales sobre malla vacía = NO FUNCIONALES. | medible | personaje, animacion | canales weights cuyo mesh no tiene vértices/targets | 0 (o marcados NO FUNCIONAL) | "Los 15 canales faciales heredados sobre malla vacía deben marcarse NO FUNCIONALES" |
| `grg.accesores_vacios` | Sin accessors/primitivas vacías (sanear en copia). | medible | todos | accessors count=0; primitivas sin POSITION | 0 | (Invariante 6) |
| `grg.godot_bones` | Godot headless importa y cuenta 56 bones (personajes base 56). | medible | personaje | bones en Skeleton3D importado | 56 (según asset) | "contar 56 bones" (Invariante 7) |
| `grg.gates` | IMPORT_OK, ANIMATION_TRACKS_OK, DEFORMATION_OK, ATTRIBUTES_OK deben pasar (más VISUAL_CRITIC_OK). | medible | personaje, animacion | estado de cada gate | todos PASS | (Invariante 8) |
| `grg.sin_lentes_alastor` | Candidato de Alastor sin primitiva 'Lentes'; ACCESSORY_REMOVED ≠ ALL_EYEWEAR_RESIDUE_GONE. | medible | personaje | primitivas con nombre/pieza Lentes | 0 | (G2-C2 Eyewear Guardian) |

## `rig-architect`: rig-architect

**Propósito:** Diseñar y validar esqueletos, bind poses, pesos y límites articulares preservando animaciones.

**Fuentes:**
- GitHub `.claude/skills/rig-architect/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `ra.convenciones` | Convenciones up/front/units declaradas. | medible | personaje | campos en manifest | declarados | (paso 2) |
| `ra.bind_pose_pesos` | inverseBindMatrices, JOINTS_0 y WEIGHTS_0 normalizados; sin puntos de peso cero. | medible | personaje, ropa | \|Σw−1\|; vértices Σw=0 | a definir / 0 | "Evitar puntos de peso cero" (paso 4) |
| `ra.sin_cambios_joint` | Sin cambios de joint no autorizados. | medible | personaje | diff nombres/padres/rest vs base | 0 | (paso 4) |
| `ra.sin_mallas_partidas` | Sin mallas partidas al exportar. | medible | personaje | componentes conexos antes/después de export | igual | (paso 4) |
| `ra.simetria` | Tests de pesos/transformaciones/simetría. | medible | personaje | diferencia espejo L/R en rest de joints | a definir | (paso 7) |
| `ra.estres_articular` | Estrés articular sin penetración ni pinzamiento en codos, rodillas, hombros, caderas, dedos. | medible | personaje, animacion | autointersecciones en poses de estrés | a definir | (paso 5, 7) |
| `ra.clips_preservados` | Clips existentes preservados salvo reemplazo aprobado. | medible | animacion | nº y nombres de clips vs base | sin pérdidas | (paso 7) |
| `ra.proporcion_chibi` | Movimiento optimizado para la silueta estilizada ('avatar de dos cabezas'). | checklist | personaje, animacion | revisión visual | - | (paso 5) |

## `motion-lab`: motion-lab

**Propósito:** Crear y corregir animaciones con biomecánica, contactos, trayectoria y timing contra referencias de vídeo/pose.

**Fuentes:**
- GitHub `.claude/skills/motion-lab/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `motion.pies_plantados` | Pies plantados durante apoyo (sin foot sliding). | medible | animacion | desplazamiento horizontal del pie en apoyo | a definir (ver rig.foot_sliding: <2 % longitud pie) | (paso 4) |
| `motion.suelo` | Sin penetración del suelo. | medible | animacion | mín. altura de pies por frame | ≥ 0 (tolerancia a definir) | "suelo, colisiones" (paso 4) |
| `motion.joint_limits` | Reportar violaciones de límites articulares. | medible | animacion | rotaciones fuera de límites del rig | 0 | (paso 4) |
| `motion.penetraciones` | Reportar penetraciones (manos-objetos, cuerpo). | medible | animacion | intersecciones por frame | 0 (a definir) | (paso 4) |
| `motion.loops_continuidad` | Loops y transiciones continuas; rotaciones SLERP. | medible | animacion | diferencia pose primer/último frame en loops; saltos entre frames | a definir | (paso 4-5) |
| `motion.clips_heredados` | Mantener los 29 clips heredados del Maniquí sin sobrescribir; nuevos clips versionados. | medible | animacion | nº y nombres de clips | ≥ 29 heredados intactos | (paso 5) |
| `motion.hoja_temporal` | Contact sheet multivista en inicio, transición, mitad, final y eventos por referencia. | medible | animacion | presencia de frames clave renderizados | 5 por referencia | (paso 6) |
| `motion.no_sinusoide` | No caminata por rotación sinusoidal; fases de apoyo/balanceo, pelvis, contrapeso de brazos. | checklist | animacion | revisión visual | - | (paso 2) |

## `facial-acting`: facial-acting

**Propósito:** Gestualidad facial (parpadeo, mirada, mandíbula, labios, visemas) validada contra todas las referencias faciales.

**Fuentes:**
- GitHub `.claude/skills/facial-acting/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `facial.inventario_morphs` | Inventariar los morph targets que realmente existen antes de editar. | medible | personaje | lista de targets por malla | registrado | (paso 2) |
| `facial.no_destruir_morphs` | No destruir morph targets. | medible | personaje | nº/nombres de targets vs base | sin pérdidas | (paso 7) |
| `facial.clipping` | Sin clipping de párpados, dientes/lengua, iris ni z-fighting en extremos (ojo izq/der, parpadeo completo, boca abierta, habla). | medible | personaje, animacion | intersecciones en poses extremas de morphs | 0 (a definir) | (paso 5) |
| `facial.orejas_fijas` | Expresiones no desplazan orejas ni rompen unión craneofacial. | medible | personaje | desplazamiento de vértices de oreja en cada target | 0 | (paso 3) |
| `facial.parpadeo_completo` | Parpadeo completo cierra el ojo. | medible | personaje | apertura palpebral con blink=1 | a definir | (paso 5) |
| `facial.identidad_sobria` | Preservar identidad chibi-soft; evitar expresiones demasiado tiernas si el brief pide sobriedad. | checklist | personaje | revisión visual | - | (paso 4) |

## `cloth-dynamics`: cloth-dynamics

**Propósito:** Movimiento de tela (gabardinas, faldones) con colisiones al caminar/sentarse y comparación contra referencias.

**Fuentes:**
- GitHub `.claude/skills/cloth-dynamics/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `cloth.clipping_transiciones` | Estabilidad y clipping medidos durante transiciones, no solo en poses finales. | medible | ropa, animacion | penetración/intersección por frame en walk/run/sit/stand/turn/jump | a definir | (paso 5, 7) |
| `cloth.contactos` | Contacto con asientos, rodillas, manos y gabardina sin atravesar. | medible | ropa, animacion | penetración con colliders | 0 (a definir) | (paso 5) |
| `cloth.autointerseccion_faldones` | Sin autointersección de faldones. | medible | ropa | autointersecciones de la prenda | 0 | (paso 4) |
| `cloth.rig_base_intacto` | No modificar el rig base sin aprobación. | medible | ropa, personaje | diff joints base | 0 | (paso 7) |
| `cloth.godot_import` | Prueba de importación y física en Godot con evidencia. | medible | ropa | import Godot OK | OK | (paso 7) |
| `cloth.zonas_conservadas` | Conservar dobladillos, botones, mangas y bolsillos. | checklist | ropa | revisión visual | - | (paso 2) |
| `cloth.metodo_declarado` | Declarar si es huesos/springbones/cloth; no afirmar física real si se mueve por huesos. | checklist | ropa | - | - | (paso 3) |

## `visual-critic`: visual-critic

**Propósito:** Comparación cruzada obligatoria contra TODAS las referencias/vistas/poses, sin promedios que oculten discrepancias.

**Fuentes:**
- GitHub `.claude/skills/visual-critic/SKILL.md (= .codex; versión be20d55 más completa)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `vc.cobertura_total` | Todas las referencias cubiertas; si falta vista/cámara/referencia → INCOMPLETE. | medible | todos | cobertura report.json (referencias con par comparativo / total) | 100 % | "Si faltan vistas ... emitir INCOMPLETE" |
| `vc.vistas_personaje` | Personajes: frente, 3/4, perfil y espalda renderizados. | medible | personaje, pelo, ropa | vistas presentes | 4/4 | (Contrato) |
| `vc.iou_chamfer_por_par` | IoU y Chamfer por pareja solo con máscara binaria y cámara alineada. | medible | todos | IoU / Chamfer por referencia | a definir | "con máscaras binarias y cámaras exactas, IoU y Chamfer por pareja" |
| `vc.peor_discrepancia` | Gate sobre la peor referencia, no el promedio. | medible | todos | min(IoU) por referencia; nº ISSUE | a definir | "No concluir sólo con IoU ni promedios. Informar peor discrepancia" |
| `vc.matriz_anomalias` | anomaly_cross_view_matrix cubre todos los IDs de referencia. | medible | todos | IDs cubiertos / total | 100 % | (Enlace ejecutable) |
| `vc.procedencia_medicion` | measurement_provenance con SHA-256, método, ejes y unidades. | medible | todos | campos presentes | 4/4 | (Enlace ejecutable) |
| `vc.renders_reales` | Renders reales del GLB, no imágenes generadas; no mezclar fotos y PNG generados como mismo ángulo. | checklist | todos | - | - | (Regla de procedencia) |
| `vc.bultos_curvatura` | Buscar bultos, hundimientos, huecos, asimetrías, fragmentos flotantes en múltiples proyecciones. | checklist | todos | revisión visual (apoyo: curvatura/normales) | - | (Diagnóstico 3) |
| `vc.sin_residuo_lentes` | Alastor: sin montura/cristales/puente/patillas en frontal, 3/4, perfiles y espalda. | checklist | personaje | revisión visual | - | (G2-C2) |

## `regional-cassettes`: regional-cassettes

**Propósito:** Evaluar y versionar por región (nuca, ojos, manos, ropa...) sin vetos globales por fallos ajenos ni daños a datos compartidos.

**Fuentes:**
- GitHub `.claude/skills/regional-cassettes/SKILL.md (= .codex)` — 8 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+5)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `reg.fuera_roi_identico` | Todas las primitivas/atributos/animaciones fuera de la región, iguales. | medible | todos | igualdad de arrays por primitiva fuera de ROI (snapshot previo) | igualdad exacta | "comprobar igualdad de todas las primitivas/atributos/animaciones fuera de alcance" (paso 4) |
| `reg.original_en_region` | Si solo se añade piel, la geometría original de la región se conserva. | medible | personaje | vértices originales de ROI sin cambio | igualdad | (paso 4) |
| `reg.fallos_globales` | Rechazo global si invade geometría congelada o rompe huesos/pesos, materiales, animaciones o integridad. | medible | todos | diff de congeladas, skins, materiales, animaciones | 0 cambios | (Fallos realmente globales) |
| `reg.no_global_approved` | Reporte regional con global_model_approved=false; no llamar global_watertight a un parche con bordes laterales abiertos. | medible | todos | campos del reporte; bordes abiertos | false / coherente | (Contrato de evidencia) |
| `reg.lamina_triangulos_nuevos` | Captura que destaque solo triángulos nuevos (4 vistas). | checklist | todos | - | - | (paso 5) |

## `regional-asset-qa`: regional-asset-qa

**Propósito:** Orquestar QA por regiones independientes con auditor de seguridad global obligatorio.

**Fuentes:**
- GitHub `.claude/skills/regional-asset-qa/SKILL.md (= .codex)` — 1 ramas: experimentos/maniqui-g2c2-contorno-facial

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `rqa.global_safety` | Siempre existe un auditor scope 'global_safety' (rig, materiales, vecinos, integridad, baseline). | medible | todos | auditores del cassette con scope global_safety | ≥ 1 | (paso 1) |
| `rqa.vecinos` | Sin daño a vecinos, costuras entre piezas, UV, pesos ni animaciones. | medible | todos | diff fuera de región | 0 | (paso 3) |
| `rqa.cuatro_puertas` | Cuatro puertas distintas: técnica local, artística local, integración, autorización humana. | checklist | todos | - | - | (paso 7) |

## `regional-model-auditor`: regional-model-auditor

**Propósito:** RegionVerdict por ROI; defecto nuevo en vecino → BLOCKED_INTEGRATION del candidato responsable.

**Fuentes:**
- GitHub `.claude/skills/regional-model-auditor/SKILL.md (= .codex)` — 1 ramas: experimentos/maniqui-g2c2-contorno-facial

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `rma.vecino_nuevo_defecto` | Defecto nuevo en un vecino afectado → BLOCKED_INTEGRATION. | medible | todos | diff de regiones vecinas antes/después | 0 cambios | (paso 7) |
| `rma.indices_regiones_ajenas` | Regiones ajenas no cambian ni pierden índices o atributos. | medible | todos | igualdad de índices/atributos fuera de ROI | igualdad | (paso 3) |
| `rma.registro` | Registrar SHA base, SHA candidato, máscara ROI, desplazamiento local, nuevas aristas/caras. | medible | todos | campos del reporte | presentes | (paso 4) |

## `geometry-profiler`: geometry-profiler

**Propósito:** Perfilado determinista del motor geométrico; optimización nunca equivale a aprobación.

**Fuentes:**
- GitHub `.claude/skills/geometry-profiler/SKILL.md (= .codex)` — 10 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+7)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `prof.mismos_triangulos` | Un candidato optimizado genera los mismos triángulos (hash determinista). | medible | todos | hash de triángulos | igualdad | (Instrumentación) |
| `prof.research_required` | Sin contorno validado, con UV/skin no soportado, autointersección no auditada o Godot pendiente → RESEARCH_REQUIRED. | medible | todos | flags de gates previos | todos resueltos | (Fallos que impiden promoción) |

## `scene-director`: scene-director

**Propósito:** Escenas Godot: iluminación, cámaras, composición, props y navegación contrastadas con referencias de encuadre.

**Fuentes:**
- GitHub `.claude/skills/scene-director/SKILL.md (= .codex)` — 14 ramas: experimentos/g2c2-nuca-evaluacion-regional, experimentos/g2c3-nuca-superficie-visible, experimentos/g2c3-v3-rapado-detras-oreja-izquierda … (+11)

| id | regla | tipo | aplica_a | métrica | umbral | cita |
|---|---|---|---|---|---|---|
| `scene.flotantes_suelo` | Sin objetos flotantes; contacto con suelo. | medible | edificio, objeto | gap objeto↔suelo/soporte | 0 (a definir) | (paso 6) |
| `scene.z_fighting` | Sin z-fighting. | medible | edificio, objeto | caras coplanares solapadas | 0 | (paso 6) |
| `scene.escala` | Escala de puertas y props coherente con personajes. | medible | edificio, objeto | alturas vs spec/arquetipos | a definir | (paso 3, 6) |
| `scene.camaras_reproducibles` | Cámaras con posición, orientación, FOV/ortográfica, distancia y aspect ratio registrados. | medible | edificio | campos de cámara | presentes | (paso 4) |
| `scene.fps_medidos` | No inventar fps ni estabilidad sin medir. | medible | edificio | fps medido en Godot headless | a definir | (paso 7) |
| `scene.iluminacion_lectura` | Iluminación, sombras, oclusión y lectura del gameplay correctas. | checklist | edificio | revisión visual | - | (paso 4, 6) |

