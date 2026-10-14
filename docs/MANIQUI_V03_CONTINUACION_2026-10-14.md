# Continuación del PR #34 desde Maniquí v0.3

Estado final: **PLATEAU — 3/3 iteraciones, ninguna aprobada**. Sin promoción ni fusión. Fecha: 2026-10-14.

## Base, alcance y research brief
Base única de los candidatos hermanos: `assets/maniqui/maniqui_v0_3.glb`, commit `f60267bc600c74c5bd658fac7194c11f5c63899f`. Se conservan v0.2, v0.3, Delta y todos sus binarios. glTF Y-up, metros, frente +Z; no aplicar la convención ALTH de milímetros/Z-up a estos datos.

Inspeccionados `maniqui.py`, `reparar_v03.py`, reporte v0.3, notas de relevo, memoria maestra y bitácoras de Drive. El recorte por color de Gamma y la separación por bins de la cúpula dejan dos bordes incompatibles. El parche v0.3 sigue el borde de la cúpula y no reconstruye la piel de las sienes. Los bordes UV no equivalen a agujeros: al unificar posiciones a 1 micrómetro, Cabeza pasa de 5406 a 3146 posiciones y tiene 15 componentes; varios son facciones (nariz y párpados). No descartar componentes sólo por tamaño. Toda Cabeza está rígidamente pesada al joint 5 (Head).

Hipótesis: reemplazar la cúpula y el tejido defectuoso superior por una superficie paramétrica continua, con borde inferior guiado por piel existente. Preservar los vértices y triángulos de ojos, nariz, boca, orejas y cuerpo fuera de la banda. Ajustar la transición mediante interpolación radial por ángulo y altura, no mediante el punto euclidiano más cercano sin restricciones. La guía elipsoidal se obtiene del cráneo existente. No se afirma soldadura topológica si la transición resulta sólo superpuesta.

Fuentes técnicas locales: glTF 2.0 POSITION/NORMAL/JOINTS_0/WEIGHTS_0, funciones de lectura y escritura ya utilizadas por el proyecto; parametrización elipsoidal y suavizado periódico de SciPy. Herramientas libres: Python, NumPy, SciPy, Pillow; Blender disponible si hace falta una segunda visualización. Sin APIs generativas ni servicios de pago.

## Criterios y parada
Máximo tres candidatos hermanos desde v0.3. Evaluar cada uno con cuatro vistas reales (frente, 3/4, perfil, espalda), acercamientos, poses Wave, Sit-pose y movimiento de cabeza. IoU de silueta >=95% por vista es una señal de conservación, no aprobación artística. Verificar binarios de animación/skin/nodos, 56 huesos, 29 clips, facciones protegidas y ausencia de regresión fuera de la cabeza. Si no hay resultado suficiente, registrar PLATEAU y conservar candidatos y evidencia. No fusionar.

## Bitácora
- Inspección documental y visual realizada; clonada la rama del PR #34. Se detectó y resolvió la restricción de red del sandbox usando el mecanismo autorizado, sin cambiar proxy ni credenciales.
- Registrado inicio en memoria maestra, bitácora técnica y bitácora shrinkwrap de Drive. Captura local con coordenadas para delimitar cejas, frente y sienes.

## Resultados reales

Los tres candidatos son hermanos de v0.3, no descendientes entre sí. La cúpula nueva tiene 4097 vértices y 8064 triángulos. Se añade geometría al binario conservando intacto el bloque original; se sustituyen los índices de la banda defectuosa y los accesores de Craneo. r3 añade vértices de intersección a Cabeza sin mover sus vértices originales.

| Candidato | Frente | 3/4 | Perfil | Espalda | Evaluación |
|---|---:|---:|---:|---:|---|
| r1 | 99.18% | 98.70% | 96.63% | 99.18% | RECHAZADO: frente abultada, hueco sobre oreja; recorta 99 triángulos de región facial protegida y 14 de región de oreja. |
| r2 | 98.67% | 97.60% | 95.19% | 98.67% | RECHAZADO: frente más regular, pero hueco junto a ceja y fragmentos laterales; conserva facciones frontales, recorta 38 triángulos de región de oreja. |
| r3 | 98.73% | 97.96% | **94.78%** | 98.73% | NO APROBADO: conserva las dos regiones protegidas y cubre mejor la transición; quedan fragmentos laterales y costura visible, perfil bajo umbral. |

