"""Adán V29 (sobre V22 HABLA → V28): boca plana (decisión de Admin, 18 oct 2026: "plana").

La piel alrededor de la boca se reemplaza, en reposo, por una superficie lisa; los gestos (morphs) no se tocan:
son desplazamientos que se suman al reposo, así que se mueven igual desde la cara plana.

Medido (perfil x = 0): el labio de arriba sobresalía 6 mm·u sobre la piel de abajo de la nariz (z 0.158 contra
0.152) en una franja de ~1 cm; el labio de abajo y las comisuras tenían relieves y surcos.

1) Dentro de un óvalo alrededor de la boca, la altura de la piel se rehace con un relleno bi-armónico (Δ²z = 0):
   la superficie más lisa posible que se une sin escalón a la piel de afuera (barbilla, cachetes, base de la nariz).
   Probados y descartados: ajuste local (V26: hundido arriba del labio) y polinomio global (dejaba un aro en la
   orilla del óvalo, visible en Godot como una "U" bajo la boca).
   La rendija queda en su lugar, solo 0.5 mm·u metida para que se lea como línea.
3) La copa negra sigue a la orilla de la rendija; dientes y lengua se meten detrás de la piel nueva.
4) Normales recalculadas (soldando costuras) en la zona y un anillo de vecinos.
Uso: python receta_adan_v29.py ADAN_V22_HABLA.glb ADAN_V29.glb
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

PIEL = v24.PIEL
S = re._suave
# óvalo plano (centro en la rendija): semiejes en x y en y; orilla de desvanecido
OV_X, OV_Y_ARR, OV_Y_ABA, ORILLA = 0.058, 0.030, 0.026, 0.45
METIDA = 0.0005


def base(x, y):
    y = y - v24.Y0
    return np.stack([np.ones_like(x), y, y ** 2, y ** 3, x ** 2, x ** 2 * y, x ** 2 * y ** 2, x ** 4, x ** 4 * y], 1)


def aplanar(E):
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
    M_ = L2[il][:, il]; rhs = -L2[il][:, ifx] @ P[ifx, 2]
    z_new = P[:, 2].copy()
    z_new[il] = spl.spsolve(M_.tocsc(), rhs)
    linea = METIDA * np.exp(-(dy / 0.0030) ** 2) * S((v24.XW * 1.05 - np.abs(P[:, 0])) / 0.008)   # se desvanece en las comisuras
    P0 = P.copy()
    P[:, 2] = np.where(libre, z_new - linea, P[:, 2])
    # pulido: la malla de la cara es irregular (triángulos de tamaños muy distintos) y el relleno deja ondas
    # chicas; Taubin solo en z sobre la superficie (sin la pared), con peso que se apaga en la orilla
    wpul = np.clip((1 + ORILLA - r) / ORILLA, 0, 1) * libre
    for _ in range(40):
        for f_ in (0.5, -0.53):
            zm = np.asarray(A @ P[:, 2]).ravel() / np.maximum(deg, 1)
            P[:, 2] += f_ * wpul * (zm - P[:, 2]) * (deg > 0)
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
            zm = np.asarray(Afull @ P[:, 2]).ravel() / np.maximum(degf, 1)
            P[:, 2] += 0.5 * wc * (zm - P[:, 2])
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
    E.log.append({"operacion": "boca plana (superficie lisa en reposo; gestos intactos)", "vertices": int(mov.sum()),
                  "coef_superficie": [round(float(c), 5) for c in cz], "anillo_ajuste": int(anillo.sum())})


def copa_detras(E, margen=0.0008):
    """La copa negra de la boca no debe asomar por delante de la piel nueva (en las comisuras asomaba hasta
    4.6 mm·u y Godot la proyectaba como sombra: los "hoyuelos" de las comisuras)."""
    from scipy.interpolate import griddata
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    Vf, _ = E.leer(q); Vf = Vf[Vf[:, 2] > 0.10]
    hechos = 0
    for p in E.prims(v24.BOCA_INT):
        V, T = E.leer(p)
        m = (np.abs(V[:, 0]) < 0.07) & (V[:, 1] > 0.49) & (V[:, 1] < 0.58)
        zf = griddata(Vf[:, :2], Vf[:, 2], V[m, :2])
        z = V[m, 2].copy(); ok = ~np.isnan(zf)
        z[ok] = np.minimum(z[ok], zf[ok] - margen)
        hechos += int((np.abs(z - V[m, 2]) > 1e-7).sum())
        V2 = V.copy(); V2[m, 2] = z
        E.escribir(p, V2, T)
    E.log.append({"operacion": "copa negra detrás de la piel", "vertices": hechos})


def main(src, dst):
    t28 = dst + ".v28.glb"
    v28.main(src, t28)
    E = re.Editor(t28)
    aplanar(E)
    copa_detras(E)
    v25.dientes_adentro(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V29: V28 + boca plana (piel lisa en reposo, gestos intactos). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t28)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-2:]:
        print(x)
