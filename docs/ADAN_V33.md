# Adán V33 · cabeza con aristas más afiladas (CABEZA APROBADA)

- **Pedido de Admin (18 oct 2026):** "afilar" las aristas de la cabeza para parecerse más a las referencias (Hoja de vistas).
- **Resultado:** `ADAN_V33.glb`, SHA-256 `9467cdd48878e1335d0f58f3ff8402cff766167bbb618dd2d525332c95e689a3`. Receta `docs/medicion/receta_adan_v33.py` (V32 + este paso), reproducible bit a bit.

## Medido

Cortes horizontales de la piel de la cabeza: cada corte es casi una elipse (superelipse n ≈ 2.1–2.5 adelante, 2.1–5 atrás). En la hoja la cabeza es una caja de esquinas redondeadas.

## Qué se hizo

- Cada corte, de y = 0.55 hacia arriba, pasa a una superelipse más cuadrada con los mismos semiejes (n ≥ 3.4 adelante, n ≥ 3.0 atrás). Frente, costados y nuca no se mueven; salen las esquinas.
- El mismo campo se aplica a todo lo que va en la cabeza (piel, orejas, guía capilar), así nada se separa.
- **Protegido:**
  - La cara (ojos, párpados, cejas, mejillas, boca): adelante el campo solo vive en los costados (φ < 24–42°).
  - La quijada (y < 0.55): la primera prueba hacía "cachetes".
- Normales del archivo + el cambio de las normales geométricas, para no perder lo hecho en la boca en V29–V30.
- 11 404 vértices movidos (y ≥ 0.551), con un máximo de 13 mm·u. Quiebres de boca/quijada: PASS 0.77 (igual que V30).

## Probado y descartado

- Campo sin proteger la cara: deformaba párpados y ojos (capas con separaciones de décimas de mm) e inflaba las mejillas.

- **Admin (18 oct 2026, 09:56):** "Me gusta la cabeza" → cabeza afilada aprobada; las manos siguen en trabajo (V34).
