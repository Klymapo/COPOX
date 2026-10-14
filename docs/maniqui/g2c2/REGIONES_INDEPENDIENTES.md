# COPOX · Política de avances por partes · primer cassette NUCA

**Fecha:** 2026-10-14. **Estado:** G2-C2-R, modelo r3 experimental. **NO aprobación general ni fusión**.

## Decisión de dirección
No rechazar una modificación de nuca porque siga mal la cara. No rechazar la mano porque la gabardina tenga un problema, etc. **Se juzga únicamente la pieza intervenida**, siempre que se preserven las zonas ajenas y los invariantes compartidos (rig, clips, material, UV, archivos originales). Cada pieza mantiene un registro y un candidato derivado separado. El avance global sólo se aprueba al final, cuando todas las regiones necesarias han sido revisadas y existe una composición sin conflictos.

Motor reusable `copox/geometry/regional_review.py` y skill `regional-cassettes` para Codex y Claude. Todo candidato genera `region/candidate_hash`, informe técnico, capturas antes/después y dictamen local. Los defectos **preexistentes** de otras regiones no impiden certificar algo local; los cambios que invadan otra región **sí** bloquean.

## División propuesta del GLB (todas las piezas)
| Subproyecto de trabajo | Estado al inicio | Dependencias / especificación |
|---|---|---|
| **Nuca / cráneo posterior** | **Prueba técnica local generada** | Probar cobertura posterior sin tocar cara u orejas; unión a piel de cuello pendiente |
| Sienes / patillas anatómicas | Pendiente | Excluir patillas de los lentes, preservar orejas y ojos |
| Frente | Pendiente | Evitar bulto; conservar cejas y proporciones originales |
| Ojos y párpados | Congelados durante nuca | Evaluación facial en su propio cassette |
| Nariz y boca | Congelados durante nuca | Reconstrucción facial con referencias correctas |
| Orejas | Congeladas durante nuca | No modificar por parche de nuca |
| Cuello | Pendiente | Compatibilidad anatómica con nuca |
| Cabello | Pendiente | No asumir que islas del pelo son piel |
| Manos y dedos | Pendiente | Dedos/pulgar/proporciones, pruebas de agarre |
| Brazos y hombros | Pendiente | Articulaciones, piel y skinning |
| Torso y vestuario | Pendiente | Cuello de camisa, chaleco, corbata |
| Gabardina / faldones | Pendiente | Tela al caminar/sentarse, colisiones, sombreado |
| Piernas, rodillas y pies | Pendiente | Pasos menos rígidos, articulaciones |
| Lentes (accesorio) | **Remoción experimental PASÓ** | Ver PR #43; restos grises sin identidad aún REVIEW_REQUIRED |
| Rig, animaciones, gestos | Invariantes y QA por separado | 56 huesos, 29 clips nombrados; sólo 13 con claves variables en auditoría G2-B, morphs faciales pendientes |
| Materiales, UV y export Godot | Gate transversal | Todos los candidatos deberán conservar importación válida |

Las divisiones **no implican** que ya existan primitivas independientes para todas las subregiones: algunas comparten `Cabeza` o `Brazos`. El cassette debe usar máscaras de triángulo verificadas o un nodo/material independiente, según el caso.

## Primera prueba real: NUEVO parche posterior, no global
**Fuente**: `assets/maniqui/maniqui_v0_3_r3.glb` SHA256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`.
**Artefacto de prueba**: `assets/maniqui/maniqui_v0_3_r3_nuca_local_prototipo.glb` en GitHub Actions, NO versionado como baseline ni fusionado.

Método `copox.geometry.partial_nape.rear_nape_patch`: selecciona una secuencia continua posterior del borde de Craneo por posiciones X/Z reales y extiende una pequeña banda con índices originales compartidos. No toca cara, labios, párpados, nariz ni orejas.

**Resultados de la primera prueba**:
- **34 aristas** de rim posterior, **68 triángulos nuevos**, **35 vértices nuevos**.
- Cráneo original: **4097 vértices y 8064 triángulos**. Candidato: **4132 vértices y 8132 triángulos**.
- Desplazamiento local máximo hacia abajo **42 mm** y factor radial **0.97**, dentro de la región posterior predefinida.
- Todos los vértices y caras del cráneo original permanecen idénticos; `Cabeza` y todas las demás primitivas permanecen byte/JSON idénticas, igual que los datos preexistentes de materiales, clips, huesos y el buffer original.
- **130 aristas abiertas**, porque el parche regional tiene borde inferior y dos extremos. No afirmar retopología manifold completa ni soldadura a Cara.
- Reimportación del GLB: estructura y atributos comprobados; **no se ha hecho aún una prueba Godot completa del candidato**.
- Resultado: `NUCA_LOCAL_TECHNICAL_PASS__VISUAL_REVIEW_REQUIRED`. Esto significa **avance técnico conservable**, no mejora visual certificada.

**Capturas del GLB auténtico**:
- [Antes y después, frontal/perfil/nuca/nuca ¾](nuca/NUCA_LOCAL_ANTES_DESPUES_4V.png).
- [Los únicos triángulos añadidos resaltados en azul](nuca/NUCA_SOLO_TRIANGULOS_NUEVOS_4V.png).
- [Informe de QA regional JSON](nuca/REPORTE_NUCA.json).

## Flujo para siguientes zonas
`Elegir una zona → Congelar el resto → Mutar copia → Comprobar cambios únicamente dentro del ROI → Capturas reales de ESA zona → Aprobar/rechazar sólo ese avance → Guardar candidato por región`.

Si **nuca mejora y cara no**, poner `nuca=REGION_IMPROVED_PENDING_HUMAN_APPROVAL`, `cara=REVIEW_REQUIRED`; ninguna selección de versión global hasta ejecutar composición e integración, con revisión final de intersecciones, rig, Godot y referencias.

Si se sobreescriben triángulos de otra parte, cambia el rig o se altera un modelo base aprobado, bloquear incluso aunque la nuca se vea mejor. La integridad transversal del asset **nunca** se descarta.

No fusionar PR ni sustituir GLB sin decisión expresa de Admin. Implementación 100% gratuita Python/NumPy/SciPy/Pillow + GitHub Actions.
