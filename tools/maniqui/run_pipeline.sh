#!/usr/bin/env bash
# Reproduce la cadena Beta + Gamma -> Alastor Delta -> v1.1 -> maniquí v0.2 + ropa -> maniquí v0.7 (cabeza canónica).
# Sin Blender: solo Python 3 + numpy + Pillow. Correr desde la raíz del repo:
#   bash tools/maniqui/run_pipeline.sh [carpeta_salida]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/models/source/alastor"
OUT="${1:-$ROOT/build/maniqui}"
mkdir -p "$OUT"
cd "$ROOT/tools/maniqui"          # los scripts se importan entre sí por ruta relativa
PY="python3 -I"

BETA="$SRC/alastor_beta_juego.glb"
GAMMA="$SRC/alastor_gamma_30k_2k.glb"

echo "1/6 shrinkwrap por zonas + cabeza de Gamma (corte 0.55)"
$PY wrap2.py "$BETA" "$GAMMA" "$OUT/it4c.glb" 9 5 0.55
echo "2/6 trasplante de faldones, pantalón y zapatos -> Alastor Delta"
$PY wrap3.py "$OUT/it4c.glb" "$BETA" "$GAMMA" "$OUT/alastor_delta.glb"
echo "3/6 cuello nuevo (v1.1)"
$PY neck.py "$OUT/alastor_delta.glb" "$OUT/alastor_delta_v1_1.glb" 0.47
echo "4/6 maniquí v0 (sin pelo/lentes/ropa) + archivo de ropa"
$PY maniqui.py "$OUT/alastor_delta_v1_1.glb" "$OUT/it4c.glb" "$OUT/maniqui_v0.glb" "$OUT/ropa_alastor_v0.glb" "$BETA"
echo "4b/7 huesos: brazos 15 % más cortos y piernas 25 % más separadas (medido en Theo)"
$PY huesos.py "$OUT/maniqui_v0.glb" "$OUT/maniqui_v0_h.glb" UpperArm=0.85 LowerArm=0.85 UpperLeg.x=1.25 Shoulder.z+=0.050
echo "5/7 torso, pelvis, brazos y piernas de bloque (v0.1)"
$PY cuerpo.py "$OUT/maniqui_v0_h.glb" "$OUT/maniqui_v0_1.glb"
echo "6/7 manos (ref mano-con-regla) y botas (ref Theo) (v0.2)"
$PY manos_pies.py "$OUT/maniqui_v0_1.glb" "$OUT/maniqui_v0_2.glb"

echo "7/7 cabeza canónica ALTH medida de las referencias + cuerpo de bloques (v0.14)"
$PY medir_cara.py "$ROOT/refs/personajes/joven-rubio-4-vistas.jpg" "$OUT/theo_frente.json" --recorte 0,0,768,768
$PY medir_cara.py "$ROOT/refs/personajes/detective.jpg" "$OUT/alastor_34.json"
$PY cabeza.py "$OUT/maniqui_v0_2.glb" "$OUT/maniqui_v0_14.glb" rasgos/alastor.json      # cuerpo.py y manos_pies.py ya generan bloques redondeados (P_BOX)
$PY facezoom.py "$OUT/maniqui_v0_14.glb" "$OUT/maniqui_v0_14_cara.png"

echo "Previews:"
$PY render.py "$OUT/maniqui_v0_14.glb" "$OUT/maniqui_v0_14_4vistas.png" >/dev/null
$PY pose.py "$OUT/maniqui_v0_14.glb" Wave 0.6 "$OUT/maniqui_v0_14_wave.png" >/dev/null
$PY measure.py "$OUT/alastor_delta.glb" "$GAMMA" "$BETA" "$OUT/delta"
echo "Listo en $OUT"
