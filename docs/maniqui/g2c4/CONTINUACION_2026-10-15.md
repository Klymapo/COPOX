# Continuación autorizada · 15 de octubre de 2026

PR47 sigue en borrador, head 320b322. B2 y todos los ensayos anteriores
permanecen inmutables. Se continúa por petición expresa «Continua».

## Research brief: superficie lateral anclada

La eliminación de pelo no basta: hay un vacío entre el borde lateral
real de Craneo (Y=.672) y la inserción posterior de la oreja. Se propone
un parche lateral nuevo anclado a los vértices EXISTENTES del borde de
Craneo y a posiciones del borde retenido de Cabeza, sin mover ninguno.
Es una adición localizada a la superficie faltante, no una remodelación
de la calva/nuca existente. Los 5087 vértices y 10008 caras originales de
Craneo deben conservarse exactamente como prefijo. La oreja y todos los
atributos de Cabeza permanecen intactos salvo índices del pelo probado.

Se usa carta lateral 2D, contorno medido, triangulación Delaunay sujeta a
validación de todas las aristas del contorno e interpolación armónica de
la coordenada X. No se usa simetría ni un elipsoide supuesto. Pesos y
normales se transfieren desde anclajes reales. El parche debe evitar
cruces propios, no invertir normales y cerrar visualmente el vacío.

Referencias: scipy.spatial.Delaunay y scipy.sparse.linalg.spsolve;
https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html

A3 será el tercer y último ensayo de A. Si no cumple conectividad o
intersecciones regionales, se rechaza sin consumir una cuarta versión.
Para C se medirán contornos y el cuello existente antes de emitir un
nuevo GLB. Ningún rechazo se usa como padre.

## Research brief C2: transición anular inferior

El cuello heredado es una manga de 216 vértices/360 caras y 36 puntos
por borde, con un borde superior de 34 cm de ancho que se solapa con
la mandíbula. C2 estudiará sustituir exclusivamente esa transición por
una superficie inferior abierta en el cuello, anclada al contorno real
mandibular anterior y al borde inferior existente de la nuca. La calva
no se deforma. Se conserva la primitiva y su material; los datos antiguos
permanecen en el binario, pero sus índices dejan de estar activos en C2.

El contorno anterior se obtiene del grafo de aristas libres de Cabeza,
con extremos medidos. Su altura se curva de forma localizada para reducir
los dientes del borde, conservando X/Z, labios y caras superiores. El
anillo interior se orienta perpendicularmente al eje Neck→Head del rig;
centro y semiejes se registran como perfil de V3, no regla universal.
Los nuevos pesos se interpolan entre el peso real del borde y la mezcla
Neck/Head del cuello existente. No hay cierre central ni tapa.

Referencias: contrato glTF JOINTS_0/WEIGHTS_0, especificación Khronos;
interpolación lineal de pesos normalizados y construcción de tiras de
cuadriláteros trianguladas. Filtros: inversión, cruces con toda la geometría
retenida, contorno libre único interior, costuras espaciales y poses.
Si las uniones a las superficies históricas se cruzan, C2 se rechaza.

C2 se rechaza: 71 cruces con el torso y 7 con cuatro triángulos laterales
de Cabeza. C3, último hermano desde V3, cambia únicamente el perfil de
anclaje del anillo: centro 26 mm sobre Neck a lo largo del eje hacia Head,
y arco de nuca existente 5041–5077 (más bajo), conservando todos esos
vértices. Esta reducción del arco evita intentar envolver los fragmentos
laterales superiores. La banda anterior y la operación se mantienen.
No se eliminan las cuatro caras en conflicto: se evalúa primero si el
nuevo recorrido puede respetarlas. El resultado se acepta o rechaza
con los mismos filtros, sin crear un cuarto candidato C.

Resultado: la Delaunay inicial se sustituyó por triangulación restringida
(recorte de orejas, inserción de puntos y flips internos), con contorno
exacto. A3 se rechazó por 31 cruces. C2/C3 se rechazaron por 78/1 cruces
y la unión inferior angular/discontinua. Ver continuacion_2026-10-15/RESULTADO.md.
