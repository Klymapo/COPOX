"""Theo V11 (sobre V10) / Adán V18 (--solo-estilo): auditoría artística, sin pelo ni boca.

- Cráneo de lado: la nuca era corta y plana; la mitad de atrás de la cabeza (detrás de la oreja)
  se alarga ×1.15 en profundidad y se redondea (gorro de pelo incluido).
- Entrecejo y nariz: se quita la arista del entrecejo y el bloque viejo (la zona se lleva a una
  superficie suave ajustada) y se pone una nariz nueva: cubo biselado pequeño y rosado, como la Hoja
  (0.26 × 0.24 ED, centrada en v 0.27, sale 0.14 ED).
- Cejas en bloque: las placas planas se cambian por bloques de 10 tramos que siguen la frente, con
  grosor (canto visible en 3/4 y perfil),
  misma silueta que la textura de V05; los gestos de ceja (arriba, ceño, triste) se copian a los
  bloques desde la placa vieja, vértice por vértice.
- Cara baja limpia: el frente de v 0.35–1.0 se acerca a una superficie simétrica de 4.º orden
  (planos limpios tipo caja redondeada), protegiendo la boca.
- Orejas: el panel rosa plano se cambia por una ranura en C más oscura (tres barras delgadas).
Uso: python receta_theo_v11.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, y, S = v5.ED, v5.YC, v5.y, re._suave
PIEL, BOCA = v5.PIEL, v5.BOCA
es_cabeza = v5.es_cabeza
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")
CEJAS = {"L": ("C7V2_brow_BAKE_L", 0.0615, +1), "R": ("C7V2_brow_BAKE_R", -0.0733, -1)}


def cabeza(E):
    return next(E.leer(p)[0] for p in E.prims(PIEL) if es_cabeza(E.leer(p)[0]))


def z_piel(H, x, yy, k=10):
    """z de la piel frontal bajo (x, y): promedio ponderado de los k vecinos más cercanos."""
    Hf = H[H[:, 2] > 0.06]
    q = np.c_[x, yy]
    d2 = ((q[:, None] - Hf[None, :, :2]) ** 2).sum(-1)
    idx = np.argsort(d2, 1)[:, :k]
    w = 1 / (np.take_along_axis(d2, idx, 1) + 1e-10)
    return (Hf[idx, 2] * w).sum(1) / w.sum(1)


# --- cráneo de lado -----------------------------------------------------------------------
def campo_nuca(z0=-0.03, k=1.15):
    def f(V):
        w = S((V[:, 1] - 0.56) / 0.03) * S((z0 - V[:, 2]) / 0.03)
        kk = 1 + (k - 1) * w
        V1 = V.copy(); V1[:, 2] = np.where(V[:, 2] < z0, z0 + (V[:, 2] - z0) * kk, V[:, 2])
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 2, 2] = np.where(V[:, 2] < z0, kk, 1.0)
        return V1, J
    return f


# --- entrecejo y nariz ----------------------------------------------------------------------
def _poli(X, Y):
    return np.c_[np.ones(len(X)), X ** 2, Y, Y ** 2, X ** 2 * Y, Y ** 3, X ** 4]


def campo_entrecejo_nariz(H):
    v = (YC - H[:, 1]) / ED
    u = np.abs(H[:, 0]) / ED
    ajuste = (v > -0.6) & (v < 0.75) & (u > 0.45) & (u < 1.0) & (H[:, 2] > 0.1)
    ajuste |= (v > -0.75) & (v < -0.45) & (u < 0.45) & (H[:, 2] > 0.1)     # frente sobre el entrecejo
    c, *_ = np.linalg.lstsq(_poli(H[ajuste, 0], H[ajuste, 1]), H[ajuste, 2], rcond=None)

    def f(V):
        vv = (YC - V[:, 1]) / ED
        uu = np.abs(V[:, 0]) / ED
        w = S((0.42 - uu) / 0.12) * S((vv + 0.45) / 0.12) * S((0.52 - vv) / 0.08) * S((V[:, 2] - 0.1) / 0.02)
        z = _poli(V[:, 0], V[:, 1]) @ c
        V1 = V.copy(); V1[:, 2] = V[:, 2] + (z - V[:, 2]) * w
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


def nariz_nueva(E, H):
    yc = y(0.27)
    zs = float(z_piel(H, np.array([0.0]), np.array([yc]))[0])
    sale = 0.14 * ED
    hz = (sale + 0.012) / 2
    zc = zs + sale - hz
    re.agregar_caja(E, "ADAN_CUERPO", PIEL, (0.0, yc, zc), (0.13 * ED, 0.12 * ED, hz), "Head", bisel=0.22)
    p = E.j["meshes"][next(n for n in E.j["nodes"] if n.get("name") == "ADAN_CUERPO")["mesh"]]["primitives"][-1]
    n = E.j["accessors"][p["attributes"]["POSITION"]]["count"]
    p["attributes"]["COLOR_0"] = E._add(np.tile([1.0, 0.86, 0.84, 1.0], (n, 1)), "VEC4", 34962)
    E.b = bytes(E.out)
    E.log.append({"operacion": "nariz nueva: cubo biselado 0.26×0.24 ED, sale 0.14 ED, rosada (COLOR_0)", "material": PIEL})


# --- cejas en bloque ------------------------------------------------------------------------
def _prisma(frente, atras):
    """Prisma de caras planas a partir de dos polígonos (mismo orden de vértices)."""
    n = len(frente)
    V, F = [], []

    def cara(pts):
        i = len(V); V.extend(pts)
        for k in range(1, len(pts) - 1):
            F.append([i, i + k, i + k + 1])
    cara(list(frente)); cara(list(atras[::-1]))
    for k in range(n):
        a, b = k, (k + 1) % n
        cara([frente[a], atras[a], atras[b], frente[b]])
    V = np.array(V); F = np.array(F)
    c = V.mean(0)
    T = V[F]; nr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    flip = (nr * (T.mean(1) - c)).sum(1) < 0
    F[flip] = F[flip][:, ::-1]
    # normales planas: un vértice por esquina de cada cara
    V2 = V[F].reshape(-1, 3); F2 = np.arange(len(V2)).reshape(-1, 3)
    return V2, F2


def _ceja_tira(H, cx, sale, grosor, hundida, n=10):
    """Bloque de ceja en n tramos que siguen la curva de la frente. Silueta de V05 (ED desde el centro
    del ojo, Xo hacia afuera): de −0.25 a +0.35; arriba −0.47→−0.50, abajo −0.30→−0.35 (externo recortado)."""
    t = np.linspace(0, 1, n + 1)
    Xo = -0.25 + 0.60 * t
    arriba = -0.47 - 0.03 * t
    abajo = -0.30 - 0.05 * t
    abajo = np.where(Xo > 0.27, abajo - (Xo - 0.27) / 0.08 * 0.07, abajo)   # chaflán externo inferior
    x = cx + sale * Xo * ED
    yt, yb = y(arriba), y(abajo)
    zt, zb = z_piel(H, x, yt), z_piel(H, x, yb)
    FT = np.c_[x, yt, zt + grosor]; FB = np.c_[x, yb, zb + grosor]
    BT = np.c_[x, yt, zt - hundida]; BB = np.c_[x, yb, zb - hundida]
    quads = []
    for i in range(n):
        j = i + 1
        quads += [(FT[i], FB[i], FB[j], FT[j]), (BT[i], BT[j], BB[j], BB[i]),
                  (FT[i], FT[j], BT[j], BT[i]), (FB[i], BB[i], BB[j], FB[j])]
    quads += [(FT[0], BT[0], BB[0], FB[0]), (FT[n], FB[n], BB[n], BT[n])]
    c = np.r_[FT, FB, BT, BB].mean(0)
    V, F = [], []
    for q in quads:
        q = np.array(q); i = len(V); V.extend(q)
        tri = [[i, i + 1, i + 2], [i, i + 2, i + 3]]
        nr = np.cross(q[1] - q[0], q[2] - q[0])
        if (nr * (q.mean(0) - c)).sum() < 0 and q is not None:
            tri = [r[::-1] for r in tri]
        F.extend(tri)
    V = np.array(V); F = np.array(F)
    V2 = V[F].reshape(-1, 3); F2 = np.arange(len(V2)).reshape(-1, 3)
    return V2, F2


def cejas_en_bloque(E, H, grosor=0.05 * ED, hundida=0.04 * ED, color=(0.345, 0.22, 0.125)):
    mat_i = len(E.j["materials"])
    E.j["materials"].append({"name": "CEJA_BLOQUE", "pbrMetallicRoughness": {"baseColorFactor": [*([c ** 2.2 for c in color]), 1.0],
                                                                             "metallicFactor": 0.0, "roughnessFactor": 0.9}})
    for lado, (mat, cx, sale) in CEJAS.items():
        V, F = _ceja_tira(H, cx, sale, grosor, hundida)
        re.agregar_malla(E, "ADAN_CUERPO", "PIEL_REFERENCIAS_THEO_ALASTOR_v04", V, F, "Head", f"ceja {lado} en bloque")
        p = E.j["meshes"][next(n for n in E.j["nodes"] if n.get("name") == "ADAN_CUERPO")["mesh"]]["primitives"][-1]
        p["material"] = mat_i
        # normales planas (agregar_malla las suaviza; aquí cada vértice es de una sola cara)
        T = V[F]; Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); Nf /= np.linalg.norm(Nf, axis=1, keepdims=True)
        p["attributes"]["NORMAL"] = E._add(np.repeat(Nf, 3, axis=0), "VEC3", 34962)
        # gestos: delta del vértice más cercano de la placa vieja
        placa = next(E.prims(mat))
        Pv, Tv = E.leer(placa)
        idx = np.argmin(((V[:, None, :2] - Pv[None, :, :2]) ** 2).sum(-1), 1)
        for t, D in zip(p["targets"], Tv):
            if np.abs(D).max() > 0:
                t_new = D[idx]
                t["POSITION"] = E._add(t_new, "VEC3", None, True)
        E.b = bytes(E.out)
        # la placa vieja queda escondida dentro de la cabeza
        E.deformar(mat, lambda Q: (Q.mean(0) + np.array([0, 0, -0.04]) + (Q - Q.mean(0)) * 0.01, np.tile(np.eye(3) * 0.01, (len(Q), 1, 1))),
                   f"placa {mat} escondida (la reemplaza el bloque)")
    E.log.append({"operacion": "cejas en bloque: prismas con grosor 0.045 ED, gestos copiados de la placa", "material": "CEJA_BLOQUE"})


# --- cara baja limpia -------------------------------------------------------------------------
def campo_cara_baja(H):
    v = (YC - H[:, 1]) / ED
    u = np.abs(H[:, 0]) / ED
    boca = (np.abs(v - 0.59) < 0.1) & (u < 0.5)
    ajuste = (v > 0.3) & (v < 1.0) & (u < 1.1) & (H[:, 2] > 0.06) & ~boca
    A = lambda X, Y: np.c_[np.ones(len(X)), X ** 2, Y, Y ** 2, X ** 2 * Y, Y ** 3, X ** 4, X ** 2 * Y ** 2, Y ** 4]  # noqa: E731
    c, *_ = np.linalg.lstsq(A(H[ajuste, 0], H[ajuste, 1]), H[ajuste, 2], rcond=None)

    def f(V):
        vv = (YC - V[:, 1]) / ED
        uu = np.abs(V[:, 0]) / ED
        w = S((vv - 0.32) / 0.1) * S((1.0 - vv) / 0.08) * S((1.1 - uu) / 0.15) * S((V[:, 2] - 0.06) / 0.03)
        w *= 1 - S(1 - np.sqrt((uu / 0.55) ** 2 + ((vv - 0.59) / 0.13) ** 2))     # la boca queda igual
        z = A(V[:, 0], V[:, 1]) @ c
        V1 = V.copy(); V1[:, 2] = V[:, 2] + (z - V[:, 2]) * 0.7 * w
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


# --- orejas -------------------------------------------------------------------------------------
def orejas_ranura(E):
    es_panel = lambda V: len(V) == 84 and np.abs(V[:, 0]).min() > 0.15 and (np.abs(V[:, 0]).max() - np.abs(V[:, 0]).min()) < 0.004  # noqa: E731
    E.deformar(PIEL, lambda Q: (Q.mean(0) * np.array([0.9, 1, 1]) + (Q - Q.mean(0)) * 0.01, np.tile(np.eye(3) * 0.01, (len(Q), 1, 1))),
               "panel rosa de las orejas escondido", primitiva=es_panel)
    for lado in (-1, 1):
        xe = lado * (0.1952 + 0.0005)
        yc, zc, hy, hz, t = 0.6108, -0.030, 0.021, 0.014, 0.0028
        barras = [((xe, yc, zc + hz - t / 2), (0.0006, hy, t / 2)),            # frente (C abierta hacia atrás)
                  ((xe, yc + hy - t / 2, zc), (0.0006, t / 2, hz)),            # arriba
                  ((xe, yc - hy + t / 2, zc), (0.0006, t / 2, hz))]            # abajo
        for centro, semi in barras:
            re.agregar_caja(E, "ADAN_CUERPO", PIEL, centro, semi, "Head", bisel=0.05)
            p = E.j["meshes"][next(n for n in E.j["nodes"] if n.get("name") == "ADAN_CUERPO")["mesh"]]["primitives"][-1]
            n = E.j["accessors"][p["attributes"]["POSITION"]]["count"]
            p["attributes"]["COLOR_0"] = E._add(np.tile([0.80, 0.62, 0.57, 1.0], (n, 1)), "VEC4", 34962)
            E.b = bytes(E.out)
    E.log.append({"operacion": "orejas: ranura en C más oscura (en vez del panel rosa)", "material": PIEL})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    cn = campo_nuca()
    E.deformar(PIEL, cn, "nuca: mitad de atrás ×1.15 en profundidad", primitiva=es_cabeza)
    for mat in PELO:
        E.deformar(mat, cn, f"nuca: {mat} sigue la forma")
    H = cabeza(E)
    E.deformar(PIEL, campo_entrecejo_nariz(H), "entrecejo plano y nariz vieja fundida en la cara", primitiva=es_cabeza)
    H = cabeza(E)
    nariz_nueva(E, H)
    cejas_en_bloque(E, H)
    E.deformar(PIEL, campo_cara_baja(cabeza(E)), "cara baja limpia (superficie simétrica 4.º orden, boca protegida)", primitiva=es_cabeza)
    orejas_ranura(E)
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    for mat in PELO:
        E.recalcular_normales(mat, None, f"normales recalculadas: {mat}")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V11" if identidad else "Adán V18") + ": auditoría artística (nuca, nariz, cejas, cara baja, orejas). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print({k: v for k, v in x.items() if k != "material"})
