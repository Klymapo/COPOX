---
name: anatomic-cut
description: Recorta mallas 3D por regiones anatómicas sin perder ojos, orejas, boca, normales, UV ni pesos del rig. Úsala para retirar placas, restos de pelo y geometría interpenetrada con máscaras de protección.
---

# Anatomic Cut · Cirugía selectiva

## Activación
Usar cuando sea necesario eliminar geometría defectuosa o sustituir una región por una superficie paramétrica sin perder facciones.

## Procedimiento
1. Inspeccionar topología con `copox.adapters.mesh_topology_probe`, identificar UV seams y regiones anatómicas; no declarar agujero a partir de índices duplicados por UV.
2. Clasificar triángulos `protected_faces` ANTES de operar; proteger el triángulo entero cuando toque ojos, orejas, labios u otras regiones congeladas.
3. Ejecutar `copox.geometry.anatomic_cut.cut_plane` con `POSITION`, `NORMAL`, `TEXCOORD_0`, `JOINTS_0`, `WEIGHTS_0` si están presentes. Se interpolan los atributos en los nuevos puntos de corte.
4. Morph targets, atributos custom y skin de más de 4 influencias no están cubiertos: bloquear y diseñar un adaptador explícito en vez de descartarlos.
5. Examinar conteos de caras recortadas, intersecciones, nuevas aristas abiertas y triángulos protegidos intactos. Un triángulo protegido puede sobresalir del plano y crear discontinuidad; NO declarar que la región quedó limpia.
6. Guardar candidato hermano con hash nuevo, sin sobrescribir fuentes; ejecutar `copox-auditoria-3d`. Si aparece un borde objetivo abierto, enviarlo a Surface Stitch, no taparlo por superposición.
7. Rechazar si los atributos del rig, las facciones o las UV no pasan las verificaciones; detener tras tres iteraciones sin progreso.

## Comprobación
`python -m unittest discover -s tests -p 'test_geometry_operations.py' -v`.

## Enlace con Visual Critic
Solicitar `operator=Anatomic Cut` sólo cuando la matriz multivista identifique fragmentos y el diagnóstico de malla mida componentes desconectados/triángulos flotantes, plano de corte medido, atributos compatibles y protección de triángulos lista. Comparar **todas las vistas/poses** antes de elegir y después de cortar, incluyendo referencias contradictorias. No eliminar facciones por una única silueta lateral, no procesar morph targets sin soporte y no convertir el preflight en permiso de fusión.