El IoU usa idénticas cámaras, encuadre, resolución y rasterizador contra **v0.3**, no contra una referencia artística aprobada. La silueta no mide identidad facial ni continuidad de superficie. No se selecciona r2 sólo porque supera el umbral: falla preservación y evaluación visual. r3 es la propuesta más conservadora de las facciones, pero tampoco se promueve.

### Cambios por iteración
- **r1:** reconstrucción elipsoidal guiada por radios de piel a la altura del borde; recorte superior conservador por triángulo. La transición rápida a la cúpula produjo un bulto. La máscara angular era demasiado estrecha en los extremos de las cejas. Se conserva como fallo documentado.
- **r2:** protección explícita de la región frontal (z > 0.155 m, |x| < 0.185 m, y < 0.775 m), frente más ancha, mezcla más gradual hasta y=0.94 y mayor cobertura lateral. Corrige el abultamiento y preserva los 1357 triángulos de esa región; la auditoría posterior descubre pérdida de triángulos en la región de oreja. Se conserva como rechazo.
- **r3:** protección adicional de orejas (triángulos que tocan |x| > 0.205 m, y < 0.712 m); contorno inferior angular revisado y recorte de polígonos con interpolación de atributos en la banda. De 1824 triángulos afectados por el recorte, 1624 salen completamente; los que cruzan el contorno se retriangulan. Se conservan los 1357 triángulos de facciones frontales y los 481 de región de oreja. Hay 3894 triángulos en Cabeza. Las placas residuales que cruzan la zona protegida no se eliminan a ciegas.

## Evidencia y verificación
- Por candidato: cuatro vistas de reposo y cuatro acercamientos de cabeza; cuatro vistas de Wave (0.6 s), Sit-pose (0.033333335 s), HeadShake (0.7 s) y Nod (0.55 s); acercamientos adicionales de HeadShake y Nod. Diez hojas PNG por candidato, incluyendo baseline, con SHA-256; **30 hojas / 120 paneles** en el paquete de evidencia. Se inspeccionaron visualmente las hojas de cabeza y poses. No son imágenes generativas.
- Render real de triángulos del GLB mediante z-buffer CPU, sombreado plano, Python/NumPy/Pillow. Poses evaluadas con skinning y SLERP de cuaterniones; todos los 783 samplers originales declaran LINEAR.
- **56 huesos y 29 clips** en cada candidato; nodos, skins, materiales y definición de animaciones idénticos. Bytes originales de buffers de animaciones e inverse bind matrices conservados. Tres muestras de cada clip (inicio, mitad, final): **87 muestras por candidato, 261 en total**, sin valores no finitos; cuerpo y posiciones originales de facciones coinciden con baseline en todas ellas.
- R3: atributos originales de Cabeza preservados como prefijo; comprobación explícita de pertenencia de cada triángulo protegido. No confundir conservar vértices con conservar triángulos: esa distinción descubre los fallos de r1/r2.
- Cúpula de los tres: sin triángulos degenerados, sin aristas no manifold; **128 aristas abiertas en el borde inferior**. Es una superficie abierta superpuesta a la cara, **no soldada ni estanca**. La auditoría no certifica el resto de la malla como manifold.
- Reproducción final de los tres candidatos: idéntica byte por byte. Script se niega a sobrescribir un destino existente y exige el hash exacto de v0.3.
- Se conservan los problemas heredados fuera de alcance (fragmentación de mandíbula/nuca, extremidades primitivas, gestos faciales sin morph targets). Conservar 29 clips no recupera blendshapes perdidos antes de v0.3.
- No se ejecutó Godot ni un barrido continuo de colisiones/autointersecciones. Las muestras discretas de poses no prueban todos los fotogramas.

