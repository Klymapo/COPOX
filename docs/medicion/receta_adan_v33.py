"""Adán V33 (sobre V22 HABLA → V32): cabeza con aristas más afiladas, como la Hoja de vistas.

Pedido de Admin (18 oct 2026): "afilar" las aristas de la cabeza para parecerse más a las referencias.
Medido (SENKU, cortes horizontales de la piel de la cabeza): visto desde arriba, cada corte es casi una elipse
(superelipse n ≈ 2.2–2.6, adelante y atrás): la cara se va redondeando hacia los lados sin un canto. En la hoja la
cabeza es una caja de esquinas redondeadas: frente casi plano y un canto claro entre la cara y el costado.
Arreglo: cada corte horizontal pasa de su superelipse medida (n₁) a una más cuadrada (n₂ = N_FRENTE / N_ATRAS) con
los mismos semiejes: los puntos de frente, costados y nuca no se mueven; solo salen las "esquinas" (diagonales).
El mismo campo (por rayo: r' = r · g(φ)) se aplica a todo lo que va en la cabeza (piel, ojos, párpados, cejas, boca,
orejas, guía capilar), así nada se separa. Se desvanece hacia el cuello. Las normales del archivo se conservan y se
les suma el cambio de las normales geométricas (no se pierde el trabajo de V29–V30 en la boca).
Uso: python receta_adan_v33.py ADAN_V22_HABLA.glb ADAN_V33.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v32 as v32  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402

N_FRENTE, N_ATRAS = 3.4, 3.0
Y_CUELLO = (0.55, 0.60)        # el campo pasa de 0 a 1 en esta franja (la quijada no se toca: hacía cachetes)
PASO = 0.01
PHI_CARA = (24.0, 42.0)        # grados, medidos desde el costado hacia el frente


def _se(phi, a, b, n):
    return (np.abs(np.cos(phi) / a) ** n + np.abs(np.sin(phi) / b) ** n) ** (-1.0 / n)


def cortes(P):
    """Parámetros por corte horizontal de la piel: a (medio ancho), zc, bF, bB, nF, nB."""
    ys = np.arange(0.50, 0.70 + 1e-9, PASO)
    filas = []
    for y in ys:
        q = P[np.abs(P[:, 1] - y) < 0.003]
        a = np.abs(q[:, 0]).max()
        zc = q[np.abs(q[:, 0]) > a - 0.004, 2].mean()
        fila = [y, a, zc]
        for sel in (q[:, 2] >= zc, q[:, 2] < zc):
            h = q[sel]; b = np.abs(h[:, 2] - zc).max()
            phi = np.arctan2(np.abs(h[:, 2] - zc), np.abs(h[:, 0])); r = np.hypot(h[:, 0], h[:, 2] - zc)
            ns = np.arange(1.6, 6.0, 0.1)
            err = [np.median(np.abs(r - _se(phi, a, b, n))[r > 0.8 * _se(phi, a, b, n)]) for n in ns]
            fila += [b, ns[int(np.argmin(err))]]
        filas.append(fila)
    C = np.array(filas)
    # suavizado a lo largo de y (los cortes de arriba casi no tienen nuca de piel: se usa la guía capilar)
    K = np.array([1, 2, 3, 2, 1], float); K /= K.sum()
    for c in range(1, C.shape[1]):
        C[:, c] = np.convolve(np.pad(C[:, c], 2, mode="edge"), K, mode="valid")
    return C


def campo(C, V):
    """Factor g por vértice (en xz, alrededor del eje de la cabeza del corte)."""
    y = np.clip(V[:, 1], C[0, 0], C[-1, 0])
    it = lambda k: np.interp(y, C[:, 0], C[:, k])
    a, zc, bF, nF, bB, nB = it(1), it(2), it(3), it(4), it(5), it(6)
    dz = V[:, 2] - zc
    phi = np.arctan2(np.abs(dz), np.abs(V[:, 0]))
    frente = dz >= 0
    b = np.where(frente, bF, bB); n1 = np.where(frente, nF, nB)
    n2 = np.where(frente, np.maximum(n1, N_FRENTE), np.maximum(n1, N_ATRAS))
    g = _se(phi, a, b, n2) / _se(phi, a, b, n1)
    # la cara (ojos, párpados, cejas, mejillas, boca) no se toca: adelante el campo vive solo en los costados
    # (φ < PHI_CARA[0]) y se apaga antes de llegar a las cuencas de los ojos (φ ≈ 54° en adelante)
    u = np.clip((np.degrees(phi) - PHI_CARA[0]) / (PHI_CARA[1] - PHI_CARA[0]), 0, 1)
    g = np.where(frente, 1 + (g - 1) * (1 - u * u * (3 - 2 * u)), g)
    t = np.clip((V[:, 1] - Y_CUELLO[0]) / (Y_CUELLO[1] - Y_CUELLO[0]), 0, 1)
    w = t * t * (3 - 2 * t)
    g = 1 + w * (g - 1)
    V2 = V.copy()
    V2[:, 0] = V[:, 0] * g
    V2[:, 2] = zc + dz * g
    return V2


def _ngeo(V, F):
    return v32._normales(V, F)


def afilar(E):
    j = E.j
    piel = max(E.prims(v24.PIEL), key=lambda x: j["accessors"][x["attributes"]["POSITION"]]["count"])
    C = cortes(accesor(j, E.b, piel["attributes"]["POSITION"]).astype(float))
    hechos, dmax = 0, 0.0
    vistos = set()
    for nd in j["nodes"]:
        if "mesh" not in nd:
            continue
        for p in j["meshes"][nd["mesh"]]["primitives"]:
            at = p["attributes"]
            if at["POSITION"] in vistos:
                continue
            V = accesor(j, E.b, at["POSITION"]).astype(float)
            # solo piezas de la cabeza (todo por encima del cuello)
            if V[:, 1].min() < 0.44:
                continue
            vistos.add(at["POSITION"])
            V2 = campo(C, V)
            if np.abs(V2 - V).max() < 1e-7:
                continue
            T = [accesor(j, E.b, t["POSITION"]).astype(float) for t in p.get("targets", [])]
            E.escribir(p, V2, [])        # morphs: desplazamientos, se conservan
            if "NORMAL" in at and "indices" in p:
                F = accesor(j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
                N0 = accesor(j, E.b, at["NORMAL"]).astype(float)
                dN = _ngeo(V2, F) - _ngeo(V, F)
                N1 = N0 + dN
                N1 /= np.maximum(np.linalg.norm(N1, axis=1, keepdims=True), 1e-12)
                at["NORMAL"] = E._add(N1, "VEC3", 34962)
            del T
            hechos += 1
            dmax = max(dmax, float(np.abs(V2 - V).max()))
    E.b = bytes(E.out)
    E.log.append({"operacion": "cabeza con aristas más afiladas (cortes horizontales a superelipse más cuadrada)",
                  "piezas": hechos, "desplazamiento_max": round(dmax, 4),
                  "n_medido_frente": [round(float(x), 1) for x in C[:, 4]], "n_medido_atras": [round(float(x), 1) for x in C[:, 6]],
                  "n_meta": [N_FRENTE, N_ATRAS]})


def main(src, dst):
    t32 = dst + ".v32.glb"
    v32.main(src, t32)
    E = re.Editor(t32)
    afilar(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V33: V32 + cabeza con aristas más afiladas (como la Hoja de vistas). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t32)
    return E.log


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2])[-1])
