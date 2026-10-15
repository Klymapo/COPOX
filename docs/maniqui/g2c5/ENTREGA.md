# G2-C5 · Entrega de recuperación nasal (ensayos no aprobados)

Trabajo relacionado con PR #47. Los ensayos R1-R3 son independientes de los candidatos G2-C5 conservador/óptico previos, y parten de V3 exacta con B2 reaplicado. Los binarios GLB se guardan en Drive; no se versionan aquí para evitar duplicar modelos de 12 MB. Todos los hashes y límites están en `R1.json`, `R2.json`, `R3.json` y `VALIDACION.json`.

Resultados: R1 falla por cuatro cruces; R2 falla por seis aristas non-manifold nuevas y se rechaza visualmente; R3 mantiene conteo topológico local pero no repara suficientemente nariz/ojos y se rechaza visualmente. R2/R3 siguen sin aprobación y no forman una combinación.

Godot 4.7.2 importó la copia compatible R3, pero el skin-bake produjo cero vértices. La validación visual se hizo con renders de GLB reales importados en Blender 4.3.2. Las capturas Godot no están disponibles por el fallo de socket Xvfb documentado en `VALIDACION.json`.

- [Carpeta Drive de los GLB, código y bitácoras](https://drive.google.com/drive/folders/1iQOsDADU-AjOYp-vrNKnD0msNTmZB4Kq)
- [Comparativa visual B2/R2/R3](https://drive.google.com/file/d/16ZtxRYnsQEnwZd5k3mxq8V0WKztQq13I/view)
- [Capturas Blender y script de render](https://drive.google.com/file/d/1QEffUdjVzqGVgtn9RC_vvtVsSs19IX32/view)

No fusionar ni promover candidatos.
