# G2-C6 · Revisión de detalles anatómicos — avance experimental

Base inmutable: G2-C3 V3, SHA256 `0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b`.
Se usa la limpieza de gafas B2, SHA256 `daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec`.
No se toma como padre ningún candidato facial rechazado R1–R3 ni el combinado conservador de G2-C5.

## Reparación real L1: unión de piernas con zapatos

El GLB B2 tenía un espacio vertical medido de 17,25 mm entre la terminación inferior de cada pierna y la corona del zapato. L1 desplaza exclusivamente el anillo inferior existente de cada primitiva de pierna (33 vértices por lado) hasta penetrar 13 mm bajo la corona del zapato. Los datos de cada lado se miden de su propia geometría, sin copiar coordenadas especulares. La sección superior de las piernas y los zapatos permanecen idénticos. El resultado deja una unión visual de tipo borde de calzado; no pretende soldar anatómicamente pie y pierna.

Código reproducible: `tools/maniqui/g2c6_ankle_join.py`. GLB sin aprobar: `build/g2c6/maniqui_G2C6_L1_UNIONES_TOBILLOS_SIN_APROBAR.glb`, SHA256 `cf759292adace095b0a0c41516e0ecebead3cb48efb44210afcbbef8cc8d71e0`. La copia `L1_compat.glb` quita solamente datos vacíos históricos para importadores; el GLB bruto y la base se conservan. 66 vértices movidos, cero triángulos añadidos/eliminados y cero atributos de pesos alterados.

Comparación real de GLB importados en Blender 4.3.2: `build/g2c6/COMPARATIVA_REAL_B2_L1_BLENDER.png`, con vista frontal, perfil y primeros planos idénticamente iluminados. En reposo la separación visible desaparece de frente; queda una línea de encuentro en el borde del zapato. Las capturas de pose se encuentran en `build/g2c6/captures_pose_mid/`. La prueba visual de una pose no certifica todo el espacio de animación.

Godot 4.7.2, importación headless de la copia compatible: error 0; 56 huesos, 24 superficies, 29 definiciones de clip, 145 muestras de matrices óseas iguales a B2. El GLB bruto presenta el error 43 heredado por accesores de recuento cero. La copia compatible descarta los 15 canales faciales huérfanos de mallas vacías y preserva los 29 nombres de clips. La validación Khronos del bruto queda en 53 errores y 182 avisos, iguales a B2; los dos mensajes informativos nuevos corresponden a accesores POSICIÓN antiguos sin uso, retenidos para preservar el binario de origen. No se declaran expresiones funcionales ni deformación comprobada por skinning.

## Límites observados del encargo amplio

- **Huecos del rostro y nariz:** siguen siendo grandes y visibles bajo/entre los ojos. Las tres técnicas faciales G2-C5 R1–R3 ya fueron rechazadas artísticamente; repetir el mismo relleno sería un progreso ficticio. L1 no modifica estos triángulos.
- **Calva:** se conserva exactamente la calva/nuca suavizada de V3, pero continúa una separación visual en la transición frontal entre el casquete y las piezas de cara. Mover el casquete o tapar el espacio con un parche óptico podría borrar avances o generar una superficie sin continuidad; no se hace aquí.
- **Mandíbula/cuello, pliegues y otras uniones:** siguen pendientes. La vista lateral de B2 muestra además discontinuidades históricas mayores en la cabeza y el cuerpo; los intentos C2/C3 de mandíbula ya fallaron. No se insertan pliegues decorativos encima de una base abierta ni se declara ergonomía funcional sin pruebas de poses de todos los miembros.

Estado: **L1 es mejora local verificable, SIN APROBAR como maniquí final.** No se combina con A/C ni se promociona automáticamente. Las versiones previas y la rama principal no se reemplazan ni fusionan.
