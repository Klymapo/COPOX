"""Adán V28 (sobre V22 HABLA → V27): movimiento — caminar, correr, saltar, dash, puñetazos y señalar.

Clips nuevos hechos por código (copox/movimiento/locomocion.py):
  Walk-loop (1.0 s) y Run-loop (0.6 s): piernas con IK de dos huesos y pie plantado; el tobillo de apoyo se
    mueve hacia atrás a velocidad constante → en el juego el personaje avanza a esa velocidad y los pies
    no patinan: caminar 0.259 u/s, correr 0.834 u/s (Adán mide 0.848 u).
  Jump (1.0 s): agacharse, impulso, aire, caída, aterrizaje (la cadera sube 0.20 de alto).
  Dash (0.55 s): arranque inclinado, piernas en tijera, brazos atrás, puños.
  Punch_R / Punch_L (0.6 s): guardia, golpe recto con giro de cadera, regreso; puños cerrados.
  Point, M31_4_Senalar, M34_5_Tableta: índice estirado de verdad.
Uso: python receta_adan_v28.py ADAN_V22_HABLA.glb ADAN_V28.glb
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.movimiento import locomocion  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v27 as v27  # noqa: E402


def main(src, dst):
    t27 = dst + ".v27.glb"; t = dst + ".tmp.glb"
    v27.main(src, t27)
    clips = locomocion.escribir(t27, t)
    asentado = locomocion.asentar(t)
    compactar(t, dst)
    os.remove(t); os.remove(t27)
    return clips, asentado


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2]))
