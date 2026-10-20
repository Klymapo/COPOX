#!/usr/bin/env bash
# Blender (bpy) en GitHub Actions: intenta tools/ensure_blender.sh y, si falla, instala el bpy más reciente que
# PyPI tenga para Python 3.11/3.13 sin fijar versión. Deja `alth-python`. Los errores salen como anotaciones
# (::error::) porque los logs completos no siempre se pueden leer desde la sesión.
set -u
bash tools/ensure_blender.sh && command -v alth-python >/dev/null && alth-python -c "import bpy" 2>/dev/null && exit 0
echo "::warning::ensure_blender.sh no dejó bpy; pruebo bpy sin versión fija"
tail -n 8 /tmp/alth-install.log 2>/dev/null | while read -r l; do echo "::warning::install.log: ${l:0:180}"; done
pip install -q uv >/dev/null 2>&1 || true
for py in 3.11 3.13 3.12; do
  rm -rf "$HOME/.bpy"
  if uv venv -q --python "$py" "$HOME/.bpy" >/tmp/bpy_ci.log 2>&1 && uv pip install -q --python "$HOME/.bpy/bin/python" bpy numpy scipy pillow >>/tmp/bpy_ci.log 2>&1; then
    if "$HOME/.bpy/bin/python" -c "import bpy; print(bpy.app.version_string)" >>/tmp/bpy_ci.log 2>&1; then
      printf '#!/bin/sh\nexec "%s/bin/python" "$@"\n' "$HOME/.bpy" | sudo tee /usr/local/bin/alth-python >/dev/null
      sudo chmod +x /usr/local/bin/alth-python
      echo "::notice::Blender listo con Python $py: $(alth-python -c 'import bpy; print(bpy.app.version_string)')"
      exit 0
    fi
  fi
  tail -n 4 /tmp/bpy_ci.log | while read -r l; do echo "::warning::py$py: ${l:0:180}"; done
done
echo "::error::No se pudo instalar bpy en ningún Python"
exit 1
