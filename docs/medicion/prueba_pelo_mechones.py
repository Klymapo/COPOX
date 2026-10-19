"""PRUEBA de pelo por mechones (no es versión de Adán): mismo proceso que la receta V48.3, pero el pelo es la cáscara de
V48.3 + mechones gruesos tipo Theo (copox/medicion/pelo_mechones.py). Módulo de prueba: se compara contra V48.3.
Uso: GODOT_BIN=… python prueba_pelo_mechones.py ADAN_V47.glb ADAN_V48_3_MECHONES_PRUEBA.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v48_3 as v483  # noqa: E402

TRIS_MECHONES = 16000


def main(src, dst):
    from copox.medicion import pelo_cascara as pc
    from copox.medicion import pelo_mechones as pm
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    clase0 = pc.PeloOrilla

    class ConMechones(clase0):
        """PeloOrilla cuya malla es la de los mechones; techo() (bordes) sigue siendo el de la cáscara base."""

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._m = pm.PeloMechones(self)

        def malla(self, paso=0.0011, pulido=2):
            return self._m.malla(paso=paso, pulido=pulido)

        def normales(self, V, h=0.0004):
            return self._m.normales(V, h)

    pc.PeloOrilla = ConMechones
    t0, o0 = v483.TRIS_PELO, v483.ORILLA_PULIDO
    v483.TRIS_PELO, v483.ORILLA_PULIDO = TRIS_MECHONES, 0
    try:
        E = re.Editor(src)
        carpeta = os.path.dirname(os.path.abspath(dst))
        log = [v483.nuca_piel(E), v483.frente(E), v483.pelo(E, carpeta), v483.cerrar_bordes(E)]
    finally:
        pc.PeloOrilla = clase0
        v483.TRIS_PELO, v483.ORILLA_PULIDO = t0, o0
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    E.b = bytes(E.out)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="PRUEBA de pelo por mechones sobre Adán V48.3. No es versión del personaje.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
