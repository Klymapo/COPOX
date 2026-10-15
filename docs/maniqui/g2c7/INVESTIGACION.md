# G2-C7 · Investigación de likeness y regiones

Fecha: 2026-10-15. Referencia maestra del Detective/Alastor:
`refs/personajes/detective.jpg`; contexto de AlasTheo:
`refs/escenas/detective-y-joven-rubio-estudio.png`. Para el lenguaje de
formas chibi-soft y cuatro vistas de Theo: `refs/personajes/joven-rubio-4-vistas.jpg`
y `refs/infografias/hoja-de-vistas-personaje.png`. La referencia individual de
Alastor manda sobre Theo para edad, masa, rostro y proporciones. El requisito
previo de calva sin gafas impide copiar pelo o montura aunque sean señales
icónicas de la imagen original.

Se inspeccionaron los GLB Gamma (30k triángulos), Delta (rig de 56 huesos y
29 clips), Theo Alpha (sin rig, 0,11 m), V3, B2, R1–R3 rechazados y L1.
Gamma se renderizó realmente en Blender en cuatro vistas; L1 y los candidatos
G2-C7 con las mismas cámaras/luces. Gamma es referencia de apariencia, no
donante automáticamente compatible: cero triángulos coinciden exactamente
por firma geométrica con Delta; en región facial la mediana de distancia
Gamma→Delta es aproximadamente 11 mm sin alineación y 7,8 mm con una simple
traslación de prueba. Ese desplazamiento impide injertarlo de forma segura
sin registro anatómico, pesos y pruebas de intersección nuevas. Theo Alpha
tampoco es donante de rig/escala. Los scripts faciales G2-C5 ya agotaron tres
intentos de restauración/relleno y no se vuelven a usar como padres.

## Cinco defectos visuales de mayor impacto, por prioridad

1. **Cara y nariz:** pérdida de piel bajo y entre los ojos, puente nasal y
   mejillas; sombras de fondo atraviesan el plano facial. En L1 los ojos
   grises no muestran además el iris marrón característico. Es el mayor
   bloqueo de likeness facial.
2. **Perfil craneofacial y mandíbula:** la calva lisa se lee como una esfera
   separada de una cara baja y angulosa. El contorno inferior tiene picos y
   partes sin continuidad; difiere de la mandíbula ancha pero suave del
   Detective de referencia.
3. **Cuello/nuca/hombros:** existe una discontinuidad lateral visible entre
   mandíbula, cuello y torso. Una pose de cabeza puede exponerla más; ningún
   render en reposo la valida como unión animable.
4. **Cuerpo y articulaciones:** torso y miembros aún se leen como tubos o
   piezas superpuestas, lejos de la masa y la ropa estructurada de la
   referencia. L1 sí cerró visualmente el hueco pierna/zapato.
5. **Manos, pies y detalles:** manos finas con empalmes visibles, pies ovalados
   sin talón claro y ausencia de los pliegues formales del lenguaje AlasTheo.

La altura del maniquí L1 es 0,963 m y la porción craneal aproximada 0,427 m:
unas 2,26 cabezas. La relación global se aproxima a la intención de dos
cabezas, pero la semejanza de silueta global no prueba fidelidad del rostro.
La referencia original está en perspectiva, con pelo, gafas y abrigo; no se
calcula un porcentaje de likeness a partir de sus píxeles.

## Cassette regional experimental

Foco de esta campaña: **rasgos visibles de ojos/cejas y piel**. Baseline de
todos los ensayos: L1 SHA256
`cf759292adace095b0a0c41516e0ecebead3cb48efb44210afcbbef8cc8d71e0`.
V1 y V2 son hermanos de L1, no se encadenan. A partir del atlas original
GammaHead retenido en el GLB y de triángulos Delta emparejados exactamente,
se restauran UV sólo cuando la procedencia es inequívoca. Se congelan
posición de triángulos, pesos, rig, jerarquías y animaciones. Los auditores
regionales son: integridad por esquina de triángulo, reproducción de UV,
lectura frontal de ojos/cejas, ausencia de manchas negras nuevas, revisión
de perfil, Godot y comparación real de GLB exportado. Cualquier FAIL veta
la promoción global. No hay cassette productivo de maniquí en
`copox/cassettes/enabled/`; este ensayo usa la semántica de hermanos y
auditoría COPOX de modo experimental, sin ejecutar ni fingir una promoción
del engine.

V1 transfiere ampliamente 1.245 caras de textura original y revela parches
negros de pelo/gafas alrededor de orejas y mandíbula: rechazo artístico
temprano. V2 usa una selección medida de 674 triángulos de ojos/cejas y
piel uniforme del propio atlas para el resto. Se revisa por región y no se
propone como solución de agujeros/mandíbula/cuello. Sin tercer ensayo por
inercia si la limitación restante exige una nueva topología y registro de
Gamma que esta campaña no puede validar.

Fuentes: `copox/README.md`, `docs/COPOX_LOOP_ENGINE.md`,
`assets/references/characters/detective/README.md`,
`assets/references/characters/theo/README.md`,
`docs/maniqui/g2c5/INVESTIGACION.md`.
