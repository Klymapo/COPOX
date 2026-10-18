# Adán V25 · boca sin surcos y orejas nuevas (SIN APROBAR)

- **Base:** Adán V22 HABLA → V24 → V25. **Resultado:** `ADAN_V25.glb`, SHA-256 `cf0e60d52c23ba55e68f2d20d2b54c6369b42c35c2fc40c2a17a2ec3b8f79844` (no se sube al repo).
- **Receta:** `docs/medicion/receta_adan_v25.py ADAN_V22_HABLA.glb ADAN_V25.glb` (~6 s; corre V24 por dentro).

## Boca: los surcos

Encontrados con CHXP en modo curvatura y en Godot de cerca:
1. El borde de la rendija era dentado (vértices a alturas desparejas, ±0.3 mm·u).
2. Bandas cóncavas arriba y abajo de los labios.
3. Al abrir, el labio de arriba arrastraba una franja angosta que se doblaba en surco.

Arreglo:
- Los dos bordes de la rendija se ajustan a curvas suaves (y = a + b·x² + c·x⁴) y se juntan en las comisuras.
- Anillo alrededor de la boca: Laplaciano (aplana el bulto y el surco) + Taubin (pule sin encoger). El borde solo se mueve en z. La copa negra sigue a su borde. Normales recalculadas soldando costuras.
- Caídas del campo de la boca más anchas (labio de arriba 0.12→0.24 ED, labio de abajo 0.08→0.16, comisuras 0.15→0.25).
- Dientes y lengua se vuelven a meter 4 mm·u detrás de la piel nueva.

Probado y descartado: aplanar los labios contra una superficie ajustada (la boca quedaba hundida 7 mm·u o asomaba la pared de adentro) y pintar la pared de adentro (manchas).

## Orejas (SENKU · `copox/medicion/orejas.py`)

Medidas en unidades del ojo, contra la Hoja de vistas de perfil:

| Medida | V24 | V25 | Referencia |
|---|---|---|---|
| Alto (ojos) | 1.03 | 1.43 | 1.39 |
| Ancho / alto | 0.70 | 0.75 | 0.72 |
| Arriba de la oreja bajo el ojo (ojos) | 0.30 | 0.20 | 0.22 |
| Sobresale de la silueta (ancho de cabeza) | 0.09 | 0.08 | 0.08 |

Oreja nueva: rectángulo vertical con esquinas redondeadas (superelipse n=5), bisel suave, hueco de 0.27 × 0.46 corrido hacia la cara y sombreado por color de vértice, inclinada 6° hacia atrás, apoyada en la piel (sin rendija) y pesada 100 % a Head. La caja vieja y la ranura en C se pliegan dentro de la cabeza.

## Pendiente conocido

- Queda un bulto leve de labio de arriba (más suave que en V24).
- Una muesca diminuta arriba del hueco de la oreja, solo visible muy de cerca.
