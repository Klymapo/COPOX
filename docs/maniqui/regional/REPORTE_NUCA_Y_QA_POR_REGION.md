# COPOX · G2-C2 — Avances independientes por región (nuca primero)

Fecha: 2026-10-14. Rama `experimentos/maniqui-g2c2-contorno-facial`. PR #43 **borrador**. Ninguna fusión ni sustitución de baselines.

## Nueva política para **todo** GLB
Un personaje deja de evaluarse como objeto indivisible. Cada pieza puede avanzar con su propia evidencia y su propio historial. Por ejemplo, si **nuca pasa** y **rostro falla**, se conserva la mejora de nuca para revisión/integración posterior. El rostro pendiente **no cambia el estado de nuca**, salvo si el candidato de nuca altera realmente una región protegida vecina.

Regiones normalizadas: `nuca`, `craneo`, `rostro`, `ojos`, `orejas`, `cabello`, `cuello`, `torso`, ambos brazos, manos, piernas y pies, `ropa`, `accesorios`. Para otros assets se define ROI equivalente en su cassette, nunca una adaptación ciega de coordenadas del Maniquí.

`copox/geometry/regional_acceptance.py` distingue:
- `REJECTED_LOCAL`: no pasa pruebas de esa región.
- `BLOCKED_INTEGRATION`: afecta vecinos protegidos o rompe atributos/rig.
- `NEEDS_EVIDENCE`: faltan mediciones/capturas.
- `PASS_LOCAL_TECHNICAL`: integridad, vecinos y evidencia estructural pasan, pero **falta aprobación artística**.
- `REJECTED_VISUAL_LOCAL`: evaluado y rechazado en su apariencia regional.
- `ACCEPTED_LOCAL`: veredicto visual satisfactorio y pruebas locales completas; **NO** implica permiso de fusionar.

`global_approval=false` y `promotion_allowed=false` por diseño en todos los reportes, incluidos los de regiones aceptadas. El siguiente gate verifica relaciones entre regiones, exportación/skin/materiales y aprobación explícita del propietario.

Existe una skill `regional-model-auditor` idéntica para Codex y Claude, en `.codex/skills/` y `.claude/skills/`.

## Experimento REAL con la nuca de r3

Fuente inmutable `assets/maniqui/maniqui_v0_3_r3.glb` SHA-256 `3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b`.

`copox/geometry/regional_nape_patch.py`: identifica un **arco continuo de 56 aristas orientadas** en el borde posterior del `Craneo`. Construye nuevos triángulos conectados a los índices existentes **sólo en la nuca**; no desplaza los vértices antiguos ni toca la primitiva `Cabeza` o las otras piezas. Para cada nuevo vértice se copian los atributos y pesos del vértice de borde correspondiente. El arco posterior se comprueba contra límites de Z y presupuesto de desplazamiento. El método NO suelda la nuca al rostro antiguo y NO cierra todo el cráneo: es una mejora parcial y local, no retopología final.

`tools/maniqui/g2c2_nape_only.py` genera dos GLB experimentales **hermanos** desde la misma fuente, no encadena candidatos ni sobreescribe archivos. Reimporta cada GLB para comprobar la nueva geometría. Registra SHA, triángulos nuevos, nodos, pesos y definiciones originales; preserva el buffer viejo como prefijo.

| Variante | Aristas posteriores | Vértices nuevos | Triángulos nuevos | Desplazamiento máximo |
|---|---:|---:|---:|---:|
| `nuca_local_suave` | 56 | 171 | 336 | 22.204 mm |
| `nuca_local_profunda` | 56 | 228 | 448 | 37.656 mm |

En ambas: mismos originales de `Cabeza`, cuerpos, materiales, jerarquía, 56 huesos y 29 **definiciones** de clips. No probamos aún deformación real en Godot ni 29 movimientos funcionales; 15 canales faciales históricos siguen con problemas conocidos.

**[Comparativa real de cuatro vistas para r3 + dos variantes](G2C2_NUCA_LOCAL_4V.png)**. El frontal conserva la apariencia anterior. Desde perfil y espalda aparece una banda nueva en el borde posterior del cráneo; la versión profunda produce una falda/banda más marcada, poco orgánica. La versión suave es más conservadora, pero **todavía presenta una transición recta que debe suavizarse con un método geométrico mejor y todas las referencias pertinentes**. Estos resultados son **aprobación técnica local únicamente**, no aprobación artística de la nuca.

Informe cuantitativo: `G2C2_NUCA_REGIONAL_REPORT.json`. Estados:
- `nuca = PASS_LOCAL_TECHNICAL`
- `rostro = REJECTED_LOCAL` (defectos previos, no modificados)
- `ojos/orejas = NEEDS_EVIDENCE`
- `global_approval = false`, `promotion_allowed = false`

## Validación y trazabilidad
[GitHub Actions #38621516241 — SUCCESS](https://github.com/Klymapo/COPOX/actions/runs/38621516241):
- 8 tests del gate regional;
- 5 tests de la geometría localizada;
- 2 GLB reales generados con pruebas de conservación de cara, skin, nodos, materiales y animaciones;
- Capturas auténticas front/3-4/perfil/espalda; SHA de baseline intacta;
- [Artifact: dos GLB experimentales y evidencias](https://github.com/Klymapo/COPOX/actions/runs/38621516241/artifacts/11921069865) (30 días).

**Los GLB quedan en artifacts, no se comitean como activos aprobados.** Se versionan los reportes y capturas en rama experimental.

## Qué sigue para la región nuca
1. Refinar la banda plana y buscar continuidad lateral curva sin tocar ni tapar orejas/cuello/cara.
2. Validar exclusivamente nuca con vistas trasera y perfiles de la **identidad correcta**; si mejora y pasa neighbours, emitir `ACCEPTED_LOCAL` sin exigir terminar el rostro.
3. Mantener `rostro`, `cejas`, restos grises cerca de lentes y animación facial en carriles **separados**.
4. Después, integrar regiones localmente aprobadas y comprobar transiciones, rig, intersecciones y materiales con Godot; requerir consentimiento para cualquier reemplazo.

No se prometió que r3 ahora fuese watertight globalmente, ni que la nuca esté lista para usar en el juego.
