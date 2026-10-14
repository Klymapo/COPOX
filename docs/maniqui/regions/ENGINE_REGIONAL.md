# COPOX · Motor de auditoría independiente por región

Fecha 2026-10-14. **Experimental**, sin reemplazo ni fusión. PR #43, rama `experimentos/maniqui-g2c2-contorno-facial`.

## Cambio de paradigma confirmado

La unidad que compite y se audita ya no es exclusivamente el GLB completo: puede ser una **región** del asset. El defecto de otra región nunca invalida automáticamente un avance local. Se verifican, sin embargo, posibles daños a vecinos, atributos y esqueleto: esos sí son relevantes para la pieza.

El registro actual define 18 regiones para el personaje: nuca, cráneo, rostro, ojos, orejas, cabello, cuello, torso, brazos izquierdo/derecho, manos izquierda/derecha, piernas izquierda/derecha, pies izquierdo/derecho, ropa y accesorios. Cada una tiene su propia evidencia, pruebas y evaluación artística; se puede extender el registro para otras clases de asset.

## Dos niveles de aceptación

`copox/geometry/regional_acceptance.py` separa:
- `PASS_LOCAL_TECHNICAL`: pruebas estructurales y vecinos pasan; sigue pendiente evaluación artística.
- `ACCEPTED_LOCAL`: además existe aprobación artística local; **no** significa permiso para sustituir el GLB.
- `NEEDS_EVIDENCE`: faltan referencias, capturas o datos técnicos.
- `REJECTED_LOCAL` / `REJECTED_VISUAL_LOCAL`: falló la pieza concreta, no otras.
- `BLOCKED_INTEGRATION`: se dañó una región vecina o falló la seguridad de atributos/rig.

La promoción requiere un paso distinto de integración y la aprobación explícita del usuario. Por diseño, `global_approval=false` y `promotion_allowed=false` incluso si una pieza alcanza `ACCEPTED_LOCAL`.

## Cómo se conecta con el motor de cassettes

En un cassette que habilite esta función **explícitamente**:
```json
{
  "evaluation": {
    "scope": "region",
    "region": "nuca"
  }
}
```
Además del resto de campos habituales del cassette, su perfil debe incluir como mínimo dos auditores:
```json
[
  {
    "id": "nuca-geometry",
    "region": "nuca",
    "critical": true,
    "command": ["python", "-m", "MI_AUDITOR_DE_NUCA", "{audit_result}"]
  },
  {
    "id": "shared-rig-and-neighbors",
    "scope": "global_safety",
    "critical": true,
    "command": ["python", "-m", "MI_AUDITOR_DE_SEGURIDAD", "{audit_result}"]
  }
]
```
*Los comandos `MI_AUDITOR_...` son placeholders explicativos, no programas ejecutables.* Deben implementarse antes de activar un cassette concreto.

Reglas del motor `copox/engine.py`: en modo `evaluation.scope=region`, sólo corren auditores etiquetados para esa región más auditores `scope=global_safety`. Los auditores de arte de otras regiones se registran `N-A / other_region_not_a_veto`. Tanto la región objetivo como la seguridad global deben existir, ser aplicables y pasar. Los auditores con `applicable=false` **no satisfacen ningún gate obligatorio**.

El ganador se registra con `LOCAL_ELIGIBLE` y manifiesto `LOCAL_QA_READY_FOR_REVIEW`. En **ningún caso** se ejecuta `commands.promote` de un cassette regional. Los cassettes globales antiguos conservan su comportamiento anterior; no deben utilizarse para sustituir activos sin los procedimientos de aprobación del proyecto.

## Experimentos reales de nuca disponibles ahora

Fuente `maniqui_v0_3_r3.glb`, SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`.

**A) Ensayos de banda curva por región** (análisis anterior, mismo PR #43):
- `nuca_local_suave`: 336 triángulos nuevos, 171 vértices, 22.204 mm máximo; estado `PASS_LOCAL_TECHNICAL`.
- `nuca_local_profunda`: 448 triángulos nuevos, 228 vértices, 37.656 mm máximo; estado `PASS_LOCAL_TECHNICAL`.
- [Capturas reales de cuatro vistas](../regional/G2C2_NUCA_LOCAL_4V.png) · [Reporte](../regional/G2C2_NUCA_REGIONAL_REPORT.json).
- Ninguna aprobada artísticamente; la banda de la versión profunda es notoriamente rígida y necesita refinamiento. Ni una ni otra se sueldan a toda la cara.

**B) Ensayo independiente de arco parcial** (separado, no encadenado):
- `copox/geometry/partial_loft.py` y `tools/maniqui/region_nuca_probe.py`.
- Nuevo GLB candidato de nuca con **49 vértices** y **96 triángulos**, sólo posteriores y enlazados a índices originales del cráneo.
- Conserva los datos de rostro, demás piezas, 56 huesos y 29 definiciones de clips. Fuente original intacta, primitiva de cráneo permanece con **un loop abierto** y no está soldada al rostro.
- Estado `NEEDS_EVIDENCE` porque hacen falta comparaciones artísticas verificadas, auto-intersecciones y prueba Godot. [Cuatro vistas reales](nuca/NUCA_ANTES_DESPUES_4V.png) · [Reporte](nuca/REGIONAL_QA.json).

**Importante:** que los tres ensayos sean técnicamente posibles NO demuestra que cualquiera haya limpiado definitivamente la nuca. Se mantiene el mejor candidato por métricas de región y revisión humana, no se descarta por defectos en ojos o cara.

## Pruebas

- [CI regional](https://github.com/Klymapo/COPOX/actions/workflows/maniqui-regional-qa.yml): `test_regional_acceptance`, `test_partial_loft`, `test_engine_regions`, `test_engine_preflight` y un GLB real de nuca.
- [CI previo de dos variantes de nuca](https://github.com/Klymapo/COPOX/actions/runs/38621516241) con capturas y paquetes GLB.
- El motor prueba explícitamente `nuca=PASS` con `rostro=FAIL` y **no ejecuta** promoción. También comprueba que fallar seguridad global o marcarla no aplicable BLOQUEA la nuca.

## Próximas regiones

Mantener el trabajo de nuca independiente y abrir carriles paralelos para cabello, orejas/ojos, manos, pies, prendas y accesorios. Los lentes ya fueron retirados como primitiva de ropa separada en un experimento anterior; los residuos cerca de los ojos requieren verificación específica sin borrar facciones.

**No hay modelo completo aprobado ni GLB histórico reemplazado.**
