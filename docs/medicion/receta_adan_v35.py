"""Adán V35 (sobre V22 HABLA → V34): manos, tercera ronda — pulgar.

Skills de Argos aplicadas (rama propuesta/g2c-advancing-front-skills): rig-architect (bind pose e
inverseBindMatrices coherentes, clips preservados), motion-lab (poses de mano por clip), gltf-rig-guardian
(conteo de huesos, clips y morphs antes/después) y visual-critic (cada referencia por separado).
SENKU (copox/medicion/mano.py) contra la mano con regla: el pulgar sale a 73° de los dedos (ref 43°) y en Idle,
PointFwd y Aim se ve como palo que sobresale (revisión visual independiente de V34).
Arreglo: el pulgar (metacarpo y su cadena, con sus vértices) gira PULGAR_GIRO° en el plano de la palma hacia los
dedos, alrededor de la cabeza del metacarpo. Las claves de rotación del pulgar en TODOS los clips se conjugan
(q' = R q R⁻¹): cada pose queda igual que antes pero girada como el reposo, así el pulgar se cierra sobre los dedos
en puños y queda pegado en Idle. Pesos por cadena rehechos.
Uso: python receta_adan_v35.py ADAN_V22_HABLA.glb ADAN_V35.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import proporciones  # noqa: E402
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
import receta_adan_v34 as v34  # noqa: E402
import receta_adan_v27 as v27  # noqa: E402

PULGAR_GIRO = 30.0
# Puño de la hoja de vistas: dedos cerrados de verdad. En los clips el "puño" llegaba a 35/47/30° (M31_3_Puno) o
# 48/55/38° (Idle): los dedos quedaban como peine. Los dedos (no el pulgar) que ya estaban cerrados se llevan a un
# puño completo; los gestos de mano abierta (curva < CURVA_ABIERTA) no se tocan.
PUNO = {"Proximal": 85.0, "Intermediate": 100.0, "Distal": 70.0}
CURVA_ABIERTA, CURVA_PUNO = 15.0, 35.0


def _qz(grados):
    h = np.radians(grados) / 2
    return np.array([0.0, 0.0, np.sin(h), np.cos(h)])


def _qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def cerrar_punos(E):
    """Por clip y cuadro: la curva del proximal de cada dedo decide cuánto puño hay (0 abierto … 1 puño); las tres
    falanges se llevan juntas a PUNO con esa fracción. Solo cambia el giro alrededor del eje de flexión (z)."""
    j = E.j
    nombres = {i: n.get("name", "") for i, n in enumerate(j["nodes"])}
    dedos = ("Index", "Middle", "Ring", "Little")
    hechos = 0
    for a in j.get("animations", []):
        canales = {}
        for ch in a["channels"]:
            nm = nombres[ch["target"]["node"]]
            if ch["target"]["path"] == "rotation" and any(d in nm for d in dedos):
                canales[nm] = ch
        for lado, sg in (("Left", -1.0), ("Right", 1.0)):     # flexión: −z en la izquierda, +z en la derecha
            for d in dedos:
                prox = canales.get(lado + d + "Proximal")
                if prox is None:
                    continue
                Qp = accesor(j, E.b, a["samplers"][prox["sampler"]]["output"]).astype(float).reshape(-1, 4)
                curva = np.degrees(2 * np.arctan2(sg * Qp[:, 2], Qp[:, 3]))
                u = np.clip((curva - CURVA_ABIERTA) / (CURVA_PUNO - CURVA_ABIERTA), 0, 1)
                f = u * u * (3 - 2 * u)
                if f.max() < 1e-6:
                    continue
                for fal, meta in PUNO.items():
                    ch = canales.get(lado + d + fal)
                    if ch is None:
                        continue
                    sm = a["samplers"][ch["sampler"]]
                    Q = accesor(j, E.b, sm["output"]).astype(float).reshape(-1, 4)
                    if len(Q) != len(f):
                        continue
                    out = []
                    for q, fk in zip(Q, f):
                        th = np.degrees(2 * np.arctan2(sg * q[2], q[3]))
                        nuevo = (1 - fk) * th + fk * meta
                        resto = _qmul(_qz(-sg * th), q)          # lo que no es flexión se conserva
                        out.append(_qmul(_qz(sg * nuevo), resto))
                    sm["output"] = E._add(np.asarray(out, np.float32), "VEC4")
                    hechos += 1
    E.b = bytes(E.out)
    E.log.append({"operacion": "puños cerrados (dedos que ya cerraban → puño completo)", "canales": hechos})
    return hechos


def giros():
    # palma abajo en pose T: el plano de la palma es xz; girar alrededor de y lleva el pulgar (+z) hacia los dedos
    return [{"tipo": "rotar", "raiz": "LeftThumbMetacarpal", "eje": [0, 1, 0], "grados": PULGAR_GIRO},
            {"tipo": "rotar", "raiz": "RightThumbMetacarpal", "eje": [0, 1, 0], "grados": -PULGAR_GIRO}]


def main(src, dst):
    t34 = dst + ".v34.glb"
    v34.main(src, t34)
    a, b, c = dst + ".a.glb", dst + ".b.glb", dst + ".c.glb"
    r = proporciones.editar(t34, a, giros(), nota="Adán V35: pulgar girado en reposo. SIN APROBAR.")
    r["claves_conjugadas"] = proporciones.conjugar_claves(a, b, giros())
    E = re.Editor(b)
    r["repesado"] = v27.repesar(E)
    r["puños"] = cerrar_punos(E)
    E.guardar(c, nota="Adán V35: V34 + pulgar 30° hacia los dedos (reposo y clips) y puños cerrados. SIN APROBAR.")
    compactar(c, dst)
    for f in (a, b, c, t34):
        os.remove(f)
    return r


if __name__ == "__main__":
    r = main(sys.argv[1], sys.argv[2]); r.pop("huesos_movidos", None); r.pop("repesado", None); print(r)
