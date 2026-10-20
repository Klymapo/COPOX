"""Labios desde la voz: Rhubarb Lip Sync (CPU, local) → visemas ALTH (vis_A…vis_FV) (20 oct 2026).

Ruta AAA §6.2. En español se usa el reconocedor FONÉTICO de Rhubarb (`-r phonetic`): el de PocketSphinx sólo entiende
inglés. Con el guion (--dialogo) mejora la precisión.

  python -m copox.movimiento.labios AUDIO.wav --glb PERSONAJE.glb --clip Habla_Escena3 --salida OUT.glb
         [--rhubarb /ruta/rhubarb] [--dialogo guion.txt] [--fps 30] [--emocion Cara_Base] [--json cues.json]

Formas de Rhubarb → morphs ALTH (la cara ya trae vis_A, vis_E, vis_I, vis_O, vis_U, vis_MBP, vis_FV):
  A (M, B, P cerrada) → vis_MBP         B (K, S, T, dientes)  → vis_I .7 + boca_dientes .3
  C (E abierta)       → vis_E           D (A muy abierta)     → vis_A + mandibula .4
  E (O redonda)       → vis_O           F (U, W fruncida)     → vis_U
  G (F, V)            → vis_FV          H (L larga)           → vis_E .5 + mandibula .25
  X (reposo)          → nada
Coarticulación: cada forma entra en 60 ms y sale en 80 ms (rampas suaves), así no «parpadea» la boca.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess

import numpy as np

FORMAS = {
    "A": [("vis_MBP", 1.0)], "B": [("vis_I", 0.7), ("boca_dientes", 0.3)], "C": [("vis_E", 1.0)],
    "D": [("vis_A", 1.0), ("mandibula", 0.4)], "E": [("vis_O", 1.0)], "F": [("vis_U", 1.0)],
    "G": [("vis_FV", 1.0)], "H": [("vis_E", 0.5), ("mandibula", 0.25)], "X": [],
}


def rhubarb(audio, binario=None, dialogo=None):
    b = binario or os.environ.get("RHUBARB_BIN") or shutil.which("rhubarb")
    if not b:
        raise FileNotFoundError("falta el binario de Rhubarb (RHUBARB_BIN o --rhubarb)")
    cmd = [b, "-f", "json", "-r", "phonetic", "--extendedShapes", "GHX", "-q", audio]
    if dialogo:
        cmd[1:1] = ["--dialogFile", dialogo]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)["mouthCues"]


def cues_a_pesos(cues, morphs, fps=30, entrada=0.06, salida=0.08, intensidad=1.0):
    """mouthCues [{start, end, value}] → pesos [n, len(morphs)] con rampas de entrada/salida."""
    dur = max(c["end"] for c in cues) if cues else 0.0
    n = int(np.ceil(dur * fps)) + 1
    t = np.arange(n) / fps
    idx = {m: i for i, m in enumerate(morphs)}
    P = np.zeros((n, len(morphs)))
    for c in cues:
        forma = FORMAS.get(c["value"], [])
        if not forma:
            continue
        a, b = float(c["start"]), float(c["end"])
        sube = np.clip((t - (a - entrada)) / entrada, 0, 1)
        baja = np.clip(((b + salida) - t) / salida, 0, 1)
        env = np.minimum(sube, baja)
        env = env * env * (3 - 2 * env)
        for m, g in forma:
            if m in idx:
                P[:, idx[m]] = np.maximum(P[:, idx[m]], g * env * intensidad)
    return t, np.clip(P, 0, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Voz → clip de labios ALTH (Rhubarb, CPU)")
    ap.add_argument("audio")
    ap.add_argument("--glb", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rhubarb")
    ap.add_argument("--dialogo")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    from copox.medicion.rostro_edicion import Editor
    from copox.movimiento import clip_gltf as cg
    cues = rhubarb(a.audio, a.rhubarb, a.dialogo)
    E = Editor(a.glb)
    morphs = cg.nombres_morphs(E)
    t, P = cues_a_pesos(cues, morphs, a.fps)
    cg.agregar_clip_morphs(E, a.clip, t, P)
    E.log.append({"operacion": "labios desde audio (Rhubarb fonético)", "clip": a.clip, "cues": len(cues)})
    E.guardar(a.salida, nota=f"Clip de labios {a.clip}. SIN APROBAR.")
    if a.json:
        json.dump({"cues": cues, "fps": a.fps}, open(a.json, "w"))
    print(json.dumps({"clip": a.clip, "cues": len(cues), "segundos": float(t[-1]) if len(t) else 0}))


if __name__ == "__main__":
    main()
