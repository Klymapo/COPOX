"""Chequeo del entorno antes de construir o auditar (19 oct 2026).

Lección: sin GODOT_BIN, `simplificar()` devolvía la malla densa SIN AVISAR (GLB de 150 MB, SHA distinto). Aquí se
resuelve Godot (variable o ruta conocida), se revisan xvfb-run y los repos hermanos, y se FALLA con un mensaje claro.

Uso:  python -m copox.entorno            (imprime el estado; código 1 si falta algo obligatorio)
      from copox import entorno; entorno.preparar()   (exporta GODOT_BIN si lo encuentra; lanza si falta)
"""
from __future__ import annotations

import json
import os
import shutil
import sys

GODOT_CONOCIDOS = ("/home/claude/godot/Godot_v4.7.2-stable_linux.x86_64",)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELOS = os.environ.get("COPOX_MODELOS", os.path.join(os.path.dirname(RAIZ), "copox-modelos"))
CAPTURAS = os.environ.get("COPOX_CAPTURAS", os.path.join(os.path.dirname(RAIZ), "wt-cap"))
BASE = os.path.join(MODELOS, "adan", "ADAN_BASE_CONGELADA.glb")
BASE_SHA = "0422ae54636b3d40c235c4d3b412163027ea67b1f2e3521a09008a5e20164f43"


class EntornoIncompleto(RuntimeError):
    pass


def godot():
    g = os.environ.get("GODOT_BIN", "")
    if g and os.path.exists(g):
        return g
    for c in GODOT_CONOCIDOS:
        if os.path.exists(c):
            return c
    return ""


def sha256(ruta):
    import hashlib
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def estado(verificar_base=False):
    g = godot()
    e = {"godot": g or None, "xvfb_run": shutil.which("xvfb-run"), "copox_modelos": os.path.isdir(MODELOS) and MODELOS,
         "capturas": os.path.isdir(CAPTURAS) and CAPTURAS, "base_congelada": os.path.exists(BASE) and BASE,
         "calidad": os.environ.get("ALTH_CALIDAD", "final")}
    if verificar_base and e["base_congelada"]:
        e["base_sha_ok"] = sha256(BASE) == BASE_SHA
    return e


def preparar(necesita=("godot", "xvfb_run"), verificar_base=False):
    """Exporta GODOT_BIN y revisa lo obligatorio. Lanza EntornoIncompleto con la lista de faltantes."""
    e = estado(verificar_base)
    if e["godot"]:
        os.environ["GODOT_BIN"] = e["godot"]
    faltan = [k for k in necesita if not e.get(k)]
    if verificar_base and e.get("base_sha_ok") is False:
        faltan.append("base_congelada (SHA distinto: alguien la modificó)")
    if faltan:
        raise EntornoIncompleto("Falta en el entorno: " + ", ".join(faltan) + ". Godot 4.7.2 va en "
                                + GODOT_CONOCIDOS[0] + " (o exporta GODOT_BIN); xvfb-run: apt install xvfb.")
    return e


if __name__ == "__main__":
    e = estado(verificar_base=True)
    print(json.dumps(e, indent=2, ensure_ascii=False))
    ok = e["godot"] and e["xvfb_run"] and e.get("base_sha_ok", True)
    sys.exit(0 if ok else 1)
