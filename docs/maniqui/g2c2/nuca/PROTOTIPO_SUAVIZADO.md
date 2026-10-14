# G2-C2-R · Nuca: alternativa de curvatura gradual (sin aprobación)
Fecha: 2026-10-14. PR #44 borrador. Nunca fusionar ni reemplazar r3 sin permiso.

## Propósito
El prototipo anterior produce una banda posterior de grosor demasiado uniforme. Es control técnico y se conserva idéntico. Añadimos perfil `eased` con dos anillos de transición, caída vertical 50–100% en el arco, alisado gradual de extremos y acercamiento radial progresivo. Mantiene la primitiva `Cabeza`, facciones y otros assets congelados.

## Límites honestos
No hay soldadura con Cara ni cuello, no cierre watertight, no corrección de morph targets faciales huérfanos ni garantía de estética superior. Más polígonos no implican automáticamente mejor likeness. Puede seguir viéndose la nueva nuca a través de agujeros antiguos de la cara en vista frontal.

## Evaluación y custodia
`flat` conserva la geometría histórica y sus capturas. `eased` escribe un GLB hijo con nombre nuevo, informe de hash y cuatro vistas en `docs/maniqui/g2c2/nuca/suavizada/`. Ambos se quedan en artifacts temporales de GitHub Actions sin promoverse. Gates: 56 huesos, 29 definiciones, originales intocados, sin triángulos degenerados ni aristas nonmanifold añadidas; revisión visual separada, Godot para la nueva variante todavía por ejecutar. Usar solo NumPy, SciPy, Pillow y Actions gratis.

## Registro de cambios
- 2026-10-14 · Argos: perfil alternativo `eased`, cobertura curvada de nuca en dos anillos, unit tests y CI de generación/comparación. Todas las fuentes y modelos aprobados siguen intactos. Estado inicial: experimental, sujeto a CI y revisión artística.

- 2026-10-14 · QA preliminar: CI #38623498481 detectó expectativa de prueba incorrecta: dos anillos crean 132 bordes abiertos frente a 130 del control (dos laterales adicionales). No se marcó watertight. Se corrigió el test y se mantuvieron idénticas las leyendas de capturas del control flat para no reescribir visualmente el experimento histórico.
