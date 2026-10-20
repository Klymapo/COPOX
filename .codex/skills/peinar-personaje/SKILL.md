---
name: peinar-personaje
description: Elige o crea el pelo de un personaje ALTH-META (bloques low-poly sobre arco SENKU, cobertura total y resortes en Godot). Úsala cuando haya que peinar a un personaje o ajustar su pelo.
---

# Peinar personaje (COPOX)

**Reglas de Admin:** cubre SIEMPRE toda el área de pelo (CHXP `cobertura_pelo` ≥ 99.5 %) y se mueve como pelo al
correr o brincar (`pelo_resortes`).

## Usar lo que existe
En la ficha, `pelo`: `theo` (CAPA_PELO_THEO, aprobado de momento), `corto`, `mechones`, `rapado`
(`copox/medicion/catalogo.py` → `PELO`). Son nodos de la base congelada con KHR_node_visibility.

## Hacer un peinado nuevo (lo que funcionó con Theo)
1. Referencia de 3 vistas con `.senku.json` → arco del pelo con SENKU (`copox/medicion/senku_ref.py`), IoU de franja ≥ 0.9.
2. Bloques low-poly explícitos (`pelo_bloques`) siguiendo el arco; mechones de cobertura fijos a `Head`.
3. Huesos de resorte (`pelo_huesos`) + `copox/godot/alth_resortes.gd`: el SpringBoneSimulator3D se crea DESPUÉS del
   primer cuadro; rigidez 4, arrastre 0.6, gravedad 0.1; GIF con `--fixed-fps 60`.
4. Separación pelo/piel > 1 mm (si no, dientes en Godot). Volver un nodo `CAPA_PELO_<NOMBRE>` y agregarlo al catálogo.
5. CHXP V3 con `--gif Walk-loop,Run-loop`.

No usar: bolas encadenadas (parecen trenzas), PeloCunas, `hundir` la cáscara.
