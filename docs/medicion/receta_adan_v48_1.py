# EXPERIMENTO DESCARTADO (19 oct 2026): dos intentos sin resultado; ver nota abajo. No hay GLB publicado.
"""Adán V48.1 (sobre V47, camino A): pómulos, lados y nuca planos con un campo LOCAL. La cara de V47 queda igual.

V48 (caja completa) no se aprobó (19 oct 2026): la cabeza quedó como ladrillo, alta, y crecieron facciones y pelo.
Camino A, elegido por Admin: partir de V47 y aplanar solo donde se pidió:
- Pómulos y cachetes: la superficie que se curvaba hacia atrás (hasta 1.6 cm detrás del plano de la frente) sale hacia el
  plano del frente.
- Lados bajo el pelo, entre la sien y la quijada: hacia caras planas.
- Nuca: la masa bajo el pelo se aplana contra el plano de atrás.
Se usa la misma caja de V48 solo como objetivo (cabeza_caja.CajaCabeza), con peso por zona (cabeza_caja.mascara_local)
y un tope de 8 % hacia adentro (nunca hacia afuera: inflar hacía cachetes de bolsa). Solo se mueven la piel de la cabeza y las capas del pelo; ojos, cejas, párpados, boca, nariz y
orejas no se tocan (el peso es 0 cerca de ellos). Los gestos se escalan con el mismo factor. Al final, el borde del pelo
de la nuca se vuelve a sellar sobre la piel (pelo_nuca, como V45).
Uso: python receta_adan_v48_1.py ADAN_V47.glb ADAN_V48_1.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v48 as v48  # noqa: E402

PIEZAS = ("Cabeza_PIEL_EXPUESTA_v04", "GUIA_CAPILAR_RELLENO_RUBIO_v04", "GUIA_CAPILAR_CONTORNO_RUBIO_v04")
TOPE = 0.08
NUCA = dict(delta=0.004, banda=0.016, ancho_th=95.0, holgura=0.0015)


def cabeza(E):
    from copox.medicion import cabeza_caja as cc
    from copox.medicion.gltf import accesor
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    S = v39._leer(E, prims["Cabeza_PIEL_EXPUESTA_v04"], "POSITION").astype(float)
    H = v39._leer(E, prims["GUIA_CAPILAR_RELLENO_RUBIO_v04"], "POSITION").astype(float)
    orejas = np.abs(S[:, 0]) > 0.133
    nariz = (np.abs(S[:, 0]) < 0.03) & (S[:, 1] > 0.56) & (S[:, 1] < 0.635) & (S[:, 2] > 0.14)
    caja = {**v48.CAJA, "k_min": 1 - TOPE, "k_max": 1.0,   # solo hacia adentro: nunca infla
            "fuerza": 1.0, "y_cuello": (0.40, 0.41)}
    C = cc.CajaCabeza(**caja).ajustar(np.vstack([S[~orejas & ~nariz], H]))
    log = {"operacion": "cabeza: campo local (pómulos, lados, nuca)"}
    for pz in PIEZAS:
        p = prims[pz]
        V = v39._leer(E, p, "POSITION").astype(float)
        w = cc.mascara_local(V)
        k = 1 + (C.k(V) - 1) * w
        V1 = C.c + (V - C.c) * k[:, None]
        mov = np.abs(V1 - V).max(1) > 1e-7
        p["attributes"]["POSITION"] = E._add(V1.astype(np.float32), "VEC3", 34962, True)
        for t in p.get("targets", []):
            D = accesor(E.j, E.b, t["POSITION"]).astype(float)
            if np.abs(D).max() > 0:
                t["POSITION"] = E._add((D * k[:, None]).astype(np.float32), "VEC3", None, True)
        T = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        N0 = v39._leer(E, p, "NORMAL").astype(float)
        N1 = v48._normales_soldadas(V1, T)
        if np.einsum("ij,ij->i", N0, N1).mean() < 0:
            N1 = -N1
        N = N0.copy(); N[mov] = N1[mov]
        p["attributes"]["NORMAL"] = E._add(N.astype(np.float32), "VEC3", 34962)
        log[pz[:20]] = {"movidos": int(mov.sum()), "max_mm": round(float(np.linalg.norm(V1 - V, axis=1).max()) * 1000, 1)}
    E.b = bytes(E.out)
    return log


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
    E.guardar(tmp, nota="Adán V48.1: pómulos, lados y nuca planos (campo local). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
