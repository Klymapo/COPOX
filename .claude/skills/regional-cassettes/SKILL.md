---
name: regional-cassettes
description: Ejecuta, audita, versiona y aprueba por separado las regiones de un GLB o cualquier asset COPOX. Evita descartar una mejora de nuca porque el rostro siga defectuoso, sin permitir daños a datos compartidos.
---

# COPOX · Cassettes regionales (no vetos globales por fallos ajenos)

## Principio operativo
**Una región a la vez.** La nuca, sienes, frente, cejas, ojos, nariz, boca, orejas, cuello, manos, brazos, torso, gabardina, piernas, zapatos, texturas, rigs y clips tendrán evaluaciones y bitácoras independientes. Una región que pasó **no se rehace** por un defecto ajeno.

## Reglas de selección
1. Elegir `target_region`, `base_glb_sha256`, geometría/triángulos permitidos, zona de protección y artefactos de otras partes congeladas. Definir qué pruebas de la región aplican, usando las 4 vistas y todas las referencias del mismo personaje.
2. Antes de editar: calcular checksum de GLB y snapshot por primitiva; `regional_review.aggregate_regional_review` gestiona estatus por región.
3. Crear candidato **hermano, nunca sobrescribir** la versión aprobada o experimental base. Modificar sólo triángulos/vértices que estén en la región elegida. Para un parche de nuca usar `copox.geometry.partial_nape.rear_nape_patch`.
4. Después de editar: comprobar igualdad de todas las primitivas/atributos/animaciones fuera de alcance; la geometría original dentro de la región debe conservarse cuando sólo se añade nueva piel. Incluir tests de distancias, normals, winding, pesos, UV, glTF/Godot cuando corresponda.
5. Obtener captura real del candidato frontal, perfil, posterior y tres cuartos. Ideal: lámina adicional que destaque **sólo los triángulos nuevos**. Visual Critic evaluará la región objetivo; cualquier defecto en otra región se anota como dependencia futura y **no rechaza automáticamente el logro local**.
6. Registrar dos niveles **distintos**:
   - `LOCAL_TECHNICAL_PASS + REGION_READY_FOR_VISUAL_REVIEW`: geometría preservada y revisable, no necesariamente bonita.
   - `REGION_IMPROVED_PENDING_HUMAN_APPROVAL`: mejora visual regional demostrada, aún sin permiso para promoción.
7. Guardar la variante de región con SHA y decisiones; **no** fusionar patches inconexos o candidatos generados sobre distintas bases de forma automática. Cuando se compongan cambios regionales, recalcular topología, intersecciones y Godot completo.
8. Cambios a `GameState`, autoloads y producción quedan fuera de alcance salvo aprobación explícita; ningún commit a `main` ni sustitución de GLB.

## Fallos realmente globales
Un candidato sí se rechaza incluso con mejora local si invade geometría congelada, rompe huesos/pesos, materiales, animaciones, identidad del personaje, integridad del archivo o introduce riesgos fuera del ROI. Defecto preexistente sin cambios, por ejemplo ojos todavía fragmentados mientras se ensaya la nuca, **no** equivale a `out-of-scope damage`.

## Contrato de evidencia
`copox/geometry/regional_review.py` devuelve status por sección, checks globales indispensables y `global_model_approved=false`. `tools/maniqui/g2c2_nuca_cassette.py` demuestra el flujo con datos r3 reales. Ejecutar:
```
python -m unittest discover -s tests -p 'test_regional_nape.py' -v
python -m tools.maniqui.g2c2_nuca_cassette
```
Reportar `LOCAL_TECHNICAL_CANDIDATE` y nunca llamar `global_watertight` a la expansión de una parte del rim con bordes laterales abiertos.

## Escalabilidad
Usar exactamente el mismo cassette de selección → modificación → evidencia → QA → registro sobre modelos/ropa, peinados, manos, poses, scripts, interfaces y escenas. El cassette es reusable; no asumir que `Cabeza` es la única pieza editable.
