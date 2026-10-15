# Reproducción gratuita G2-C4

Ejecutar desde la raíz de la rama G2-C4. Requiere Python con numpy/scipy/
Pillow, Node con gltf-validator 2.0.0-dev.3.10, Godot4.7.2 y Xvfb. No APIs
generativas, licencias de pago ni servicios de render de pago.

1. Recuperar el GLB V3 del artefacto 11924734007 y copiarlo a
   `assets/maniqui/maniqui_v0_3_r3_g2c3_v3_rapado_oreja_izquierda_SIN_APROBAR.glb`.
   Alternativa si expiró el artefacto: `python -m tools.maniqui.g2c3_v3_rapar_mechon_izquierdo`.
   Esta alternativa reconstruye el pipeline histórico, pero G2-C4 NO edita
   r3; exige el SHA exacto de V3 antes de toda operación.
2. `python -m tools.maniqui.g2c4_inspect`
3. `python -m tools.maniqui.g2c4_candidates`
4. `python tools/maniqui/g2c4_refine.py`
5. `python tools/maniqui/g2c4_intersections.py`
6. `python tools/maniqui/g2c4_prepare_qa.py`
7. Con GODOT apuntando al ejecutable 4.7.2:
   `xvfb-run -a "$GODOT" --path build/g2c4/godot --rendering-method gl_compatibility --audio-driver Dummy --script res://qa.gd > build/g2c4/godot/qa_v3.log 2>&1`
8. Con gltf-validator accesible a Node:
   `node tools/maniqui/g2c4_validate.cjs`
9. `python -m unittest discover -s tests -p 'test_regional_nape.py' -v > build/g2c4/regional_tests.log 2>&1`
10. `python tools/maniqui/g2c4_sheets.py`
11. `python tools/maniqui/g2c4_finalize.py`

Se niega sobrescribir GLBs existentes. Para reproducir, usar un checkout
nuevo o conservar la carpeta build anterior con otro nombre. Los reportes
JSON son derivados regenerables; V3 y los GLB producidos son inmutables.

Los valores regionales de `profile()` son mediciones particulares de V3 y
su referencia UV. Para otro personaje hay que medir, identificar y revisar
sus regiones antes de usar `delete_faces()` o el ajuste de borde. La
coincidencia por textura/proximidad no constituye una regla universal.

`g2c4_finalize.py` pasa comprobaciones de regresión y CONSERVA estados
RECHAZADO. No convierte un resultado técnico en aprobación artística,
no fusiona, no promueve, no genera ABC con candidatos vetados.
