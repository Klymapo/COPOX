# Adán V49 (19 oct 2026) — SIN APROBAR

Sobre V48.3 (aprobada de momento). Receta: `docs/medicion/receta_adan_v49.py ADAN_V48_3.glb ADAN_V47.glb ADAN_V49.glb`.
Derivado de entrega: `docs/medicion/vestir_adan.py ADAN_V49.glb ADAN_V49_VESTIDO.glb`.
Skills aplicadas (Drive/SKILLS de Argos): vestuario-cabello (ropa ajustada = skinning, módulos separados, culling solo en
derivado, pelo por mechones de raíz ancha y punta suave), anatomía 3D (pelvis sugerida por silueta, sin hipertrofia, sin
remesh global, se preservan rig/morphs), movimiento y rig (56 huesos y clips intactos, validación en Godot), y de la rama
de experimentos gltf-rig-guardian (sin primitivas vacías, Godot importa) y visual-critic (cuatro vistas + movimiento).

## Cuerpo
- **Pelvis** (Pelvis_PIEL): triángulo de frente (ancha bajo el torso, en V hasta la entrepierna), unión suave a torso y
  piernas; pesos Hips → muslos. El short ya se puede quitar. Pendiente: aún se marca el borde de la tapa de las piernas.
- **Cuero cabelludo** (CueroCabelludo_PIEL): superficie lisa 4.5 mm bajo el pelo, entra bajo la piel en la orilla.
- **Pies**: separados de las piernas (bajo y = 0.045) en el nodo PIES_DESCALZOS.

## Piezas intercambiables (KHR_node_visibility)
| Nodo | Por defecto | Qué es |
|---|---|---|
| CAPA_SHORT | visible | short azul (removible) |
| PIES_TENIS | visible | pie con tenis (suela #F7F0E7, corte #A8453B, empeine redondeado; apoya en y = 0) |
| PIES_DESCALZOS | oculto | pies |
| CAPA_GUIA_CAPILAR | visible | pelo liso V48.3 |
| CAPA_PELO_CORTO | oculto | corte sencillo (lados y nuca más arriba) |
| CAPA_PELO_MECHONES | oculto | 20 mechones estilo ALTH (hoja de Theo) |

## Vestido (derivado ADAN_V49_VESTIDO)
Camisa #FBEFE1 y pantalón #4A5770 por partes (torso, mangas, cadera desde la pelvis, perneras), tenis, mechones; short,
pies y pelo liso ocultos; piel tapada por la ropa quitada solo en el derivado. Probado caminando en Godot 4.7.2.

SHA-256: V49 `500b849c94a3fa82f5ac910a4413aa29a916e90ab5871e875dcfae53c58beb1d` · vestido `3fbe679f5db3aeef270565ed903a24503b7ada3b16444a26a849cb2b3d2ac3ac`.
