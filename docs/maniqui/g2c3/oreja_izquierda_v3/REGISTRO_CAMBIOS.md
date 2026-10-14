# COPOX · G2-C3 V3 · Rapado mínimo tras oreja izquierda

**Fecha:** 2026-10-14  
**PR experimental:** #46 (borrador)  
**Modelo de origen:** V2 `completo_v2` SHA256 `b7998d382f13ef8997a2dc2f73539a61da9ec5aa27605897534b13d47f3517e6`  
**Región autorizada:** isla topológica pequeña posterior a la oreja izquierda, no la oreja misma.

## Diagnóstico anatómico
En V2 se retiró una isla desconectada de **46 caras** tras oreja izquierda, pero quedó otra de **8 triángulos** separada a mayor profundidad posterior. Sus límites observados en la segmentación de r3 son:
- X `[-0.222786, -0.199735]`
- Y `[0.703391, 0.734685]`
- Z `[-0.131243, -0.105095]`

La isla de 8 triángulos es independiente de la primitiva craneal y de la conectividad del cuerpo principal de la cara y oreja. Su identificación usa la malla V2, no una estimación de la imagen.

## Operación ejecutable
`tools/maniqui/g2c3_v3_rapar_mechon_izquierdo.py`:

1. Recuperar V2 GLB desde r3 por el pipeline exacto y exigir su SHA256 anterior.
2. Identificar componente de exactamente 8 triángulos conectado por posiciones redondeadas solo para análisis.
3. Verificar que sus límites coinciden con la isla registrada en las seis coordenadas y que no comparte índices ni posiciones con el resto de la cabeza.
4. Reconstruir **solo el accessor de índices de triángulos** de la primitiva `Cabeza` eliminando las 8 referencias de cara; no borrar ni mover vértices ni editar ningún atributo.
5. Exportar V3 con nuevo nombre `maniqui_v0_3_r3_g2c3_v3_rapado_oreja_izquierda_SIN_APROBAR.glb`.
6. Comprobar que el buffer V2 completo es prefijo byte-identical, la primitiva `Craneo` y todos los materiales, clips, huesos, nodos y morph targets permanecen idénticos.
7. Obtener seis vistas reales antes/después, primeros planos en 4 cámaras con medición pixelar y prueba de importación Godot 4.7.2.

## Seguridad y límites
- Bloqueo estricto si la isla cambia de tamaño o posición, o si hay una cara/vértice compartido.
- No hay modificación de la oreja, cuero cabelludo, cara, ni del modelo V2 original.
- El cambio no promete unión craneofacial ni corrige canales faciales huérfanos.
- Una importación correcta **no** es aprobación artística. La V3 no se integra sin autorización.

## Evidencia
Workflow `.github/workflows/maniqui-g2c3-v3-oreja-izquierda.yml` y resultados, cuando CI termine, en `docs/maniqui/g2c3/oreja_izquierda_v3`, además de un artifact GLB sin aprobar.

## REGISTRO DE CAMBIOS
2026-10-14 — Creada rama experimental `experimentos/g2c3-v3-rapado-detras-oreja-izquierda` desde cabeza de PR #45, sin fusionar. Nuevo script y prueba de comparación Godot de V2 contra V3. **Estado inicial: CI solicitado, pendiente de verificar ejecución**, preservar todo trabajo anterior.
