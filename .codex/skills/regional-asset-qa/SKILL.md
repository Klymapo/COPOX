---
name: regional-asset-qa
description: Orquesta correcciones y auditorías anatómicas por regiones independientes de un GLB, sin que un defecto de cara rechace una nuca válida. No modifica ni promociona modelos sin aprobación.
---

# COPOX · Regional Asset QA

## Objetivo
Cada zona del GLB progresa de forma independiente. **Un fallo en la cara no veta una nuca localmente válida**; un éxito local tampoco autoriza sustituir el modelo completo.

## Alcance
Usar para nuca, cráneo, rostro, ojos, orejas, cabello, cuello, torso, brazos, manos, piernas, pies, ropa y accesorios. Nombres canónicos en `copox.geometry.regional_acceptance.REGIONS`.

## Pasos
1. Asignar `evaluation: {"scope":"region","region":"nuca"}` (cambiar la región según la tarea) en cassette. Los auditores de geometría deben etiquetarse `region: "nuca"` y debe existir **siempre** un auditor `scope: "global_safety"` para rig, materiales, vecinos, integridad y baseline.
2. Capturar vistas/poses **de la región elegida** desde el GLB real; contrastar todas las referencias relevantes de esa región. Un defecto en otra región no cuenta como veto local.
3. Registrar fuente y hashes; modificar únicamente atributos/vértices/caras de la región seleccionada, sin dañar vecinos, costuras entre piezas, protección de facciones, UV, pesos ni animaciones.
4. Ejecutar primero preflight regional barato. Sólo si es apto pasar a captura de cuatro vistas, tests y auditores locales + seguridad global. Si la nuca falla por su propia geometría o afecta al cuello, entonces sí bloquear la nuca.
5. El motor `copox.engine` filtra auditores por región y conserva los de seguridad global. Cuando todo pasa, registra `LOCAL_QA_READY_FOR_REVIEW`, **nunca ejecuta** `commands.promote` en este modo.
6. `copox.geometry.regional_acceptance.evaluate_regions` mantiene estados separados: `NEEDS_EVIDENCE`, `PASS_LOCAL_TECHNICAL`, `ACCEPTED_LOCAL`, `REJECTED_VISUAL_LOCAL`, `REJECTED_LOCAL`, `BLOCKED_INTEGRATION`.
7. Las cuatro puertas son distintas: integridad técnica local; juicio artístico local; pruebas de integración con vecinos/rig; autorización humana para sustituir o fusionar. Un éxito en cualquiera NO implica superar los demás.

## Primera demostración real
`python -m tools.maniqui.region_nuca_probe` crea una banda exclusivamente posterior sobre r3 original, añade vértices sin modificar rostro, verifica pesos/huesos/animaciones y presenta comparación real frontal, 3/4, perfil, trasera. El resultado `NEEDS_EVIDENCE` significa que no ha sido aprobado visualmente. La cabeza sigue abierta y NO soldada a Cara.

## Comprobaciones
`python -m unittest discover -s tests -p 'test_regional_acceptance.py' -v`
`python -m unittest discover -s tests -p 'test_partial_loft.py' -v`
`python -m unittest discover -s tests -p 'test_engine_regions.py' -v`
`python -m unittest discover -s tests -p 'test_engine_preflight.py' -v`

## Reglas inquebrantables
No fusionar PRs, no reemplazar GLBs históricos, no declarar una nuca corregida si falta aprobación visual, no mezclar referencias de personajes distintos, no borrar ojos/párpados/cejas/orejas por retirar lentes. Mantener una bitácora y artefactos por **región y candidato**.
