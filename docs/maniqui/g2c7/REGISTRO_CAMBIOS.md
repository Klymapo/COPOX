# Registro de cambios · COPOX G2-C7 · 2026-10-15

Base: L1 (V3 + B2 + unión local de tobillos), SHA256
`cf759292adace095b0a0c41516e0ecebead3cb48efb44210afcbbef8cc8d71e0`.
No se modificaron ni sustituyeron V3, Gamma, Delta, Theo Alpha o L1.

| Región | Archivos | Cambio | Resultado |
|---|---|---|---|
| Ojos/cejas | `tools/maniqui/g2c7_restore_likeness_texture.py`, `docs/maniqui/g2c7/V1.json` | Primera restauración amplia desde atlas original. | V1 rechazado: superficies negras de pelo/gafas. GLB conservado. |
| Ojos/cejas y tono de piel | `tools/maniqui/g2c7_selective_features.py`, `docs/maniqui/g2c7/V2.json` | 674 triángulos con UV de procedencia exacta; resto de cara y calva con tono mediano medido. Ningún vértice ni peso modificado. | V2 mejora local, sin aprobación global. |
| Cara/nariz/mandíbula | `docs/maniqui/g2c7/INVESTIGACION.md`, `docs/maniqui/g2c7/RESULTADO.md` | Comparación Gamma/Delta/V3/B2/L1 y referencias. | Bloqueo documentado: huecos y discontinuidades existentes; no se ocultan con parche. |
| Cuello y miembros | Láminas y pruebas en `build/g2c7/`, paquete Drive. | Revisión visual e importación Godot; se conservan uniones de tobillos L1. | Sin mejora geométrica nueva; cuello/perfil suspenden. |

GLB V2 SHA256 `0efe44e912a23c2dfae2be850494d7e8a93475606af5e08ba49e69e536daed63`.
Capturas reales de Gamma/L1/V2, cuatro vistas, detalles y `Wave` están en
`build/g2c7/` y en [Drive](https://drive.google.com/drive/folders/1560pGpXPUpCsS04aQdPhaeJwDPrH4yGU).
Godot 4.7.2 importa la copia compatible con error 0; bruto error heredado 43.
56 huesos, 29 nombres de clip; 15 clips faciales siguen sin geometría de morph funcional.
Rama experimental G2-C7, PR borrador, sin fusión ni promoción.
