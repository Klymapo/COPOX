"""Adán V47 (sobre V46.1): mano 15 % más chica, puño sin nudillos que sobresalgan, brazo recto y liso.

Pedido de Admin (19 oct 2026), en Lápiz y aprobado con "Adelante v47":
- "¿Podemos reducir un 15 % el tamaño de la mano?" Decisión: la punta del dedo queda más arriba de la entrepierna
  (el brazo no se alarga).
- "Cuando cierre el puño, que no se vean los nudillos sobresalir."
- "Mantener recto y liso las uniones de todo el brazo."
Qué hace:
1. Manos (abierta, puño, señalar) al 85 %: mismo estilo de V44 (dedos al largo de la hoja, abanico, pulgar a 40°).
2. Puño y señalar de bloque (mano_bloques._bloque): los dedos doblados son UNA caja redondeada, al ras del dorso, con cara
   plana al frente y ranuras leves entre dedos. Así no sobresale ningún nudillo. En señalar el índice sale recto.
3. Brazo recto (brazo_geo, lineal=True): del hombro a la muñeca los semiejes van en línea recta, sin bíceps ni cintura
   en el codo. La muñeca sigue la hoja del brazo (0.73 del brazo y 0.75 del ancho de la palma nueva): 6.4 × 6.6 cm
   (V46: 7.6 × 8.3 cm).
4. Codo sin esquina al doblar: entre brazo y antebrazo los pesos pasan en una rampa de 5 cm (V45: los transferidos de
   la malla vieja).
Pies, piernas, torso, short y cabeza: los de V46.1.
Uso: GODOT_BIN=… python receta_adan_v47.py ADAN_V46_1.glb ADAN_V47.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v44 as v44  # noqa: E402
import receta_adan_v45 as v45  # noqa: E402

ESCALA = 0.85                                   # mano: 85 % (Admin)
MUNECA = (0.032, 0.033)                         # semi alto, semi fondo de la muñeca (hoja del brazo)
BRAZO = dict(sigma=0.012, codo_max=0.0, p=2.6, lineal=True, muneca=MUNECA)
RAMPA_CODO = 0.050                              # u: ancho de la transición brazo → antebrazo en los pesos


_POSES_V44 = v44._poses


def _poses():
    from copox.medicion import mano_bloques as mb
    P = _POSES_V44()
    P["puno"] = {**P["puno"], "bloque": list(mb.DEDOS)}
    P["senalar"] = {**P["senalar"], "bloque": ["Middle", "Ring", "Little"]}
    return P


def pesos_codo(E):
    """En el brazo: hombro con los pesos transferidos; desde 5 cm del hombro, UpperArm → LowerArm en una rampa ancha."""
    from copox.medicion import torso_geo  # noqa: F401  (mismo orden de importación que v45)
    import receta_adan_v24 as v24
    nombres, H = v40.v38_skin(E)
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    for lado, s in (("Left", 1.0), ("Right", -1.0)):
        p = prims["Brazo" + lado[0]]
        V = v39._leer(E, p, "POSITION").astype(float)
        J = v39._leer(E, p, "JOINTS_0").astype(int); W = v39._leer(E, p, "WEIGHTS_0").astype(float)
        x = s * V[:, 0]
        iu, il = nombres.index(lado + "UpperArm"), nombres.index(lado + "LowerArm")
        xe = s * float(H[lado + "LowerArm"][0]); xu = s * float(H[lado + "UpperArm"][0])
        f = np.clip((x - (xe - RAMPA_CODO / 2)) / RAMPA_CODO, 0, 1); f = f * f * (3 - 2 * f)
        Ja = np.zeros_like(J); Wa = np.zeros_like(W)
        Ja[:, 0], Ja[:, 1] = iu, il
        Wa[:, 0], Wa[:, 1] = 1 - f, f
        m = np.clip((x - (xu + 0.010)) / 0.020, 0, 1); m = m * m * (3 - 2 * m)     # junto al hombro: los de antes
        Wd = np.zeros((len(V), len(nombres)))
        np.add.at(Wd, (np.repeat(np.arange(len(V)), 4), J.ravel()), (W * (1 - m[:, None])).ravel())
        np.add.at(Wd, (np.repeat(np.arange(len(V)), 4), Ja.ravel()), (Wa * m[:, None]).ravel())
        top = np.argsort(-Wd, axis=1)[:, :4]
        Wt = np.take_along_axis(Wd, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
        p["attributes"]["JOINTS_0"] = v24._add_raw(E, np.ascontiguousarray(top, np.uint16), 5123, "VEC4", 34962)
        p["attributes"]["WEIGHTS_0"] = v24._add_raw(E, np.ascontiguousarray(Wt, np.float32), 5126, "VEC4", 34962)
    E.b = bytes(E.out)
    return {"operacion": "pesos del codo", "rampa": RAMPA_CODO}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    carpeta = os.path.dirname(os.path.abspath(dst))
    b0, e0, p0 = dict(v45.BRAZO), v40.ESCALA_MANO, v44._poses
    v45.BRAZO.clear(); v45.BRAZO.update(BRAZO)
    v40.ESCALA_MANO = e0 * ESCALA
    v44._poses = _poses
    try:
        log = [v45.brazos(E, carpeta), pesos_codo(E), v45.manos(E, carpeta)]
    finally:
        v45.BRAZO.clear(); v45.BRAZO.update(b0)
        v40.ESCALA_MANO = e0
        v44._poses = p0
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V47: mano 85 %, puño de bloque, brazo recto. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print({k: v for k, v in x.items() if not k.startswith("perfil")})
