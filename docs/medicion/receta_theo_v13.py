"""Theo V13 (sobre V12) / Adán V20 (--solo-estilo): cabeza lisa en todos sus puntos.

En vez de seguir suavizando la malla vieja, la piel de la cabeza se reemplaza por una superficie
matemáticamente lisa ajustada a su forma actual:
- desde un centro dentro de la cabeza, el radio de cada vértice se ajusta con un polinomio en la
  dirección (grado 12, 455 términos, equivalente a armónicos esféricos de grado 12); la superficie
  ajustada no tiene bultos ni hundidos de alta frecuencia;
- cada vértice se mueve a la superficie ajustada sobre su rayo; se conserva el detalle solo en la boca
  (abertura, labios, comisuras), en las caras interiores y junto a los bordes abiertos;
- un Taubin ligero final une las zonas conservadas con la superficie lisa (se probó una relajación
  tangencial con reproyección: movía hasta 9 mm y empeoraba las uniones; descartada);
- luego el gorro de pelo se ajusta igual (su propia superficie) y las piezas pegadas a la cara (placas
  de ojo, párpados, cejas, nariz, orejas) se reacomodan a la piel nueva.
Uso: python receta_theo_v13.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys
from itertools import combinations_with_replacement

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, S = v5.ED, v5.YC, re._suave
PIEL = v5.PIEL
es_cabeza = v5.es_cabeza
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")
CENTRO = np.array([0.0, 0.64, 0.0])


def base(u, grado):
    cols = [np.ones(len(u))]
    for k in range(1, grado + 1):
        for comb in combinations_with_replacement(range(3), k):
            cols.append(np.prod(u[:, comb], axis=1))
    return np.stack(cols, 1)


def ajuste_radial(V, w_ajuste, grado=12, lam=1e-6, devolver_coef=False):
    d = V - CENTRO
    r = np.linalg.norm(d, axis=1)
    u = d / r[:, None]
    A = base(u, grado)
    Aw = A * w_ajuste[:, None]
    coef = np.linalg.solve(Aw.T @ A + lam * np.eye(A.shape[1]), Aw.T @ r)
    if devolver_coef:
        return u, r, A @ coef, coef
    return u, r, A @ coef


def relajar(V1, Fw, w, libre, coef, grado, conservar, iteraciones=25):
    """Relajación tangencial (triángulos parejos) + reproyección a la superficie lisa en las zonas libres;
    al final un Taubin suave en todo lo no protegido. Trabaja sobre la malla soldada."""
    nw = w.max() + 1
    P = np.zeros((nw, 3)); np.add.at(P, w, V1); P /= np.bincount(w, minlength=nw)[:, None]
    lib = np.zeros(nw); np.maximum.at(lib, w, libre)
    con = np.zeros(nw); np.maximum.at(con, w, conservar)
    E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]); E2 = np.unique(np.concatenate([E2, E2[:, ::-1]]), axis=0)
    cnt = np.bincount(E2[:, 0], minlength=nw)

    def lap(Q):
        s = np.zeros_like(Q); np.add.at(s, E2[:, 0], Q[E2[:, 1]])
        return s / np.maximum(cnt, 1)[:, None] - Q

    def normales(Q):
        T = Q[Fw]; Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); N = np.zeros_like(Q)
        for i in range(3):
            np.add.at(N, Fw[:, i], Nf)
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    for _ in range(iteraciones):
        L = lap(P); N = normales(P)
        Lt = L - (L * N).sum(1)[:, None] * N
        P += 0.5 * Lt * lib[:, None]
        d = P - CENTRO; u = d / np.linalg.norm(d, axis=1, keepdims=True)
        rf = base(u, grado) @ coef
        r = np.linalg.norm(d, axis=1)
        P = np.where((con < 0.5)[:, None], CENTRO + u * rf[:, None], P)
    for _ in range(8):
        for f in (0.5, -0.53):
            P += f * lap(P) * (lib * (1 - S(np.clip(con * 2 - 1, 0, 1))))[:, None]
    return P[w]


def _soldar_info(E, p, V):
    F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True); w = w.ravel()
    nw = w.max() + 1; Fw = w[F]
    k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
    uu, c = np.unique(k, axis=0, return_counts=True)
    borde_w = np.zeros(nw, bool); borde_w[uu[c == 1].ravel()] = True
    E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]); E2 = np.concatenate([E2, E2[:, ::-1]])
    # distancia (en anillos) al borde, hasta 4
    dist = np.where(borde_w, 0, 99)
    for i in range(1, 5):
        cerca = np.zeros(nw, bool); cerca[E2[dist[E2[:, 0]] == i - 1, 1]] = True
        dist = np.where(cerca & (dist > i), i, dist)
    return w, Fw, dist[w]


def dist_borde_w(dist_borde, w, nw):
    d = np.full(nw, 99); np.minimum.at(d, w, dist_borde)
    return d


def cabeza_lisa(E, grado=12):
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        N = accesor(E.j, E.b, p["attributes"]["NORMAL"]).astype(float)
        w, Fw, dist_borde = _soldar_info(E, p, V)
        v = (YC - V[:, 1]) / ED
        u_ = V[:, 0] / ED
        d = V - CENTRO
        afuera = (N * d).sum(1) / np.linalg.norm(d, axis=1) > 0.2
        boca = S(1 - np.sqrt((u_ / 0.6) ** 2 + ((v - 0.59) / 0.13) ** 2)) * (V[:, 2] > 0.08)
        borde = S((4 - dist_borde) / 4.0)
        conservar = np.clip(np.maximum(np.maximum(boca, borde), (~afuera).astype(float)), 0, 1)
        u, r, rf, coef = ajuste_radial(V, (afuera & (boca < 0.05)).astype(float), grado, devolver_coef=True)
        r_nuevo = rf + (r - rf) * conservar
        V1 = CENTRO + u * r_nuevo[:, None]
        # unión suave: Taubin ligero en todo lo no protegido
        nw = w.max() + 1
        P = np.zeros((nw, 3)); np.add.at(P, w, V1); P /= np.bincount(w, minlength=nw)[:, None]
        lib = np.zeros(nw); np.maximum.at(lib, w, 1 - conservar)
        E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]); E2 = np.unique(np.concatenate([E2, E2[:, ::-1]]), axis=0)
        cnt = np.bincount(E2[:, 0], minlength=nw)
        for _ in range(6):
            for f in (0.5, -0.53):
                sm = np.zeros_like(P); np.add.at(sm, E2[:, 0], P[E2[:, 1]])
                P += f * (sm / np.maximum(cnt, 1)[:, None] - P) * np.clip(lib + 0.3, 0, 1)[:, None] * (dist_borde_w(dist_borde, w, nw) > 0)[:, None]
        V1 = P[w]
        mov = np.linalg.norm(V1 - V, axis=1)
        E.escribir(p, V1, T)
        E.log.append({"operacion": f"piel de la cabeza → superficie lisa (ajuste radial grado {grado})", "material": PIEL,
                      "movimiento_mm": {"mediana": round(float(np.median(mov) * 1000), 2), "p95": round(float(np.percentile(mov, 95) * 1000), 2),
                                        "max": round(float(mov.max() * 1000), 2)}})
        return V, V1


def gorro_liso(E, grado=10):
    for mat in PELO:
        for p in E.prims(mat):
            V, T = E.leer(p)
            N = accesor(E.j, E.b, p["attributes"]["NORMAL"]).astype(float)
            w, Fw, dist_borde = _soldar_info(E, p, V)
            d = V - CENTRO
            afuera = (N * d).sum(1) / np.linalg.norm(d, axis=1) > 0.2
            borde = S((4 - dist_borde) / 3.0)
            conservar = np.clip(np.maximum(borde, (~afuera).astype(float)), 0, 1)
            u, r, rf = ajuste_radial(V, afuera.astype(float), grado)
            V1 = CENTRO + u * (rf + (r - rf) * conservar)[:, None]
            E.escribir(p, V1, T)
            E.log.append({"operacion": f"{mat} → superficie lisa (grado {grado})", "material": mat,
                          "movimiento_max_mm": round(float(np.abs(np.linalg.norm(V1 - CENTRO, axis=1) - r).max() * 1000), 2)})


def reacomodar(E, V0, V1):
    """Las piezas pegadas a la cara siguen el desplazamiento de la piel más cercana (promedio local)."""
    D = V1 - V0
    sel = np.linalg.norm(D, axis=1) > 0

    def campo(Q):
        out = np.zeros_like(Q)
        for i in range(0, len(Q), 1500):
            B = Q[i:i + 1500]
            d2 = ((B[:, None] - V0[None]) ** 2).sum(-1)
            idx = np.argsort(d2, 1)[:, :12]
            wt = 1 / (np.take_along_axis(d2, idx, 1) + 1e-10)
            out[i:i + 1500] = (D[idx] * wt[..., None]).sum(1) / wt.sum(1)[:, None]
        return Q + out, np.tile(np.eye(3), (len(Q), 1, 1))
    mats = ("C7V2_eye_BAKE_L", "C7V2_eye_BAKE_R", "CEJA_BLOQUE", "LINEA_PARPADO_CAFE")
    for m in mats:
        if any(mm["name"] == m for mm in E.j["materials"]):
            E.deformar(m, campo, f"{m}: sigue a la piel lisa")
    # piezas de piel aparte: párpados, nariz, orejas y sus detalles
    E.deformar(PIEL, campo, "párpados, nariz y orejas: siguen a la piel lisa",
               primitiva=lambda Q: (not es_cabeza(Q)) and Q[:, 1].min() > 0.5)


def main(src, dst, identidad=True):
    E = re.Editor(src)
    V0, V1 = cabeza_lisa(E)
    reacomodar(E, V0, V1)
    gorro_liso(E)
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    for mat in PELO:
        E.recalcular_normales(mat, None, f"normales recalculadas: {mat}")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V13" if identidad else "Adán V20") + ": cabeza lisa (superficie ajustada). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print({k: v for k, v in x.items() if k != "material"})
