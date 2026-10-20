"""Escena de cine ALTH: esquema JSON, validación y reparto de cuadros entre jobs (sin bpy).

Ejemplo (docs/cine/ejemplo_escena.json):
{
  "nombre": "prueba_orbita",
  "glb": "assets/joven_rubio/theo_alpha.glb",          # ruta en el repo o "modelos:theo/THEO_VESTIDO_V4_2.glb"
  "clip": "Idle-loop",                                   # null = pose de reposo
  "cuadros": [1, 48], "fps": 24,
  "resolucion": [1280, 720], "muestras": 64,
  "visible": {"CAPA_SHORT": false},                      # además de KHR_node_visibility del GLB
  "camara": [                                            # cuadros clave (se interpolan); lente en mm
    {"cuadro": 1,  "pos": [1.6, 0.9, 2.2], "mira": [0, 0.45, 0], "lente": 50},
    {"cuadro": 48, "pos": [-1.6, 0.9, 2.2], "mira": [0, 0.45, 0], "lente": 50}
  ],
  "luz": "estudio_alth",                                 # key cálida + fill fría + rim + cielo gris suave
  "fondo": "#E3E2E9",
  "piso": true
}
Ejes: los del GLB (Y arriba, frente +Z). render_blender.py convierte a Blender (Z arriba).
"camara_relativa": true → pos/mira en unidades del alto del personaje, desde el centro de sus pies.
"eje_arriba": "z" para objetos ALTH históricos (Z arriba en los datos, p. ej. theo_alpha.glb).
"""
from __future__ import annotations

import json
import os

DEFECTO = {"clip": None, "cuadros": [1, 1], "fps": 24, "resolucion": [1280, 720], "muestras": 64, "visible": {},
           "luz": "estudio_alth", "fondo": "#E3E2E9", "piso": True, "dof": None,
           "camara_relativa": False, "eje_arriba": "y"}


def cargar(ruta):
    e = dict(DEFECTO)
    e.update(json.load(open(ruta)))
    validar(e)
    return e


def validar(e):
    faltan = [k for k in ("nombre", "glb", "camara") if k not in e]
    if faltan:
        raise ValueError(f"escena: faltan {faltan}")
    a, b = e["cuadros"]
    if not (1 <= a <= b):
        raise ValueError("escena: cuadros debe ser [inicio, fin] con 1 ≤ inicio ≤ fin")
    if not e["camara"]:
        raise ValueError("escena: la cámara necesita al menos un cuadro clave")
    for k in e["camara"]:
        for c in ("cuadro", "pos", "mira"):
            if c not in k:
                raise ValueError(f"escena: cuadro clave de cámara sin '{c}'")
    return True


def partes(e, n):
    """Reparte [inicio, fin] en n tramos contiguos (los jobs de Actions)."""
    a, b = e["cuadros"]
    total = b - a + 1
    n = max(1, min(int(n), total))
    base, resto = divmod(total, n)
    out, ini = [], a
    for i in range(n):
        tam = base + (1 if i < resto else 0)
        out.append([ini, ini + tam - 1])
        ini += tam
    return out


def camara_en(e, f):
    """Interpola la cámara (pos, mira, lente) en el cuadro f (lineal entre cuadros clave; suavizado smoothstep)."""
    ks = sorted(e["camara"], key=lambda k: k["cuadro"])
    if f <= ks[0]["cuadro"]:
        k = ks[0]; return k["pos"], k["mira"], k.get("lente", 50)
    if f >= ks[-1]["cuadro"]:
        k = ks[-1]; return k["pos"], k["mira"], k.get("lente", 50)
    for k0, k1 in zip(ks, ks[1:]):
        if k0["cuadro"] <= f <= k1["cuadro"]:
            t = (f - k0["cuadro"]) / max(k1["cuadro"] - k0["cuadro"], 1)
            t = t * t * (3 - 2 * t)
            lerp = lambda a, b: [x + (y - x) * t for x, y in zip(a, b)]        # noqa: E731
            return lerp(k0["pos"], k1["pos"]), lerp(k0["mira"], k1["mira"]), k0.get("lente", 50) + (k1.get("lente", 50) - k0.get("lente", 50)) * t


def resolver_glb(e, raiz, modelos=None):
    g = e["glb"]
    if g.startswith("modelos:"):
        if not modelos:
            raise FileNotFoundError("la escena pide un GLB de copox-modelos y no hay checkout de modelos")
        return os.path.join(modelos, g.split(":", 1)[1])
    return os.path.join(raiz, g)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Escena de cine: validar y repartir cuadros")
    ap.add_argument("escena")
    ap.add_argument("--partes", type=int, default=4)
    a = ap.parse_args()
    e = cargar(a.escena)
    print(json.dumps({"parte": list(range(len(partes(e, a.partes)))), "tramos": partes(e, a.partes)}))


if __name__ == "__main__":
    main()
