# LECCIONES · ALTH-META / COPOX (26 sep – 19 oct 2026)

Este archivo junta lo que se aprendió en el camino, para no repetirlo. La historia completa está en `docs/BITACORA_MAESTRA.md`. Cada lección sigue el formato **falla → causa → arreglo → regla**.

## A. Reglas de Admin (vigentes)

**Palabras clave**
- **Lápiz** = diseñar, sin crear ni modificar nada.
- **Martillo** = construir lo acordado.
- **Dispara** = preguntar antes.

**Trabajo y registro**
- Presupuesto cero.
- Todo movimiento en el Drive de Gaston o en el GitHub de Klymapo se registra en la Memoria maestra, sección «Registro de cambios».
- Carpetas de Drive en MAYÚSCULAS.
- No borrar nada; lo que sobre va a la papelera.
- Verificar en la fuente (repo o Drive) antes de decir que algo está pendiente.

**Versiones**
- Cada versión lleva número nuevo, sale **SIN APROBAR** y nunca se sobrescribe.
- Los GLB van solo a `copox-modelos`, nunca al repo público.
- Theo Alpha (`ed2b04ec…`) es intocable.
- `ADAN_BASE_CONGELADA.glb` no se edita: los personajes nuevos parten de ella.

**Método**
- Máximo **3 iteraciones** por método. Si no se llega a unanimidad: **PLATEAU**, se conserva la baseline y se cambia de técnica.
- Antes de una técnica nueva va un research brief (skill `investigar-referencias`).
- Mandan las referencias renderizadas; el PDF de 95 mm es histórico.

**Herramientas**
- Usar siempre la versión más nueva de CHXP (hoy V3).
- Mostrar acercamientos de la zona que se tocó.
- Promoción técnica no es aprobación artística: el score nunca sustituye la revisión visual.

**Estilo**
- **Pelo:** cubre siempre toda el área (≥ 99.5 %) y se mueve como pelo, con resortes.
- **Ropa:**
  - Por capas, nunca pintada; un poco holgada.
  - Con la textura que le corresponde, sutil.
  - Respeta el límite entre pantalón y zapato.
  - La técnica del short es la referencia.
- **Cuerpo:** «liso y plano», sin bultos ni huecos. Boca de malla, no calcomanía. Dedos separados.
- **Colores:** solo de la paleta. Un color nuevo se propone antes de usarlo.

## B. Errores técnicos que ya costaron horas

