---
name: regional-model-auditor
description: Evalúa, conserva y versiona avances por región de cada GLB (nuca, cara, orejas, cabello, manos, piernas, ropa); errores ajenos nunca vetan el trabajo local y las fusiones exigen autorización explícita.
---

# COPOX · Regional Model Auditor

## Regla principal

**La nuca no fracasa porque la cara esté defectuosa.** Lo mismo aplica a brazos, manos, pies, cabello, vestuario, interfaces y otros assets compuestos. Evaluar cada región de forma independiente y conservar el mejor candidato de esa región como **evidencia**, sin reemplazar modelos aprobados.

## Operativa

1. Definir una ROI geométrica estable (cara, cráneo, nuca, cuello, orejas, pelo, torso, brazo derecho/izquierdo, mano derecha/izquierda, pierna, pie, ropa y accesorio). Para assets genéricos, añadir un cassette propio; nunca adaptar coordenadas de Alastor a otro personaje sin medición.
2. Aplicar `visual-critic` a **todas las referencias pertinentes a esa región** y al impacto sobre vecinos protegidos. Una referencia de cara pendiente NO bloquea QA de nuca, pero no se acepta una nuca que rompa cuello u orejas.
3. Ejecutar modificación en una **copia inmutable de baseline**, generando un GLB por candidato. Las regiones ajenas no cambian ni pierden índices o atributos. Mantener `glTF Rig Guardian`.
4. Crear capturas *reales* frontal, perfil, 3/4, posterior, además de primeros planos útiles. Registrar SHA de base, GLB candidato, máscaras ROI, desplazamiento local, nuevas aristas/caras, vecinos y QA Godot si corresponde.
5. Emitir un `RegionVerdict` en `copox.geometry.regional_acceptance`. Los estados son `REJECTED_LOCAL`, `BLOCKED_INTEGRATION`, `NEEDS_EVIDENCE`, `PASS_LOCAL_TECHNICAL`, `REJECTED_VISUAL_LOCAL` o `ACCEPTED_LOCAL`.
6. **PASS_LOCAL_TECHNICAL no significa aprobado visualmente**. `ACCEPTED_LOCAL` requiere comparación artística verificada de esa región. Integración exige gate propio y permiso de Admin; nunca fusionar ni promover desde un estado local.
7. Defecto fuera de la ROI -> dejar esa región en `PENDING` o con su propio rechazo; **no disminuir el estado de otra región**. Defecto nuevo en un vecino afectado -> `BLOCKED_INTEGRATION` sólo para el candidato responsable.
8. Conservación de evidencia: mantener reportes y capturas en rama/Actions; no eliminar fuentes, no promover modelos rechazados. Candidatos pueden componerse posteriormente sólo con comprobación completa de intersecciones, skin, UV, morph, Godot y aprobación humana.

## Ejemplo ejecutable

```bash
python -m unittest discover -s tests -p 'test_regional_acceptance.py' -v
python -m unittest discover -s tests -p 'test_regional_nape_patch.py' -v
python -m tools.maniqui.g2c2_nape_only
```

Ensayo real: `docs/maniqui/regional/G2C2_NUCA_REGIONAL_REPORT.json` y `G2C2_NUCA_LOCAL_4V.png`. Produce únicamente nuevos candidatos de **nuca** desde r3 histórico; la cara sigue pendiente, sin bloqueo cruzado.
