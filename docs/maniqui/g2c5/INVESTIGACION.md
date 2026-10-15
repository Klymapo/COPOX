# G2-C5 · Huecos faciales y recuperación de nariz

Orden del usuario: «Rellena los huecos y recupera la nariz». Nueva campaña
localizada tras el cierre de A/C de G2-C4. Existe una campaña G2-C5 previa en
Drive (14-oct: combinaciones conservadora y óptica, ambas SIN APROBAR); esos
GLB no se modifican. R1-R3 son pruebas independientes de recuperación facial
para aislar la nariz, no los sustituyen ni pretenden combinarlos. No continúa
un rechazo de cara como padre.
Base inmutable G2-C3 V3, SHA256
`0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b`.
Se reaplica la selección B2 de 71 caras de gafas confirmadas; ningún
candidato A3/C2/C3 aporta geometría. Se preservan sus archivos históricos.

## Diagnóstico y técnica

El generador histórico maniqui.py clasificó lentes por proximidad a una
plantilla de gafas Beta (radio 14 mm). Esa selección retiró también caras
de piel cercanas a la montura. La nariz conserva la punta, pero tiene
bordes abiertos y falta de continuidad hacia el puente nasal y las mejillas.
Se inspeccionan las caras reales de GammaHead de Delta como referencia
anatómica/geométrica, nunca como sustituto de V3 ni de su calva/nuca.

Primero se recuperan triángulos originales ausentes, limitados a la cara,
identificados mediante geometría, conectividad y múltiples muestras de
textura de piel. Se reutilizan posiciones, normales y pesos originales
sólo si son compatibles con el skin y pose de bind de V3. Coincidencias
exactas se reutilizan por atributos; no se fusionan costuras de normales.
Se excluyen montura y las 71 caras eliminadas en B2 por firma geométrica.
La resta de caras actuales evita duplicados. Después se evalúan los
bordes abiertos restantes para interpolación localizada de piel y puente
nasal, conservando los bordes anatómicos de ojos, labios y nariz.

No se rellenan cavidades funcionales de ojos/boca ni se tapa arbitrariamente
la futura unión inferior del cuello. No se rehace la calva/nuca. Las zonas
que no puedan cerrarse sin invadir regiones protegidas se documentarán.
Como máximo tres candidatos hermanos en esta campaña nueva; no promoción
con fallos geométricos o visuales.

## Verificación

SHA de V3, triángulos restaurados y procedencia, límites de selección,
atributos y morphs protegidos, caras degeneradas, cruces regionales y
conectividad. Evaluación sobre GLB exportado en Godot 4.7.2, mismas cámaras,
escala y luces que V3/B2, vistas de nariz/ojos y poses. Conservar 56 huesos,
29 definiciones originales y declarar las limitaciones de los 15 clips
faciales vacíos heredados; no confundir compatibilidad con conformidad glTF.

Referencias: tools/maniqui/maniqui.py (clasificador histórico),
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html,
triangulación restringida y auditor de cruces locales ya documentados en
G2-C4. Sólo numpy/scipy/Pillow, Godot y herramientas gratuitas del repo.
El CLI opcional game-dev no está instalado; se usa el pipeline local existente.

## R2 · Interpolación de los huecos medidos

R1 recuperó 271 caras de piel, pero Godot muestra todavía huecos junto a
nariz y debajo de ojos. Cuatro cruces: tres caras restauradas contra la
calva preservada y un cruce entre dos caras de la propia referencia.
R2 parte otra vez de V3+B2 y omite las cuatro caras fuente en conflicto
(2826, 3781, 3782, 3784); no deforma la calva para admitirlas.

Se recorren medias aristas de la malla por abanicos de caras, separando
ciclos en vértices de contacto. Se seleccionan contornos de huecos frontales
con orientación interna. No se usa «rellenar todo»: se excluyen cavidades
oculares posteriores, contornos exteriores y aberturas mandibulares.
La carta XY fija los bordes reales y la profundidad Z se interpola
armónicamente con triangulación restringida. Los anclajes existentes
no se mueven; sólo se añaden caras y, donde hace falta, vértices interiores.
Cada parche pasa un filtro de cruces contra todo el modelo antes de
admitirse en el candidato. Se documentan los contornos no triangulables.
Shapely 2.1 se usa sólo para validar contornos en plano; numpy/scipy para
interpolación. https://shapely.readthedocs.io/en/stable/reference/shapely.is_valid.html


## R3 · Contornos plegados y relleno restringido

