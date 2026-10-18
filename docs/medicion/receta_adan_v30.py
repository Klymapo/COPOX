"""Adán V30 (sobre V22 HABLA → V28): boca plana sin escalón en la quijada.

Hallazgo (CHXP luz=juego + perfiles SENKU, 18 oct 2026): en V29 el relleno bi-armónico dejaba la zona de la boca
casi vertical (normal Ny ≈ 0) hasta 1 cm debajo de la rendija y luego doblaba de golpe hacia la quijada
(Ny −0.5): con el sol del juego eso se ve como una "U" oscura bajo la boca. A los lados de la boca (x = 0.055)
la piel natural baja suave (Ny de 0 a −0.9). El relleno aplanaba también la curva de la quijada.
Arreglo: se rellena el residuo z − G(y), donde G es el perfil vertical natural de la cara medido en columnas de
piel a los lados de la boca (|x| 0.062–0.09). Lo plano queda plano y la quijada conserva su curva, sin quiebre.
Gestos (morphs) intactos. Uso: python receta_adan_v30.py ADAN_V22_HABLA.glb ADAN_V30.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402
import receta_adan_v25 as v25  # noqa: E402
import receta_adan_v28 as v28  # noqa: E402
import receta_adan_v29 as v29  # noqa: E402
from receta_adan_v29 import PIEL, S, OV_X, OV_Y_ARR, OV_Y_ABA, ORILLA, METIDA, base, copa_detras  # noqa: E402,F401

COL_X = (0.058, 0.095)       # columnas de piel natural a los lados de la boca
Y_TOPE = 0.565


def perfil_quijada(P, frente):
    """g(x, y): forma natural de la quijada, ajustada (mínimos cuadrados, polinomio suave) en la piel a los lados de la
    boca (|x| 0.058–0.095, y 0.488–0.575). Arriba de y = 0.565 se congela (la cara ahí ya es casi vertical), para no
    imprimir ondas horizontales en los cachetes."""
    m = frente & (np.abs(P[:, 0]) > COL_X[0]) & (np.abs(P[:, 0]) < COL_X[1]) & (P[:, 1] > 0.488) & (P[:, 1] < 0.575)
    def B(x, y):
        y = np.minimum(y, Y_TOPE) - 0.53
        return np.stack([np.ones_like(y), y, y ** 2, y ** 3, y ** 4, x ** 2, x ** 2 * y, x ** 2 * y ** 2], 1)
    c, *_ = np.linalg.lstsq(B(P[m, 0], P[m, 1]), P[m, 2], rcond=None)
    err = P[m, 2] - B(P[m, 0], P[m, 1]) @ c
    return (lambda x, y: B(x, y) @ c), float(np.abs(err).max()), int(m.sum())


def aplanar(E):
    """Como V29, pero lo que se rellena es el RESIDUO z − G(y): la forma natural de la quijada (G, sacada de las
    columnas de piel a los lados de la boca) se conserva y solo se alisa lo que sobra."""
    from scipy.spatial import cKDTree
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V, T = E.leer(q)
    F = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
    w = v25._soldar(V); n = w.max() + 1
    P = np.zeros((n, 3)); np.add.at(P, w, V); P /= np.bincount(w, minlength=n)[:, None]
    yr = v24.y_rendija(P[:, 0])
    dy = P[:, 1] - yr
    frente = P[:, 2] > 0.09
    # óvalo normalizado (1 = borde del óvalo plano)
    ry = np.where(dy >= 0, OV_Y_ARR, OV_Y_ABA)
    r = np.sqrt((P[:, 0] / OV_X) ** 2 + (dy / ry) ** 2)
    # anillo de ajuste: fuera del óvalo (r de 1.35 a 2.6), y sin la nariz (|x| < 0.025 y y > 0.56 queda fuera)
    nariz = (np.abs(P[:, 0]) < 0.026) & (P[:, 1] > 0.558)
    anillo = frente & (r > 1.35) & (r < 2.6) & ~nariz
    G, err_g, n_g = perfil_quijada(P, frente)
    cz, *_ = np.linalg.lstsq(base(P[anillo, 0], P[anillo, 1]), P[anillo, 2], rcond=None)
    z_lisa = base(P[:, 0], P[:, 1]) @ cz
    # pared de adentro de la boca: lo que está muy detrás de la superficie no se toca
    cerca_rendija = (np.abs(P[:, 0]) < v24.XW * 1.25) & (np.abs(dy) < 0.010)
    # pared de adentro de los labios (lo que se mete a la boca): se separa de la superficie y no participa
    pared = cerca_rendija & (P[:, 2] < z_lisa - 0.0035)
    # en las comisuras la pared se rellena poco a poco (rampa), para que la línea termine limpia, sin muesca
    # ni un escalón de pared que Godot pinte oscuro (la piel es de dos caras)
    pared &= np.abs(P[:, 0]) < v24.XW * 0.92
    # Relleno bi-armónico (membrana tensa sin dobleces): dentro del óvalo la altura z resuelve Δ²z = 0 con la piel
    # de afuera como borde fijo. Queda lisa y se une sin escalón con la barbilla y la base de la nariz
    # (el ajuste global dejaba un aro en la orilla del óvalo). La pared de adentro de la boca queda fija.
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    Fw0 = w[F]
    Ed0 = np.unique(np.sort(np.concatenate([Fw0[:, [0, 1]], Fw0[:, [1, 2]], Fw0[:, [2, 0]]]), 1), axis=0)
    Edall = Ed0.copy()
    Ed0 = Ed0[~pared[Ed0[:, 0]] & ~pared[Ed0[:, 1]]]     # la pared no jala la superficie (antes hacía hoyuelos en las comisuras)
    A = sp.coo_matrix((np.ones(2 * len(Ed0)), (np.r_[Ed0[:, 0], Ed0[:, 1]], np.r_[Ed0[:, 1], Ed0[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1
    deg = np.asarray(A.sum(1)).ravel()
    L = sp.diags(deg) - A
    libre = frente & (r < 1.0 + ORILLA) & ~pared
    fijo = ~libre
    L2 = (L @ sp.diags(1 / np.maximum(deg, 1)) @ L).tocsr()
    il, ifx = np.where(libre)[0], np.where(fijo)[0]
    g = G(P[:, 0], P[:, 1])
    res = P[:, 2] - g
    M_ = L2[il][:, il]; rhs = -L2[il][:, ifx] @ res[ifx]
    z_new = P[:, 2].copy()
    z_new[il] = g[il] + spl.spsolve(M_.tocsc(), rhs)
    linea = METIDA * np.exp(-(dy / 0.0030) ** 2) * S((v24.XW * 1.05 - np.abs(P[:, 0])) / 0.008)   # se desvanece en las comisuras
    P0 = P.copy()
    P[:, 2] = np.where(libre, z_new - linea, P[:, 2])
    # pulido: la malla de la cara es irregular (triángulos de tamaños muy distintos) y el relleno deja ondas
    # chicas; Taubin solo en z sobre la superficie (sin la pared), con peso que se apaga en la orilla
    wpul = np.clip((1 + ORILLA - r) / ORILLA, 0, 1) * libre
    for _ in range(40):
        for f_ in (0.5, -0.53):
            rr = P[:, 2] - g
            zm = np.asarray(A @ rr).ravel() / np.maximum(deg, 1)
            P[:, 2] += f_ * wpul * (zm - rr) * (deg > 0)
    rampa = S((np.abs(P[:, 0]) / v24.XW - 0.55) / 0.37) * pared
    P[:, 2] = P[:, 2] + rampa * np.clip(z_lisa - 0.0015 - P[:, 2], 0, None)
    # grafo completo (con la pared) para pulir las puntas de la rendija
    Afull = sp.coo_matrix((np.ones(2 * len(Edall)), (np.r_[Edall[:, 0], Edall[:, 1]], np.r_[Edall[:, 1], Edall[:, 0]])), shape=(n, n)).tocsr(); Afull.data[:] = 1
    degf = np.asarray(Afull.sum(1)).ravel()
    # comisuras: el abanico de vértices en la punta de la rendija hacía un piquito; se alisa solo en z
    for sx in (1, -1):
        cx, cy_ = sx * v24.XW, v24.y_rendija(np.array([v24.XW]))[0]
        dd = np.hypot(P[:, 0] - cx, P[:, 1] - cy_)
        wc = S((0.014 - dd) / 0.008) * frente
        for _ in range(60):
            rr = P[:, 2] - g
            zm = np.asarray(Afull @ rr).ravel() / np.maximum(degf, 1)
            P[:, 2] += 0.5 * wc * (zm - rr)
    V1 = P[w]
    E.escribir(q, V1, T)
    mov = np.abs(P - P0).max(1) > 1e-7
    # normales soldadas en la zona + 2 anillos de vecinos
    Fw = w[F]
    Ed = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
    e = np.unique(Ed, axis=0); E2 = np.concatenate([e, e[:, ::-1]])
    Tn = P[Fw]; Nf = np.cross(Tn[:, 1] - Tn[:, 0], Tn[:, 2] - Tn[:, 0])
    N = np.zeros((n, 3))
    for k in range(3):
        np.add.at(N, Fw[:, k], Nf)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    zona = mov.copy()
    for _ in range(2):
        z2 = zona.copy(); z2[E2[zona[E2[:, 0]], 1]] = True; zona = z2
    viejo = accesor(E.j, E.b, q["attributes"]["NORMAL"]).astype(float)
    q["attributes"]["NORMAL"] = E._add(np.where(zona[w][:, None], N[w], viejo), "VEC3", 34962)
    # copa negra: su borde sigue a la orilla de la rendija
    bord = np.where(cerca_rendija & mov)[0]
    if len(bord):
        arbol = cKDTree(P0[bord]); dz = P[bord] - P0[bord]
        for p in E.prims(v24.BOCA_INT):
            Vc, Tc = E.leer(p)
            if len(Vc) < 300:
                continue
            dd, i = arbol.query(Vc)
            E.escribir(p, Vc + np.exp(-(dd / 0.0015) ** 2)[:, None] * dz[i], Tc)
    E.b = bytes(E.out)
    E.log.append({"operacion": "boca plana V30 (residuo sobre la curva natural de la quijada)", "vertices": int(mov.sum()),
                  "coef_superficie": [round(float(c), 5) for c in cz], "anillo_ajuste": int(anillo.sum()),
                  "quijada_g": {"vertices": n_g, "error_max": round(err_g, 5)}})


def main(src, dst):
    t28 = dst + ".v28.glb"
    v28.main(src, t28)
    E = re.Editor(t28)
    aplanar(E)
    copa_detras(E)
    v25.dientes_adentro(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V30: V28 + boca plana sin escalón en la quijada (gestos intactos). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t28)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-3:]:
        print(x)
