# G2-C7 · Resultado experimental de likeness

Fecha: 2026-10-15. Base L1, no aprobada, SHA256
`cf759292adace095b0a0c41516e0ecebead3cb48efb44210afcbbef8cc8d71e0`.
Se conservan V3, B2, L1, G2-C4/G2-C5 y el candidato rechazado V1.

| Región / criterio | L1 → V2 | Evaluación |
|---|---|---|
| Ojos y cejas | 674 triángulos emparejados exactamente con Delta reciben UV originales del atlas GammaHead; iris marrón, esclerótica y cejas recuperan lectura. | Mejora local visible en frontal y pose Wave. |
| Piel y calva | Tono de piel mediano muestreado del atlas para 2.081 triángulos de cara, casquete liso y cuello; cero vértices de la calva movidos. | Elimina el gris neutro; no corrige la unión de superficies. |
| Nariz, mejillas, mandíbula | Geometría idéntica por triángulo a L1. | FAIL artístico: huecos, bandas y aristas visibles. |
| Perfil, cuello, hombros | Geometría idéntica a L1. | FAIL artístico: separación lateral grande. |
| Brazos, manos, piernas, pies | Geometría idéntica a L1; conserva unión de tobillos. | Sin avance anatómico nuevo; formas tubulares y pies ovalados. |

V1, SHA256 `33e3db757a97eadcf55407cb6063c5b88eb0c771bd0e9dc5928ba56c5488d28a`,
queda **rechazado**: textura amplia provoca parches negros de pelo/lentes en
orejas, mandíbula y mejillas. V2, SHA256
`0efe44e912a23c2dfae2be850494d7e8a93475606af5e08ba49e69e536daed63`,
es **mejora local de rasgos, SIN APROBAR como modelo final**. Se generaron
0 triángulos geométricos nuevos y se movieron 0 posiciones desde L1; el
particionado en una superficie extra preserva exactamente las esquinas,
normales, pesos y huesos originales. Su aspecto frontal mejora; el criterio
de reconocer inmediatamente la identidad global **no se cumple**.

## Comprobaciones

- Todas las 24 primitivas de L1 preservan exactamente sus triángulos
  geométricos en V2; la cara se divide sólo por material. Ningún cruce o
  hueco geométrico nuevo puede proceder de mover vértices: no se movió ninguno.
  Los huecos y cruces históricos siguen sin resolver.
- Godot 4.7.2 headless: la copia de compatibilidad de V2 importa con error 0,
  56 huesos, 25 superficies (una extra por atlas), 29 definiciones de clip y
  145 muestras de matrices óseas idénticas a L1. El GLB bruto hereda error 43
  por accesores vacíos. No se declaran funcionales los 15 clips faciales con
  morphs huérfanos ni se certifica deformación completa por skinning.
- Validador Khronos bruto: 53 errores, 182 avisos, 179 informativos tanto en
  L1 como en V2; sin aumento. Esos errores son una limitación real de la
  fuente, aunque Godot importe la copia compatible.
- Blender 4.3.2 importó los GLB y produjo capturas reales de Gamma/L1/V2:
  cuatro vistas, tres cuartos, rostro, nariz, oreja, mandíbula, cuello, manos,
  pies y `Wave` fotograma 24. Las láminas `COMPARATIVA_4_VISTAS_REAL.png`,
  `COMPARATIVA_REFERENCIA_ROSTRO_REAL.png` y
  `COMPARATIVA_DETALLES_REAL.png` contienen esos renders y la foto maestra
  etiquetada como perspectiva. No son capturas Godot ni se atribuyen a IA.

## Siguiente mejora recomendada

Una campaña **geométrica independiente** debe registrar Gamma y V3 mediante
landmarks faciales antes de intentar un donante de piel. Hay que retopologizar
mejillas/puente/mandíbula como superficies continuas con anillos y atributos
transferidos, conservando ojos, cejas, orejas y calva. El desacuerdo espacial
Gamma–Delta medido de ~7,8 mm aun tras traslación simple veta injertar
triángulos directamente. Después se puede diseñar una unión cuello-clavícula
comprobada en poses `Nod`/`HeadShake` y refinar miembros. No se promueve la
baseline ni se fusiona ninguna rama sin la revisión visual del usuario.
