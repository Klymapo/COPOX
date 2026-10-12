# AlasTheo · Cuaderno de prototipos Stylizer

**Estado general: EXPERIMENTAL.** Este repositorio contiene herramientas, modelos de referencia, scripts y pruebas para aprender qué funciona. No hay ninguna versión artística o tecnológica declarada como producto final. Que COPOX/CHSP-X marque un *baseline* significa solo **punto de comparación reproducible**, no obra terminada.

## Para volver a empezar

1. [Generador neutro de cubo GLB](../examples/build_cube.py): un ejemplo 3D reproducible sin imagen ajena, credenciales, Blender o servicios de pago. Ver [instrucciones](../examples/README.md).
2. [Puente GLB → candidato ALTH](../alth_bridge.py): exporta un manifiesto con hash y estado `UNREVIEWED`, sin cambiar la malla.
3. [Scripts originales de Stylizer](../pipeline_core.py), [preparación Godot](../prepare_godot.py) y [pruebas](../tests/): base para reanudar el trabajo.
4. [Experimentos de proporciones STYLIZED](../research/alth-anatomy/README.md): tres scripts de Blender, medidas y documentos anteriores. Son **hipótesis históricas**, no cotas finales.
5. [Historial de AlasTheo original](../../../docs/integration/alastheo-branch-variants/READINESS.md), [especificación técnica actual](../../../spec/alth_spec.json) y [COPOX](../../../copox/README.md): para comparar intentos anteriores.

## Qué fuimos construyendo

| Fecha | Experimento o hito | Lo reutilizable hoy |
| --- | --- | --- |
| 25 sept. 2026 | Bloque 1: entrada de imagen y pipeline común | Separación de generación por etapas |
| 25 sept. 2026 | Bloque 2: proveedores 3D y reintento desde imagen almacenada | Reintentar sin regenerar entrada |
| 25 sept. 2026 | Bloque 3: salidas y ZIP por tarea | Descargas reproducibles |
| 25 sept. 2026 | Bloque 4: fidelidad y referencias | Pruebas de calidad visual todavía por mejorar |
| 25 sept. 2026 | Bloques 5–6: adaptador estático para Godot, configuración y diagnósticos | Base del exportador; **no** conserva rigs complejos |
| 25 sept. 2026 | Interfaz móvil, cola persistente y acceso con contraseña | Modelo de trabajo desde móvil y PC |
| 25 sept. 2026 | Docker y servidor independiente | Implementación de referencia; no se declara despliegue activo ni gratuito |
| 12 oct. 2026 | Investigación anterior STYLIZED incorporada | Scripts/medidas para contrastar, sin imponer estándar antiguo |
| 12 oct. 2026 | Limpieza de resultados temporales | El código útil permanece; outputs desechables se regeneran |
| 12 oct. 2026 | Stylizer integrado en ALTH-META; pruebas CI y puente GLB | Una sola base de desarrollo pública, sin fusionar mundos de ejecución |
| 12 oct. 2026 | Cubo GLB neutro + prueba de extremo a extremo del manifiesto | Ejemplo gratuito y autocontenido |

La cronología se reconstruyó de los mensajes de commits de `Klymapo/stylizer`. Que un commit diga que una función se implementó no significa que haya sido validada contra servicios actuales.

## Ramas originales del experimento

Al auditar se hallaron **10 ramas y 54 commits distintos** accesibles entre ellas. Puntos de referencia recuperables mientras exista el repositorio original:

| Rama original | SHA de punta |
| --- | --- |
| `main` | `cf76337aba1eb79fa90129601d1aa88545542d48` |
| `codex/stylizer-bloques-1-4` | `563a8038dab64376d1b8c90c9cc1fedc75d898f9` |
| `codex/stylizer-godot-web` | `a97a591fa3a55524919f38a55a1933e94c02cd23` |
| `codex/stylizer-cloud-web` | `bcb2884f447a081d7d4ea7200c01d7b52f4fe492` |
| `chore/organizacion-2026-10-12` | `4cab33c652c987cec8d9236474afbe27be080dd7` |
| `chore/remove-obsolete-generated-outputs-2026-10-12` | `e5b392673919799765fec44d3b0e413f5261d54f` |
| `consolidation/stylized-research-2026-10-12` | `2f36a977273ff93bbb470858276810e21adee679` |
| `docs/stylizer-alastheo-tool-2026-10-12` | `46bf8a07ee747de4b1be8ebff9b1ac3452c676a8` |
| `audit/alastheo-integration-2026-10-12` | `5ca35675e03968b1e6d46dfebf254a17545f4ee5` |
| `docs/history-local-links-2026-10-12` | `2afc8244a87b7e0daa095a4357432a8ce843f29e` |

Los tres antiguos `codex/...` quedaron detrás de `main` (sin commits nuevos exclusivos). Las otras ramas contienen, mayormente, variantes documentales, limpieza y migraciones ya absorbidas en la línea principal. Una de las ramas antiguas incluye referencias a archivos de certificado y cachés; por seguridad **no se importó sin auditoría todo el historial privado** al repositorio público.

## Modelos anteriores

En el repositorio Stylizer original se identificaron dos modelos de ejemplo (`model.glb`, 12.45 MB; `sample.glb`, 1.85 MB) y una imagen generada (`output_agnes.png`, 0.74 MB). **No se publicaron aquí** porque no se comprobó su procedencia ni licencia de reutilización. El cubo neutro sirve como sustituto abierto para pruebas de formato.

Si se quiere eliminar el repositorio original, primero exportar un **Git bundle completo** a un almacenamiento privado y comprobar restauración. Una lista de SHA o esta bitácora **no recuperan por sí solas todos los objetos de Git**. No publicar el bundle completo a ciegas: podría contener resultados, certificados u otros datos de etapas previas.

## Reglas simples a partir de ahora

- Todo es **prueba / candidato / referencia**, salvo declaración explícita posterior.
- Guardar un ejemplo mínimo que funcione y su forma de reproducirlo; no guardar decenas de renders casi iguales.
- Documentar por qué un intento se descartó o qué aprendimos, no solo que un script se escribió.
- Usar nombres de versión y SHA de entrada/salida; no sobrescribir pruebas históricas necesarias.
- Reservar `assets/` del proyecto para su propio flujo de revisión, pero llamar a esos estados *baseline de trabajo*, no modelo final.
