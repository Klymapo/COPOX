# Auditoría artística de Adán V45, pieza por pieza (19 oct 2026)

**Método:** contrato `visual-critic` (skills de Argos). Revisor independiente de solo lectura.
- Se usaron todas las hojas de Adán: cuerpo, cabeza, torso, brazo, piernas y pies. La Hoja de vistas va como apoyo de proporción.
- V45 se puso en pose T con la cámara de cada vista. Cada vista se juzgó por separado, sin promedios.
- Evidencia: rama `capturas`, `capturas/2026-10-19/auditoria_v45/` (`par_*.png` = hoja | V45).

**Veredicto:** UNA_CORRECCIÓN (visual-critic: ISSUES_FOUND). No es aprobación.

| # | Pieza | Resultado | Lo principal |
|---|---|---|---|
| 1 | Cabeza y cara | PASS | Igual a la hoja; aprobada desde V33 |
| 2 | Pelo (solo defectos) | ISSUE | Motas en el borde de la nuca, picos detrás de las orejas, manchas color piel sobre la oreja, escalón horizontal en la parte baja del pelo por detrás |
| 3 | Cuello | PASS | Nuca lisa, no asoma la boca |
| 4 | Torso | PASS | Liso. Pierde algo de lectura de hombro frente a los planos de la hoja (opinión) |
| 5 | Brazo | ISSUE menor | Posible esquina a media altura del brazo y escalón tipo hombrera en pose A (revisar el skinning) |
| 6 | Muñeca | ISSUE | Pliegue en la base de la palma; en puño y señalar, el contorno de la muñeca sale ondulado |
| 7 | Mano abierta | PASS | Como la hoja; sin la V del dorso |
| 8 | Puño | ISSUE | Nudillos fundidos con bultos; debería ser de bloques limpios |
| 9 | Señalar | ISSUE | Dedos doblados fundidos; misma base que el puño |
| 10 | Short | ISSUE (pruebas de ropa) | Entrepierna baja (se lee como falda), falta la costura trasera. Al correr y en Dash: dobladillo roto y el muslo atraviesa la tela |
| 11 | Piernas | PASS | Aprobadas en V42 |
| 12 | Tobillo | ISSUE (bloqueo principal) | Aro tipo calcetín. En la hoja, el tobillo es lo más ancho y el talón se bisela hacia la planta |
| 13 | Pie y dedos | ISSUE | Caja alta con aletas a los lados y la planta más ancha. En la hoja es una cuña baja en diagonal |
| 14 | Cuerpo completo | ISSUE (por los pies) | Identidad clara a distancia de juego |
| 15 | Movimiento (Godot) | ISSUE (short) | Walk, Jump, Punch y PointFwd limpios; Run y Dash fallan por el short |

**Peor discrepancia:** pie y tobillo.

**Orden de corrección recomendado:**
1. Pierna baja y pie como una sola pieza por secciones, siguiendo la hoja de pies.
2. Puño y señalar.
3. Borde del pelo.
4. Codo y hombro en pose A.
5. Short, en las pruebas de ropa.

**Cámaras dudosas:**
- SIDE de cuerpo, cabeza y torso: la hoja está girada unos grados.
- Brazo FRONT y BACK: vistos desde abajo y desde arriba.
- Puño y señalar no tienen hoja de Adán.