| Falla | Causa | Arreglo | Regla |
|---|---|---|---|
| GLB de 150 MB y SHA distinto (19 oct) | Falta `GODOT_BIN` y `simplificar()` devuelve la malla densa sin avisar | `export GODOT_BIN=/home/claude/godot/Godot_v4.7.2-stable_linux.x86_64` | Verificar el entorno antes de construir. *Propuesta: que falle si falta.* |
| Triángulos al revés después de simplificar | El LOD de `simplificar.gd` invierte el sentido de los triángulos | Reordenarlos | Revisar el volumen con signo después de pasar por Godot |
| Párpados, dientes y lengua colapsados en Godot (V24) | LOD automático al importar | LOD desactivado en `copox/godot/` | Comparar siempre CHXP contra Godot |
| Piezas invertidas (22 en el maestro; mano en V36–37) | El material `doubleSided` las escondía | `orientar.py` | Revisar el signo en cada malla nueva |
| «Labios fantasma» (≈3,800 vértices con más de 45° de error) | Normales viejas después de editar | `Editor.recalcular_normales` | Recalcular las normales después de cada edición |
| Piezas abiertas, cráteres y superficies fantasma en `ropa_ajustada` | Signo al azar de la distancia lejos de la pieza | Lo lejano cuenta como afuera; confirmar con paridad de rayo | Las capas cerradas se validan por paridad |
| Bucket de la pelvis inexistente | Signo invertido `-(y - y_bot)` | Corregir el signo | Probar cada SDF con un corte 2D antes de usarlo en malla |
| Hoyos al escalar el zapato | Se escalaba alrededor del tobillo | Anclar en el talón y no hacerlo nunca más angosto que el tobillo | Escalar desde el punto de apoyo |
| Los resortes del pelo no se mueven | El SpringBoneSimulator3D se creó antes del primer cuadro; el modo MANUAL no corre en 4.7 | Crearlo con el árbol ya corriendo y renderizar con `--fixed-fps 60` | Rigidez 4, arrastre 0.6, gravedad 0.1; los mechones de cobertura van fijos a `Head` |
| Pelo con dientes contra la piel | Separaciones de ~1 mm rebasan la precisión de profundidad | PeloOrilla con distancia real + `cerrar_bordes` (tope 3 mm) | Dejar más de 1 mm de separación |
| Hombros blancos (Theo V4 y V4_1) | La sisa recortaba el hombro y el chaleco tenía un tope de altura fijo | Tirante medido desde la articulación del brazo; chaleco hasta el cuello | Gate `hombro_cubierto` en CHXP V3 |
| La ropa atraviesa en poses | Pesos de piel distintos entre capas, más el cuello oculto | Se probaron pesos de brazo en el chaleco (mejora parcial) | PLATEAU. Siguiente paso: prueba de capas sobre lo **visible** en el render |
| Recetas que ya no se reproducen | Las recetas usan funciones privadas de otras como librería (`v24._add_raw`, `v39._leer`, `v41._prim_nueva`, `v49._*`) | `ALTH_MALLA=exacta` y el commit fijo | Pasar esos helpers a `copox/medicion` |
| 7 de 7 corridas nocturnas perdidas (18 oct) | El entorno programado no tenía acceso a `copox-modelos` | — | Probar el acceso con una corrida manual corta antes de programar |
| Shrinkwrap pega la cara a los lentes | Proyección global | Shrinkwrap por zonas, y después trasplantar piezas | Trasplantar o generar antes que proyectar |
| Más de 20 rondas G2 en PLATEAU | Parchar mallas heredadas sin piel debajo | Generar la pieza desde cero (Adán) | No parchar mallas ajenas |
| Una métrica en verde con el modelo mal | El IoU no ve huecos ni cajas (la manzana «caja», v0.3 r1 con 99 %) | Evaluar por región + revisión visual | Ninguna métrica sola aprueba |
| Mangas «remangadas» del abrigo de Alastor (V03–V04) | La caja de mallado del abrigo terminaba en x = ±0.29: cortaba la manga y dejaba ver el puño blanco | Caja a ±0.345 (V05) | La caja de `_malla` debe contener la prenda completa; medir x máx. del resultado contra el parámetro |
| Picos en el bajo trasero del abrigo de Alastor (V04–V06) | El abrigo es un sólido: el corte del bajo dejaba una tapa horizontal entre las piernas, pesada a LowerLeg, que se estiraba al posar | Quitar la tapa (material doubleSided) + alisar pesos de la falda sobre la malla **soldada por posición** (V11) | Una prenda abierta no lleva tapa; alisar pesos siempre después de soldar duplicados (sin soldar se rompe, V09) |
| `pip install bpy` falla en la sesión (20 oct) | El proxy de la sesión rechaza `pypi.org` | Blender en Actions (`tools/blender_ci.sh`) | No depender de PyPI en la sesión; probar con Actions |
| No se pueden leer logs ni artifacts de Actions desde la sesión | Ambos se sirven desde blob storage, bloqueado por el proxy | Errores como anotaciones `::error::` (API de check-runs) y resultados a una rama git | Todo workflow nuevo reporta por anotaciones y guarda su resultado en una rama |
| Cine: encuadre y AO con cubos de 2 m o piezas sin caras | El importador glTF de Blender crea mallas ayudantes (formas de hueso) | Sólo cuentan las mallas cuyo nodo o malla existe en el GLB | Filtrar siempre contra el JSON del GLB, no contra la escena de Blender |
| TwoBoneIK3D no mueve el brazo en T-pose | Extremidad recta: sin plano de flexión | Nodo polo (rodilla +Z, codo −Z) | Todo IK de dos huesos lleva polo |
| `ensure_blender.sh` falla en Actions | `bpy==5.2.2`/`4.5.14` no existen en PyPI | `blender_ci.sh` instala bpy sin versión fija (salió 5.0.1, Python 3.11) | No fijar versiones que no se han visto en PyPI |
| La corrección de hombros rompe 6 clips | Cambio global de pesos | Descartada | Regresión de todos los clips antes de aceptar |

## C. Técnicas que funcionaron

