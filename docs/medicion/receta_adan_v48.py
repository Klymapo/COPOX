"""Adán V48 (sobre V47): cabeza como una sola pieza lisa de caras planas (frente, lados y espalda).

Pedido de Admin (19 oct 2026): "Queremos que la cara se vea plana de frente. Y de atrás y los lados también. Es una sola
pieza lisa en sus lados." "Los pómulos se ven muy marcados." "Asegúrate de tener una sola pieza lisa sin bultos en la
nuca, veo una masa sobresalir." Cejas: no se tocan (solo viajan con la cara).
Método (copox/medicion/cabeza_caja.py): escalado radial hacia una caja redondeada como la hoja de la cabeza. La piel, el
pelo, los ojos, las cejas, los párpados, la boca y las orejas se mueven juntos. Los gestos se escalan con el mismo factor
y el cuello no se toca.
Caja (medida sobre V47):
- Ancho: 14 cm de semiancho. Antes la cara medía 13.3 y el pelo sobresalía hasta 16.6 a los lados: ahora pelo y cara
  forman un solo bloque, como la hoja. La quijada se angosta 8 % abajo.
- Frente: plano a z 0.148, la frente de V47. Los cachetes, que se curvaban 1.2 cm hacia atrás, salen al plano.
- Atrás: plano a z −0.160 (el pelo llegaba a −0.168). La nuca baja también se lleva al plano.
- Arriba y abajo: del mentón (0.49) a la coronilla (0.84). Aristas redondeadas de 4 cm.
Uso: python receta_adan_v48.py ADAN_V47.glb ADAN_V48.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402

CAJA = dict(centro=(0.0, 0.665, -0.006), semiejes=(0.140, 0.175, 0.154), radio=0.040, angosta_abajo=0.08,
            fuerza=0.9, k_min=0.85, k_max=1.12, y_cuello=(0.49, 0.575))   # transición ancha: sin escalón en la quijada
NUCA = dict(delta=0.020, banda=0.022, ancho_th=95.0, holgura=0.0015)   # el pelo baja hasta el cuello (hoja, vista BACK)


def _normales_soldadas(V, T):
    """Normales por posición (soldando costuras de UV): sin líneas de sombreado en las costuras."""
    _, inv = np.unique(np.round(V, 6), axis=0, return_inverse=True); inv = inv.ravel()
    Tw = inv[T]; n = inv.max() + 1
    Vw = np.zeros((n, 3)); Vw[inv] = V
    Nf = np.cross(Vw[Tw[:, 1]] - Vw[Tw[:, 0]], Vw[Tw[:, 2]] - Vw[Tw[:, 0]])
    N = np.zeros((n, 3))
    for i in range(3):
        np.add.at(N, Tw[:, i], Nf)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N[inv]


def cabeza(E):
    from copox.medicion import cabeza_caja as cc
    from copox.medicion.gltf import accesor
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    S = v39._leer(E, prims["Cabeza_PIEL_EXPUESTA_v04"], "POSITION").astype(float)
    H = v39._leer(E, prims["GUIA_CAPILAR_RELLENO_RUBIO_v04"], "POSITION").astype(float)
    orejas = np.abs(S[:, 0]) > 0.133
    nariz = (np.abs(S[:, 0]) < 0.03) & (S[:, 1] > 0.56) & (S[:, 1] < 0.635) & (S[:, 2] > 0.14)
    C = cc.CajaCabeza(**CAJA).ajustar(np.vstack([S[~orejas & ~nariz], H]))
    movidos, n_prims = 0, 0
    for m in E.j["meshes"]:
        for p in m["primitives"]:
            V = v39._leer(E, p, "POSITION").astype(float)
            if V[:, 1].max() < CAJA["centro"][1] - CAJA["semiejes"][1] + 0.005:
                continue
            V1, J = C.campo(V)
            mov = np.abs(V1 - V).max(1) > 1e-7
            if not mov.any():
                continue
            p["attributes"]["POSITION"] = E._add(V1.astype(np.float32), "VEC3", 34962, True)
            for t in p.get("targets", []):
                D = accesor(E.j, E.b, t["POSITION"]).astype(float)
                if np.abs(D).max() > 0:
                    t["POSITION"] = E._add(np.einsum("nij,nj->ni", J, D).astype(np.float32), "VEC3", None, True)
            if "NORMAL" in p["attributes"]:
                T = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
                N0 = v39._leer(E, p, "NORMAL").astype(float)
                N1 = _normales_soldadas(V1, T)
                if np.einsum("ij,ij->i", N0, N1).mean() < 0:     # misma orientación que el archivo
                    N1 = -N1
                N = N0.copy(); N[mov] = N1[mov]
                p["attributes"]["NORMAL"] = E._add(N.astype(np.float32), "VEC3", 34962)
            movidos += int(mov.sum()); n_prims += 1
    E.b = bytes(E.out)
    k = C.K
    return {"operacion": "cabeza en caja", "primitivas": n_prims, "vertices_movidos": movidos,
            "k_min": round(float(k.min()), 3), "k_max": round(float(k.max()), 3)}


def nuca(E):
    import receta_adan_v45 as v45
    n0 = dict(v45.NUCA)
    v45.NUCA.clear(); v45.NUCA.update(NUCA)
    try:
        return v45.nuca(E)
    finally:
        v45.NUCA.clear(); v45.NUCA.update(n0)


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [cabeza(E), nuca(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V48: cabeza de caras planas, una sola pieza lisa. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
