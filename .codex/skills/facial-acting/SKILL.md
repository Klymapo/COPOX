---
name: facial-acting
description: Implementa gestualidad conversacional, parpadeo, mirada, mandíbula y labios del personaje con poses y animaciones validadas contra todas las referencias faciales proporcionadas.
---

# Facial Acting · microgestos y diálogo

1. Catalogar **todas** las referencias faciales del personaje (frontal, 3/4, ambos perfiles, expresiones, habla, duda, intimidación, observación y fotogramas/vídeos). No confundir estilo de otra persona con el personaje objetivo.
2. Determinar implementación: blendshapes de párpados/cejas/boca, huesos, texturas de iris desplazables y/o mandíbula. Antes de editar, inspeccionar qué morph targets realmente existen; las animaciones de cuerpo conservadas no garantizan expresiones.
3. Separar mirada, cejas, párpados, mejillas, labios, mandíbula, barbilla y tensión cervical. Registrar prioridades y máscaras anatómicas; no desplazar inadvertidamente orejas o romper unión craneofacial.
4. Preparar visemas/phonemes de habla, pausas, respiración, movimientos de mandíbula, sincronía y microexpresiones; preservar la identidad facial chibi-soft y evitar expresiones demasiado tiernas cuando el brief pide sobriedad.
5. Probar oclusiones, z-fighting, clipping de párpados, dientes/lengua, rotación de iris y penetración durante habla. Incluir extrema izquierda/derecha de ojo, parpadeo completo, boca abierta y gestos.
6. Ejecutar `visual-critic` por **cada** expresión, ángulo y fotograma aportado; una vista frontal correcta no absuelve el perfil. Con referencias parciales, señalar `REVIEW_REQUIRED`.
7. Entregar GLB versionado, curva/facial rig, atlas/UV o shape keys, hoja de expresiones multivista y prueba Godot cuando exista. No destruir morph targets ni aprobar sin Admin.

**Nota:** rig heredado y lipsync futuro requieren contratos independientes; no declarar instaladas capacidades no implementadas.

