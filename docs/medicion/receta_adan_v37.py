"""Adán V37 (sobre V22 HABLA → V36): mano, segunda ronda de geometría — lo que dejó pendiente visual-critic.

1) Costura del dorso en la base del pulgar: el ancho de la palma variaba escalando z y eso aplastaba el redondeo
   del canto del lado del pulgar (canto vivo). Ahora el ancho cambia sin aplastar el redondeo (canto_fijo).
2) Membrana pulgar–índice más alta (como la mano con regla): lámina delgada entre la base del pulgar y el
   nudillo del índice, fundida con la palma.
3) Puños de frente más chicos que en la hoja de vistas: mano 8 % más grande (huesos, vértices y radios).
4) Agarre de la pistola (copox/movimiento/agarre.py, base para sostener objetos): la mano derecha y la pistola
   provisional se resuelven juntas (dedos rodeando el mango, palma apoyada, yema del índice en el gatillo, sin
   atravesar el arma). Se guardan: nodo AGARRE_PISTOLA (hijo de RightHand), clips Pistola_Agarre-loop y
   Pistola_Accion (aprieta el gatillo) y la curva del gatillo en los extras del nodo.
Usa los ganchos de la receta V36 (vacíos allá, así V36 se reproduce igual).
Uso: GODOT_BIN=… python receta_adan_v37.py ADAN_V22_HABLA.glb ADAN_V37.glb
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
import receta_adan_v36 as v36  # noqa: E402

ESCALA_MANO = 1.08
MEMBRANA_R = 0.0055


def membrana(H):
    a = H["LeftThumbProximal"]; b = H["LeftIndexProximal"]
    return (a, b, MEMBRANA_R * ESCALA_MANO)


PRONACION_V39 = None        # gancho V39 (sin efecto en V37/V38)


def clip_apuntar_pistola(A):
    """Apuntar con una mano: brazo derecho al frente y la mano girada (palma hacia adentro, nudillos en vertical) —
    así el arma queda derecha, con la corredera arriba. El brazo izquierdo descansa."""
    from copox.movimiento.locomocion import Clip
    ts = [0, .6, 1.2]
    c = Clip("Pistola_Apuntar-loop", 1.2, True)
    r_ = [0.06, 0.06, 1.0]
    c.mira("RightUpperArm", ts, [r_] * 3).mira("RightLowerArm", ts, [r_] * 3)
    # mano: dedos al frente (siguen al antebrazo) y palma hacia adentro (+x: el centro del cuerpo)
    c.orienta("RightHand", ts, [(r_, [1.0, 0.0, 0.0])] * 3, ([-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]))
    if PRONACION_V39:
        c.pronacion("RightHand", PRONACION_V39)   # V39: parte del giro lo hace el antebrazo (la muñeca no se tuerce)
    c.g("Spine", "y", ts, [8, 8, 8]).g("Spine", "x", ts, [2, 3, 2]).g("Head", "y", ts, [-6, -6, -6])
    # el brazo izquierdo descansa como en Idle (sin pista, Godot lo deja en pose T)
    for h in ("LeftShoulder", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightShoulder"):
        c.g(h, "y", ts, [0, 0, 0])
    return [c]


def agarre_pistola(glb, salida):
    import tempfile
    import numpy as np
    from copox.armas import armas_alth
    from copox.movimiento import agarre as ag
    from copox.medicion import rostro_edicion as re
    with tempfile.TemporaryDirectory() as d:
        armas_alth.main(d)
        o = ag.Objeto(os.path.join(d, "PISTOLA_ALTH_PROVISIONAL.glb"))
    m = ag.Mano(glb, "Right")
    A = ag.AgarreCierre(m, o)          # colocación en rejilla + cierre de dedos hasta contacto
    A.resolver()
    acc = A.accion("GATILLO", n=6)
    res = A.resultado()
    res["accion"] = {"nodo": "GATILLO", "cuadros": [{"angulo": a, "rotaciones": A.resultado(ang)["rotaciones"]} for a, ang in acc]}
    E = re.Editor(glb)
    ag.escribir_en_personaje(E, "Pistola", res)
    E.guardar(salida, nota="Adán V37: mano + agarre de pistola. SIN APROBAR.")
    return A.detalle()


DISENO_EXTRA_V38 = {}   # ganchos para V38 (sin efecto en V37)
GROSOR_V38 = 1.0


def main(src, dst):
    v36.EXTRA_EDICIONES = [{"tipo": "escalar", "raiz": f"{l}Hand", "factor": ESCALA_MANO} for l in ("Left", "Right")]
    v36.ESCALA_R = ESCALA_MANO
    v36.DISENO_EXTRA = {"canto_fijo": True, "membrana_pulgar": membrana, **DISENO_EXTRA_V38}
    grosor0 = v36.GROSOR
    v36.GROSOR = grosor0 * GROSOR_V38
    t36 = dst + ".v36.glb"
    try:
        log = v36.main(src, t36)
    finally:
        v36.EXTRA_EDICIONES, v36.ESCALA_R, v36.DISENO_EXTRA = [], 1.0, {}
        v36.GROSOR = grosor0
    from copox.movimiento import locomocion
    t36b = dst + ".v36b.glb"
    locomocion.escribir(t36, t36b, clips_fn=clip_apuntar_pistola)
    os.replace(t36b, t36)
    from copox.medicion.compactar import compactar
    tmp = dst + ".tmp.glb"
    det = agarre_pistola(t36, tmp)
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t36)
    return log + [{"operacion": "agarre pistola", **det}]


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2])[-1])
