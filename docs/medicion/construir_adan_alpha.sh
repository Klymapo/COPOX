#!/usr/bin/env bash
# Reconstruye ADÁN ALPHA (= Adán V21) desde Adán V10 con las recetas del repo.
# Uso: construir_adan_alpha.sh ADAN_V10_ESTILO.glb carpeta_salida
# Cadena completa documentada en docs/ADAN_ALPHA.md (V04 → V05 → … → V10 → V21).
set -euo pipefail
R="$(cd "$(dirname "$0")" && pwd)"; IN="$1"; OUT="$2"; mkdir -p "$OUT"
py(){ python3 "$@"; }
(cd "$R/../.." && py -m copox.medicion.compactar "$IN" "$OUT/ADAN_V10c.glb" >/dev/null)
(cd "$R/../.." && py -m copox.medicion.orientar "$OUT/ADAN_V10c.glb" "$OUT/ADAN_V11.glb")
prev="$OUT/ADAN_V11.glb"; n=12
for v in 05 06 07 08 09 10 11 12 13 14; do
  py "$R/receta_theo_v$v.py" "$prev" "$OUT/ADAN_V$n.glb" --solo-estilo >/dev/null
  prev="$OUT/ADAN_V$n.glb"; n=$((n+1))
done
cp "$prev" "$OUT/ADAN_ALPHA.glb"
sha256sum "$OUT/ADAN_ALPHA.glb"
