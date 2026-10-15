# G2-C4 · investigación y contrato regional

Base inmutable: PR46, commit 1869c51, SHA256
0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b.
Recuperada del artefacto 11924734007 de Actions 38629644236.
Coordenadas glTF: metros, Y arriba, +Z delante. No usar mm/Z-up ALTH.

## Hipótesis y método

A: el saliente derecho pertenece a Cabeza, no Craneo. La isla principal
contiene 2704 caras: no eliminar una isla completa. Recuperar procedencia
por firma de tres posiciones de triángulo contra GammaHead de Delta.
La textura de origen distingue pelo marrón de piel, pero se exige también
localización posterior derecha, continuidad y revisión visual. Ninguna
selección por espejo de la oreja izquierda. Sólo cambiar índices.

B: la selección por distancia de G2-C2 no prueba gafas. Recuperar textura
por correspondencia exacta, revisar montura frente a iris/párpados/nariz.
Las selecciones ambiguas no se eliminan. Preservar todas las posiciones,
atributos y targets; evaluar resultado aunque la limpieza resulte parcial.

C: inspeccionar el borde real inferior y las conexiones existentes antes
de añadir una transición. La primitiva Cuello existente alcanza Y=.5901
con ancho .3415: una abertura nueva no puede darse por válida sin evaluar
su intersección con esa pieza. Ningún cambio a Craneo o a facciones.
Técnica posible: reconstrucción restringida del contorno inferior y anillo
abierto, basado en borde y articulación Neck medidos; rechazar si la unión
queda ambigua o necesita invadir regiones protegidas.

## Referencias y límites

Código de procedencia: tools/maniqui/maniqui.py; identidad de triángulos
medida contra assets/alastor_delta/alastor_delta_v1_1_cuello.glb.
Lectura glTF2: índices referencian atributos comunes; apéndice binario evita
alterar animaciones/skins. Referencia: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
Godot GLTFDocument: https://docs.godotengine.org/en/stable/classes/class_gltfdocument.html

La malla facial animable histórica tiene 16 targets pero cero índices;
los 29 clips nominales no demuestran expresiones funcionales. Comparar
huesos y deformaciones reales, y separar copia de compatibilidad Godot de
GLB maestro que conserva todas las definiciones originales.

## Registro

2026-10-14: rama experimental aislada, SHA base verificado. Godot4.7.2
oficial ed1daf0bf descargado. A/B/C se generarán desde la misma V3; sin
promoción automática, fusión ni eliminación. Experimentos NP previos
permanecen intactos en otro worktree, fuera de esta línea de trabajo.