## Entregables y reproducción
Modelos: `assets/maniqui/maniqui_v0_3_r1.glb`, `maniqui_v0_3_r2.glb`, `maniqui_v0_3_r3.glb`.
Herramientas nuevas: `reconstruir_v03.py`, `evaluar_v03.py`, `auditar_v03.py` en `tools/maniqui/`. Dependencias gratuitas: numpy, scipy y pillow. Trimesh se probó sólo durante el diagnóstico; no es dependencia del pipeline final. No se utilizó un adaptador game-dev porque el proyecto no incluye `.game-dev/adapter.json`; se empleó el rasterizador propio del proyecto.

Ejemplo desde la raíz, en un destino nuevo (el comando de generación no sobrescribe versiones):

```bash
mkdir -p /tmp/copox-revision
python tools/maniqui/reconstruir_v03.py assets/maniqui/maniqui_v0_3.glb /tmp/copox-revision/r3.glb /tmp/copox-revision/r3.json --iteration 3
python tools/maniqui/evaluar_v03.py assets/maniqui/maniqui_v0_3.glb /tmp/copox-revision/r3.glb /tmp/copox-revision/capturas
python tools/maniqui/auditar_v03.py assets/maniqui/maniqui_v0_3.glb /tmp/copox-revision/auditoria.json /tmp/copox-revision/r3.glb
```

Auditorías persistentes: `MANIQUI_V03_R{1,2,3}.json`, `MANIQUI_V03_R{1,2,3}_EVALUACION.json`, `MANIQUI_V03_AUDITORIA_CONTINUACION.json`. Capturas completas en el paquete de Drive enlazado abajo; no se versionan renders de iteración en Git, conforme a CLAUDE.md.

## Parada y siguiente método
Se alcanza el máximo autorizado de tres iteraciones. **PLATEAU, no continuar con una cuarta variante ni aprobar por métrica.** La siguiente intervención debe reconstruir una banda de topología conectada, identificando manualmente el contorno facial/auricular y soldándolo al cráneo; distinguir las placas adheridas a las facciones antes de recortarlas. La superposición paramétrica mejora cobertura, pero no resuelve la unión. Esta recomendación no implica que ya se haya ejecutado.

## Registro de cierre
- Evaluadas r1, r2 y r3 con capturas reales y poses; archivados también los rechazos.
- Validada reproducción binaria y conservación del rig/animaciones. Auditoría de triángulos detectó regresiones de r1/r2; r3 conserva las regiones protegidas pero no supera todos los criterios.
- Se mantienen el PR #34 en borrador y las versiones anteriores intactas. No se cambia main, no se activa loop ni servicio de pago.

### Archivo físico de evidencia en Drive

[Descargar paquete de tres iteraciones](https://drive.google.com/file/d/1qn3U81XXWgrbXLr21w-ic7lgRbTIaKnX/view?usp=drivesdk). Subido a COPOX/SHRINKWRAP BETA-GAMMA, 17,224,658 bytes; SHA-256 `27e14af9b2e05d14c5883574b6ffabe831d4c77dd2767c6f6fe4cf566f15b6e3`. Incluye 53 archivos: 30 hojas PNG (120 paneles), tres GLB y herramientas/auditorías/manifiesto. La copia de este reporte dentro del ZIP es el corte anterior a añadir este enlace, para evitar autorreferencia del hash. No se alteró organización ni permisos de archivos previos.

### Estado de publicación
Cambios de modelos/código/auditorías preparados en commit local `afc268b`. **Push pendiente**: la revisión automática rechazó publicar este paquete en el repositorio público sin una autorización explícita adicional de divulgación. No se intentó otra vía para publicarlo. Las tres bitácoras de Drive registran resultados, rechazos y este bloqueo; el ZIP privado está subido y verificado. PR #34 permanece sin estos commits hasta recibir autorización. Esta nota no equivale a publicación ni a aprobación artística.
