# G2-C4 · continuación del 15 de octubre de 2026

**Sin aprobación: B2 se conserva; A3, C2 y C3 se rechazan. No hay ABC.**
Se ejecutó la continuación autorizada por «Continua», siempre desde V3
SHA256 `0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b`.
Se alcanzó el máximo de tres ensayos para A y C; B tiene dos.
El PR47 sigue experimental y no se fusiona. No se modifica la rama de
otros trabajos ni se sustituye ningún modelo anterior.

## Cambios reales y decisiones

| Candidato | Edición exportada | Comprobación | Decisión |
|---|---|---|---|
| A3 | Retira las 156 caras de pelo confirmadas; añade 214 vértices y 445 caras de piel lateral | 31 cruces con geometría retenida; se conservan exactamente los 5087 vértices, atributos y 10008 caras originales de Craneo | Rechazado: pliegues y unión incompleta detrás de la oreja |
| C2 | Modifica 40 índices/31 posiciones de la mandíbula (66 caras afectadas), máximo 15,35 mm; sustituye 360 caras de transición por 380 vértices/608 caras | 78 cruces: 71 con torso y 7 con cuatro caras laterales de Cabeza | Rechazado |
| C3 | Misma edición mandibular localizada desde V3; transición de 340 vértices/544 caras y anclaje posterior más bajo | Un cruce restante: Cabeza 1637 contra transición 60; cero cruces con torso | Rechazado: banda inferior angular, discontinuidad lateral y cruce sin resolver |

B2 sigue con SHA256 `daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec`.
No se retiran indiscriminadamente caras en conflicto para forzar una
métrica. Las orejas, ojos, nariz, labios y partes superiores de la cara
permanecen geométricamente intactas. A3 no mueve ningún vértice anterior.
C2/C3 modifican sólo los 40 índices enumerados de Cabeza y la primitiva
Cuello, precisamente la transición inferior objeto del ensayo. No cambian
X/Z de la mandíbula ni los vértices de calva/nuca. Las caras antiguas del
cuello quedan archivadas en el prefijo binario original, sin uso activo.

En C3 se observa una mejora del borde anterior frente a los dientes de
V3, pero el perfil revela una banda plana/angular separada lateralmente.
Eso impide declarar una reconstrucción anatómica conseguida. A3 rellena
parte del hueco derecho pero deja pliegues/solapamientos. Los rechazos
son geométricos y visuales; no se presentan como trabajo aprobable.

## Anillo experimental, no unión validada

C3: 68 puntos, centro `(0, 0.527493364, 0.017551704)` m; normal
`(0, 0.988012065, 0.154376682)`, perpendicular al eje Neck→Head real.
Semiejes 0,064 m lateral y 0,050 m anteroposterior. Índices locales
272–339 de la nueva primitiva Cuello. Anillo abierto, sin tapa. C2 tiene
76 puntos y centro más bajo `(0, 0.516625231, 0.015853560)`.
Los parámetros son un perfil explícito de V3, no proporciones universales.

El borde exterior usa puntos medidos de Cabeza y Craneo; son costuras
espaciales entre primitivas, **no una soldadura topológica global**. Hay
aristas de conexión lateral sin superficie histórica coincidente. Por
eso el anillo existe como experimento, pero no queda listo para conectar
un cuello animable sin más reparación. La topología de la banda aislada
no tiene degenerados ni aristas non-manifold; eso no resuelve sus uniones.

## Validación exportada y Godot

El auditor relee los GLB exportados: SHA, prefijo binario, materiales,
nodos, skin, 56 huesos y 29 definiciones originales conservados; malla
facial y morph targets históricos exactos. Todos los pesos son finitos,
no negativos, suman 1 y usan joints válidos. Los pesos nuevos se obtienen
de los anclajes y la mezcla real Neck/Head, no se descartan al retopologizar.
Ninguna inversión de las caras originales modificadas ni caras degeneradas
nuevas. A3 conserva cada atributo antiguo de Craneo como prefijo exacto.

Godot **4.7.2.stable.official.ed1daf0bf**, OpenGL Compatibility, Mesa
llvmpipe/Xvfb. 141 capturas reales nuevas y 16 láminas. Cada modelo V3,
B2, A3, C2 y C3 tiene 13 vistas/detalles y 12 capturas de poses; cada
candidato tiene cuatro vistas sólo de triángulos editados. Cámaras,
escala e iluminación equivalentes. La máscara A3 muestra caras retiradas
y añadidas; C muestra caras mandibulares modificadas y la nueva transición.

725 muestras (29 clips × cinco tiempos × cinco modelos): poses de los
56 huesos iguales a V3, vértices deformados finitos y posiciones/normales
del cuerpo protegido iguales. El cotejo del cuerpo en esta campaña
abarca superficies 3 en adelante; la superficie 2 cambia deliberadamente
en C. Las poses representadas son Nod, HeadShake, Wave y Sit-pose.

Los maestros, incluida V3, siguen fallando la importación directa con
error 43. Sólo las copias `_compat.glb` importan (24 superficies). Se
mantiene la limitación heredada: 14 clips con movimiento esquelético y
15 clips faciales sin pistas utilizables. No son 29 animaciones funcionales.
El saneador omite primitivas vacías/canales huérfanos en las copias, sin
restaurar la geometría de expresiones ausente ni alterar los maestros.

Khronos: 53 errores en cada maestro y 31 en cada copia compatible. Avisos
V3/B2/A3: 182/181; C2/C3: 2/1. Los 180 avisos menos proceden de sustituir
el cuello histórico y no prueban aceptación geométrica: los cruces y la
revisión visual siguen rechazando C. Informes íntegros en `khronos/`.

Los filtros geométricos corrieron antes de Godot. Los candidatos rechazados
se renderizaron únicamente para aportar evidencia comparable del rechazo,
no porque hubieran pasado el filtro. El detector cubre cruces propios de
triángulos nuevos/modificados contra el resto en reposo; excluye contacto
por vértices coincidentes y no certifica solapamiento coplanar ni todos los
instantes de animación. Los defectos históricos fuera de región se registran,
no se exige una cabeza globalmente manifold.

## Registro de depuración

La Delaunay sin restricciones perdió seis aristas del contorno de A3;
se abortó antes de exportar. Se sustituyó por triangulación de contorno
por recorte de orejas, inserción de puntos y flips internos controlados.
Un caso cóncavo de escala grande detectó oscilación numérica de flips;
se agregó tolerancia relativa. Se verificó área, rechazo de contornos
cruzados y reproducción **byte por byte del A3 ya exportado** después del
arreglo. No se alteró ni sobrescribió el candidato publicado como evidencia.

Todos los generadores rechazan sobrescribir un GLB existente. No hay cuarta
iteración de A o C. El bloqueo restante está localizado y documentado,
pero la preparación craneofacial completa sigue pendiente.
