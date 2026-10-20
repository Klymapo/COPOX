---
name: investigar-referencias
description: Antes de modelar una parte del cuerpo, prenda, objeto o técnica geométrica nueva en ALTH-META/COPOX (o tras 3 iteraciones sin unanimidad), investiga referencias reales gratuitas y escribe el research brief que CHXP exige.
---

# Investigar referencias (COPOX)

Admin (19 oct 2026): "Integra el paso de búsqueda de referencias (como hiciste con la pelvis) como una skill a COPOX".
CLAUDE.md: "Antes de cada técnica geométrica nueva se exige un research brief válido; sin él, `RESEARCH_REQUIRED`."
Esta skill produce ese brief. Presupuesto cero: solo fuentes y herramientas gratuitas.

## Cuándo
- Parte del cuerpo, prenda, calzado, peinado, objeto o edificio que no tenga brief en `docs/investigacion/`.
- Técnica geométrica nueva (o cambio de técnica tras PLATEAU).
- El asset llega a 3 iteraciones sin pasar CHXP: investigar antes de la 4.ª.

## Pasos
1. **Buscar** (WebSearch/WebFetch; sin APIs de pago): anatomía o construcción real (anatomía artística, patronaje,
   partes del calzado, planos de arquitectura), medidas reales, y la referencia del proyecto (`refs/`, Drive "Heavy").
   Mínimo 2 fuentes independientes. Anotar URL y qué se tomó de cada una.
2. **Marcas visibles**: qué se ve desde fuera (no la estructura interna): bordes, pliegues, planos, volúmenes.
3. **Proporciones y medidas**: en mm reales → ALTH con `mm_alth = mm_real × 0.0559 × k` (`spec/alth_spec.json`,
   `conversion_k`). Indicar de dónde sale cada número.
4. **Simplificación ALTH**: qué marcas sobreviven en chibi-soft low-poly (sombreado plano, chaflán por tamaño, variación
   por cara 3 %) y cuáles se quitan. Una frase por decisión.
5. **Técnica**: cómo se construye con lo que ya hay (`copox/medicion/`: implícitas + `malla_banda`, `ropa_ajustada`,
   `pelo_bloques`, …) o qué módulo nuevo hace falta. Piezas, capas, nodos intercambiables, pesos.
6. **Revisiones para CHXP**: qué se mide y con qué umbral (silueta SENKU por vista/franja, penetraciones en poses,
   cobertura, apoyo, triángulos). Si una regla no se puede medir, va como checklist visual.
7. **Plan de prueba**: archivos, clips (Idle/Walk/Run/Jump/Sit), vistas, iteraciones máximas (3) y qué se entrega.
8. **Riesgos y dudas** para Admin (decisiones que no se pueden tomar solas).

## Entregable
`docs/investigacion/<tema>.md` con estas secciones: Fuentes · Marcas visibles · Medidas (real → ALTH) ·
Simplificación ALTH · Técnica · Revisiones CHXP · Plan de prueba · Riesgos/dudas. Fecha y "Brief válido: sí".
CHXP V3 (`copox/render/auditoria.py`, revisión `research_brief`) busca el brief del tema declarado; sin él la
técnica nueva queda en `RESEARCH_REQUIRED`.

## Reglas
- No inventar medidas: si una fuente no da número, decirlo y proponer cómo medirlo (SENKU contra la hoja).
- Las referencias de terceros solo se miden; no se copian mallas ni texturas.
- Registrar en el reporte maestro de Drive cualquier archivo nuevo en GitHub de Klymapo o en Drive de Gaston.
