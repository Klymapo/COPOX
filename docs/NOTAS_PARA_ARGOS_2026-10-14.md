# Notas de Elio (Claude) para Argos · 14 oct 2026

Hola, Argos. Te paso el relevo de lo que hicimos hoy con Mario (Admin) en COPOX. Lo técnico completo está en `docs/MANIQUI_HIBRIDO_2026-10-14.md`; aquí va lo que te ahorra tiempo.

## Dónde quedó

- **Alastor Delta** (`assets/alastor_delta/alastor_delta.glb`) es la versión aprobada como base del personaje. Le gusta a Mario. No lo sobrescribas; trabaja en copias con versión (`v1.1`, `v1.2`…).
- **Maniquí v0.2** (`assets/maniqui/maniqui_v0_2.glb`) es el primer avatar de la "biblioteca": un cuerpo gris con rig, al que luego se le ponen piel, cara, pelo y ropa por piezas. La idea de Mario es la de las series animadas: pocos cuerpos base y ropa intercambiable.
- **Ropa de Alastor** (`assets/maniqui/ropa_alastor_v0.glb`), en 10 piezas con el mismo esqueleto.
- Todo se regenera con `bash tools/maniqui/run_pipeline.sh` en unos 40 s, sin Blender. Comprobado que sale idéntico.

## Lo siguiente que pidió o falta

1. **Cabeza del maniquí**: Mario quiere una cabeza redonda y calva (ya está) **sin restos**. Falta parchar la banda entre la ceja y la oreja, donde quedan pedazos de la cara de Gamma. No intentes borrarlos: deja la cara hueca. Hay que generar una superficie nueva que una el borde de la bola con la cara.
2. Después, en el orden que propuso Mario: proporciones del brazo y la mano, luego animaciones (correr, sprint, salto), luego piel, cara y pelo, y al final ropa con física.
3. Gestos: los ojos van como **textura deslizante** (decisión de Mario). Quiere ver a Theo poner los ojos en blanco y a Alastor soplar su café.

## Cómo le gusta trabajar a Mario (importante)

- **Presupuesto cero**: nada de suscripciones, APIs de pago ni tokens.
- **Todo movimiento** en el Drive de Gaston (gstn762) o en GitHub Klymapo se anota en el **Registro de cambios** del reporte maestro correspondiente (aquí: "01 — COPOX · Memoria maestra integral" en `APPS/COPOX`), con la fecha y lo que cambió.
- Carpetas de Drive **en MAYÚSCULAS**. **No borrar nada** sin preguntar: lo que sobre va a la papelera.
- Antes de decir que algo está pendiente, **verifícalo en el repo o en Drive**, no en un reporte viejo.
- Quiere respuestas directas y honestas. Si algo quedó peor, dilo; él lo nota en las imágenes.
- Con "Dispara" quiere que le hagas preguntas antes de actuar.

## Trampas que ya pisé (para que no las repitas)

- Él detecta problemas que las métricas no ven: la mandíbula, un bulto en la nuca, un doble cuello. **Muéstrale acercamientos** de la zona que tocaste, no solo las 4 vistas.
- La regla de 3 iteraciones con criterio medible (IoU ≥ 95 % en 4 vistas) le dio confianza. Úsala: si no llega en 3, cambia de método en vez de insistir.
- `spec/alth_spec.json` y `CLAUDE.md` asumen 1 u = 1 mm y Z-up; estos GLB son Y-up en metros. Decláralo si los auditas con COPOX.
- La rama es `propuesta-*`, así que no se fusiona a `main` sin la aprobación de Mario.

Suerte. — Elio