R2 cerró 13 contornos pero creó cinco aristas non-manifold nuevas: sus
diagonales coincidían con aristas de caras plegadas existentes. Se rechaza.
Los dos huecos mayores no admiten una carta frontal simple por cruces
en su propio borde. El tercer candidato vuelve a V3+B2, conserva las
267 recuperaciones compatibles y resuelve el dominio de relleno planar
como polígonos válidos menos la proyección de las superficies frontales
retenidas. Eso protege la forma visible de ojos, párpados, cejas y nariz.
La triangulación restringida de GEOS/Shapely respeta agujeros interiores;
la profundidad de borde se obtiene de aristas geométricas reales y la
interior por interpolación armónica. Puntos nuevos sobre aristas generan
costuras geométricas/T-junctions explícitas, no una soldadura global.
Cada triángulo nuevo se contrasta contra la geometría retenida, se excluyen
cruces y duplicados, y se impide aumentar aristas non-manifold. Las exclusiones
se cuentan como posibles zonas pendientes, no como «relleno total» automático.
Referencia: shapely.constrained_delaunay_triangles / GEOS constrained Delaunay.


R2 results: 267 exact skin triangles, 251 triangles over 13 projected holes,
206 added vertices; zero proper crossings, but six spatially welded
non-manifold edges were introduced by triangulation edges coinciding with
pre-existing folded triangles. Godot still shows large gaps at the nose and
eye/cheek. R2 is rejected. R3 must subtract the projection of every retained
front-facing skin/eye triangle before triangulation and protect the existing
eye islands. It is the last candidate in this three-sibling campaign.

## R3 · Auditoría geométrica y estado de evidencia

R3 recupera 267 caras de piel fuente y añade 81 triángulos repartidos en once
parches; añade 136 vértices, modifica cero vértices originales, no registra
cruces propios y mantiene el recuento de aristas non-manifold en 1. Deja 16
contornos protegidos junto a las cavidades oculares, 16 límites sin anclaje a
superficie retenida, 2 sin área visible ausente y rechaza 1 parche por cruce.
SHA256 del GLB: `05774f8177155dc3a742a77776649357b15f58ce29b2e4d7e3689c872dfd7b95`.
La validación Khronos de R3 da el mismo recuento que V3/B2: 53 errores y 182
avisos en el GLB original, 31 errores y 181 avisos en la copia de
compatibilidad; no introduce incidencias nuevas según esos contadores.

R1/R2/R3 no se promocionan. Las capturas anteriormente presentes en los
directorios `captures_v3/R1..R3` no son evidencia válida: una versión del
guion usó los nombres históricos de G2-C4 y no recorrió los candidatos G2-C5.
Se corrigió el generador, pero la repetición real quedó bloqueada por el
servidor gráfico local: `/tmp/.X11-unix` pertenece al usuario del contenedor y
Xvfb requiere propietario root; el cambio de propietario fue rechazado por
el sistema operativo. Godot headless tampoco entrega `frame_post_draw` para
esta captura y se canceló al vencer el plazo. Por tanto no hay capturas
Godot 4.7.2 nuevas ni aceptación artística de la nariz/huecos. Las capturas
antiguas quedan conservadas sin atribuirlas a estos modelos. El siguiente
paso debe reabrir la captura con un servidor gráfico disponible y evaluar el
resultado antes de cualquier combinación o promoción.

## Revisión visual real de los GLB (Blender 4.3.2)

Para no confundir la limitación de la pantalla de Godot con una revisión
artística, importé las copias compatibles V3, B2, R2 y R3 desde sus GLB y
rendericé 36 vistas en Blender EEVEE con la misma cámara, materiales y luces:
seis ángulos, rostro, nariz y ojos. Las vistas están en
`build/g2c5/blender_captures_final/` (V3/B2/R3) y
`build/g2c5/blender_captures_r2/R2/`.

R2 produce líneas triangulares nuevas cerca de cejas/ojos y conserva huecos.
R3 añade una franja pequeña y mejora parcialmente el puente, pero aún deja
huecos oscuros grandes debajo y junto a ambos ojos; la nariz conserva una
forma de bloque y no tiene continuidad suave de puente. **R2 y R3 se rechazan
artísticamente**, aunque R3 pase el filtro geométrico inicial. No entrego
ninguno como solución completa; quedan preservados como experimentos.
Godot no generó imágenes; los renders Blender no se atribuyen a Godot.

La comprobación de Godot 4.7.2 en modo headless sí importó las copias de
compatibilidad de V3, B2 y R3 (error 0); el GLB original mantiene el error
43 por los accessors vacíos históricos. R3 expone 56 huesos, 24 superficies,
29 clips y 145 muestras de matrices; éstas coinciden con V3. Se observa
movimiento óseo en 14 clips. En 15 no se observa movimiento óseo, consistente
con los canales faciales vacíos heredados. La comprobación de skinning queda
inconclusa: Godot informó que las instancias no tenían el skin registrado con
un esqueleto válido y por ello se hornearon 0 vértices. No se declara que la
deformación esté validada. Informe detallado en `VALIDACION.json`.