**Fabricación**
- Recetas reproducibles bit a bit, verificadas por SHA.
- Superficie implícita → marching cubes → Taubin → meshoptimizer vía Godot.
- `ALTH_CALIDAD=borrador` para iterar rápido.

**Cuerpo**
- Superelipse por cortes (cabeza V33).
- Loft por secciones (pie V46).
- Relleno biarmónico del residuo (quijada y boca V30).
- Repesado por cadena con rampas.
- Manos rígidas intercambiables cosidas a la muñeca.
- Pelvis: torso extruido + muslos superelípticos que se unen en la V inguinal (boceto de Admin).
- Zapato: suela, corte y tacón como piezas separadas, con el empeine diseñado.

**Pelo**
- Bloques low-poly sobre el arco medido con SENKU en 3 vistas.
- Mechones fijos para cubrir.
- SpringBoneSimulator3D.

**Ropa**
- `ropa_tubos` («técnica del short»): secciones superelípticas ajustadas al cuerpo, suavizadas.
- La capa de encima es el mismo tubo inflado.
- Texturas de tela en gris, que modulan el color de la paleta.

**Medición y auditoría**
- SENKU (unidad ED, cámara imitada, consistencia entre vistas).
- CHXP V2/V3: Godot real + compuertas con veto + inventario de skills.

**Otros**
- KHR_node_visibility para piezas intercambiables.
- Locomoción por IK en código.

## D. Pasos repetitivos → skills (hechas el 19 oct 2026)

Hechas: `publicar-version` (`python -m copox.publicar`), chequeo de entorno (`python -m copox.entorno`; `simplificar()` ya falla si no hay Godot), CHXP `--rapido` (~35 s contra 2.5 min), `crear-avatar` (`python -m copox.avatar ficha.json`), `vestir-personaje` y `peinar-personaje` (catálogo `copox/medicion/catalogo.py`). Prueba: `personajes/theo.json` reproduce THEO_VESTIDO_V4_1 con el mismo SHA (`74fc6240…`).

Hechos después (19 oct, noche): `python -m copox.medicion.senku_ficha` (la referencia propone la ficha: colores por región → paleta con ΔE, conjunto, calzado; probado en la hoja de Theo: pelo → rubio_miel ΔE 2.7, chaleco ΔE 1.0, corbata ΔE 5.2), compuerta `senku_regiones` (pisos por región), compuerta `capas_visibles` (render: la capa de abajo asomándose por la de arriba; `capas_sin_atravesar` pasa a informativa), lámina `<nombre>_COMPARATIVA.png` + agente `revisor-visual-alth` obligatorio antes de mandar, y `copox/medicion/glb_util.py` (helpers fuera de las recetas; V50_1 y Theo V4_1 conservan su SHA).

Tabla original:

| Paso | Cuántas veces se ha repetido | Skill propuesta |
|---|---|---|
| Publicar una versión: receta con `GODOT_BIN` → SHA → `copox-modelos` → `SHA256SUMS` → `ULTIMA.txt` → capturas → push → Drive | Unas 44 versiones; ULTIMA.txt se corrigió 2 veces | `publicar-version` |
| Paquete de capturas en la rama `capturas` | 71 commits | Dentro de `publicar-version` |
| Ficha `ADAN_VNN.md` | 27 fichas | Dentro de `publicar-version` |
| Arranque de sesión: Godot 4.7.2, xvfb, `GODOT_BIN`, clonar `copox-modelos` | Cada sesión | `preparar-entorno` (o un chequeo en CHXP) |
| Vestir (camisa, chaleco, pantalón, corbata, zapato) | Theo V1→V4_1 | `vestir-personaje` (catálogo con presets) |
| Peinar (arco SENKU, bloques, resortes, cobertura) | Theo y Adán | `peinar-personaje` |
| Construir un personaje de punta a punta | — | `crear-avatar` (ficha JSON → un comando) |

## E. Métodos descartados (no repetir sin un research brief nuevo)

- Shrinkwrap global.
- Dedos por micro-valles o booleanos.
- Aplanar labios contra un ajuste local o un polinomio global.
- Relajación tangencial.
- Agarre con Powell de 16 parámetros.
- Pierna cónica de 8 caras.
- Campo local de cabeza (V48.1).
- Envolvente por dirección.
- Cabeza caja (V48).
- Ropa ajustada pintada (Theo V1).
- Pelo de «bolas encadenadas».
- PeloCunas.
