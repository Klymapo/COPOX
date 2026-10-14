# COPOX G2-C4 · resultados experimentales, sin aprobación

Se recuperó V3 exacta de Actions 38629644236 / artefacto 11924734007.
SHA256: `0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b`.
Referencia: PR #46, commit `1869c51e8994987bddc423e9cce679fdfd8b355f`.
Todos los ensayos parten de esta misma V3. No se modificó V3, no se usó r3
como resultado final, no se fusionó ni se sustituyó ningún modelo anterior.

## Resultado por región

| Ensayo | Operación real | Resultado |
|---|---|---|
| A | 156 triángulos de pelo derecho retirados | RECHAZADO: aparece hueco detrás de oreja |
| A2 | 63 triángulos superiores retirados, desde V3 | RECHAZADO: hueco y saliente restante |
| B | 61 triángulos de montura retirados | PARCIAL: diez residuos adicionales identificados |
| B2 | 71 triángulos de montura retirados, desde V3 | Limpieza regional conservada para revisión; bloqueo global heredado |
| C | 40 vértices / 31 posiciones espaciales inferiores ajustadas | RECHAZADO anatómicamente: contorno aplanado, sin anillo ni unión de cuello válida |

**No se generó ABC.** A y C no pasan; B2 permanece disponible por separado.
Dos iteraciones de A, dos de B, una de C. No se continúa por inercia.

## Identificación y conservación

La primitiva Cabeza de V3 contiene 2826 caras. La isla principal contiene
2704. El pelo derecho está conectado a esa isla: repetir el rapado aislado
izquierdo no era seguro. Se midió X [0.155798,0.233212], Y
[0.570969,0.728220], Z [-0.140807,-0.013632] para A. La eliminación revela
que no existe una superficie continua detrás; una piel nueva exige una
reconstrucción regional distinta del simple rapado.

La referencia texturizada Delta se usó exclusivamente como evidencia de
procedencia, no como nueva base. Coinciden exactamente, a 1 micrómetro,
2617 triángulos de V3; todos los triángulos retirados tienen referencia
exacta. Se inspeccionaron tono de textura, situación y conectividad. El
pelo marrón difiere de la oreja; la montura azulada/neutral difiere de iris,
párpados, cejas y nariz cálidos. Los diez restos añadidos a B2 son brazos
y segmentos inferiores de la montura revisados individualmente. Las
coordenadas y IDs son un perfil específico de V3, nunca una regla para
otros personajes. `selecciones_v3.json` y cada informe enumeran las caras.

A/A2/B/B2 sólo cambian índices. C cambia POSITION y NORMAL únicamente en
los vértices inferiores seleccionados: X [-0.158005,0.160109], Y
[0.535870,0.556751], Z [-0.004762,0.200881]. Desplazamiento máximo
0.010733 m. Se conservaron X/Z y la topología. El error del ajuste de
altura baja de 0.004448 a 0.000445 m, pero eso no prueba anatomía adecuada.
La inspección inferior y frontal rechaza C como preparación del cuello.

En todos: buffer binario original conservado como prefijo exacto; nodos,
materiales, skin, 56 huesos, 29 definiciones de animación, targets y malla
facial histórica idénticos. Craneo, nuca, Cuello y cuerpo íntegros. No se
movieron orejas ni ojos; ninguna nueva cara degenerada ni inversión.
A/B no pueden crear intersecciones entre triángulos retenidos porque sus
posiciones no cambian. C: cero cruces propios nuevos en los pares regionales
probados en reposo; no equivale a una prueba continua de colisiones.

## Godot y validador: limitaciones reales

Motor oficial **4.7.2.stable.official.ed1daf0bf**, OpenGL Compatibility,
Mesa llvmpipe y Xvfb, todos gratuitos. El GLB maestro V3 falla al importar
(error 43), igual que los cinco ensayos, por datos históricos vacíos.
Las copias `_compat.glb`, derivadas por el saneador documentado del repo,
importan: 56 huesos, 24 superficies y 29 nombres de clips.

**No son 29 animaciones funcionales.** Hay 14 clips con pistas esqueléticas
y 15 sin pistas utilizables. La malla facial original contiene 16 targets
pero cero caras visibles. El saneador omite diez primitivas vacías y quince
canales huérfanos sólo en las copias de compatibilidad; los maestros
conservan todas las definiciones y bytes originales. Ninguna expresión
facial funcional se declara reparada.

Se muestrearon cinco tiempos de cada clip en seis modelos: 870 muestras.
Huesos iguales a V3 y vértices deformados finitos. Posiciones y normales
del cuerpo deformado coinciden exactamente con V3 en cada muestra. Hay capturas reales de
Nod, HeadShake, Wave y Sit-pose. Esto no certifica todos los instantes ni
las colisiones durante movimiento. Los huecos de cuerpo/cuello visibles
en las poses son históricos y no se encubren.

Khronos glTF Validator 2.0.0-dev.3.10: cada maestro, incluida V3, registra
53 errores y 182 avisos; cada copia compatible, 31 errores y 181 avisos.
No aumentan errores ni avisos; sí quedan accessors antiguos sin uso como
información por la edición conservadora. **Importar en Godot no implica
conformidad glTF completa.** Los JSON íntegros están en `khronos/`.

La topología global se evalúa como limitación histórica: V3 tiene 794
aristas de borde espaciales y una arista non-manifold en Cabeza. B2 deja
703 bordes y 14 islas frente a 16, retirando componentes de gafas. A reduce
métricas pero empeora la imagen: rechazado. No se usó manifold global como
requisito artificial para las regiones intactas.

## Evidencias

170 capturas finales de Godot: 13 vistas/primeros planos por modelo,
12 imágenes de poses por modelo y cuatro máscaras de triángulos editados
por ensayo. Veinte láminas antes/después, detalles, poses y ediciones.
Cámaras, escala, luces y fondo equivalentes. Las máscaras muestran
triángulos reales retirados o modificados; no son ilustraciones.

Las capturas previas y ensayos rechazados también se conservan. La primera
prueba de movimiento atribuía cambios residuales a clips vacíos; se
corrigió el arnés a evaluación manual y la evaluación final distingue
explícitamente pistas vacías. Los reportes finales son `godot_report_v3`;
los anteriores se archivan como diagnóstico, no como evidencia de éxito.

El eje anatómico Neck→Head y los puntos de borde medidos se registran en
`CUELLO_ANATOMIA.json`. No se inventó un anillo: no hay unión de cuello
validada. El objetivo completo G2-C4 sigue pendiente; B2 es el avance
regional recuperable y no está promovido a producción.

## Publicación y bitácoras

Publicado como [PR #47 en borrador](https://github.com/Klymapo/COPOX/pull/47),
con base en la rama V3 del PR46. Los tres ZIP figuran en la carpeta
SHRINKWRAP de Drive de Gaston; se verificaron IDs y tamaños por lectura
de la carpeta. Enlaces y SHA256 en `ENTREGABLES.md`.

Actualizadas la memoria maestra integral, la bitácora técnica de Alastor
y maniquí y la bitácora shrinkwrap Beta→Gamma con resultados, rechazos,
limitaciones Godot/Khronos, PR y paquetes. No se fusionó ninguna rama.
