"""Theo V08 (sobre V07) / Adán V15 (--solo-estilo): cráneo, contorno de ojos y boca sumida.

Pedido de Admin: «corrige la forma del cráneo, el contorno de los ojos y la boca sumida».
- Cráneo: el cráneo real es el gorro de pelo + la máscara de la cara. Era una bala: punta estrecha
  arriba (|u| 0.78 en v −1.5), ancho máximo 1.33 en v −0.5 y un pellizco brusco a 1.13 en las sienes.
  Se lleva a una caja redondeada: ancho ≈1.24 ED de v −1.0 a −0.5 y bajada suave a 1.14 en v −0.1,
  con la parte alta más llena (1.06 en v −1.4).
- Contorno de ojos: la máscara tenía cuencas con borde y los párpados (4 piezas con morph de
  parpadeo) asomaban por la placa formando un marco. Se rellenan las cuencas, las placas de ojo y
  ceja se apoyan sobre la cara, y los párpados abiertos quedan bajo la placa (el parpadeo se conserva).
- Boca sumida: la zona de la boca se eleva a la superficie suave de la cara baja conservando el
  detalle fino de los labios; el interior y el fondo negro se mueven igual.
Uso: python receta_theo_v08.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, y, S = v5.ED, v5.YC, v5.y, re._suave
PIEL, BOCA = v5.PIEL, v5.BOCA
es_cabeza = v5.es_cabeza
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")
OJOS = ("C7V2_eye_BAKE_L", "C7V2_eye_BAKE_R")
CEJAS = ("C7V2_brow_BAKE_L", "C7V2_brow_BAKE_R")

# ancho objetivo del cráneo (medio ancho en ED) por altura v
V_T = np.array([-1.7, -1.6, -1.5, -1.4, -1.3, -1.2, -1.1, -1.0, -0.5, -0.4, -0.3, -0.2, -0.1])
W_T = np.array([0.60, 0.82, 0.97, 1.07, 1.13, 1.18, 1.21, 1.24, 1.24, 1.22, 1.19, 1.16, 1.14])


def _cabeza(E):
    out = []
    for mat in (PIEL,) + PELO:
        for p in E.prims(mat):
            V, _ = E.leer(p)
            if mat == PIEL and not es_cabeza(V):
                continue
            out.append(V)
    return np.concatenate(out)


def campo_craneo(E):
    H = _cabeza(E)
    vH = (YC - H[:, 1]) / ED
    bins = np.arange(-1.75, -0.05, 0.05)
    Wc = np.array([np.abs(H[(vH >= b) & (vH < b + 0.05), 0]).max() / ED if ((vH >= b) & (vH < b + 0.05)).any() else np.nan
                   for b in bins])
    vc = bins + 0.025
    ok = np.isfinite(Wc)
    vc, Wc = vc[ok], Wc[ok]

    def f(V):
        v = (YC - V[:, 1]) / ED
        wt = np.interp(v, V_T, W_T)
        wc = np.interp(v, vc, Wc)
        dentro = (v > V_T[0]) & (v < V_T[-1] + 0.15)
        rampa = S((V_T[-1] + 0.15 - v) / 0.15)          # se apaga suave al llegar a v ≈ 0
        a = 0.85 * S((v + 1.0) / 0.3)                      # pivote: 0 arriba (sin rasgos), 0.85 ED cerca de la cara
        k = np.where(dentro, (wt - a) / np.maximum(wc - a, 1e-3), 1.0)
        k = 1 + (k - 1) * rampa
        ax = np.abs(V[:, 0]) / ED
        fuera = ax > a
        V1 = V.copy()
        V1[:, 0] = np.where(fuera, np.sign(V[:, 0]) * (a + (ax - a) * k) * ED, V[:, 0])
        J = np.tile(np.eye(3), (len(V), 1, 1)); J[:, 0, 0] = np.where(fuera, k, 1.0)
        return V1, J
    return f


def _caja_placa(E, material, margen):
    P = np.concatenate([E.leer(p)[0] for p in E.prims(material)])
    return P[:, 0].min() - margen, P[:, 0].max() + margen, P[:, 1].min() - margen, P[:, 1].max() + margen


def _dist_caja(V, caja):
    x0, x1, y0, y1 = caja
    dx = np.maximum(np.maximum(x0 - V[:, 0], V[:, 0] - x1), 0)
    dy = np.maximum(np.maximum(y0 - V[:, 1], V[:, 1] - y1), 0)
    return np.hypot(dx, dy)


def _cuad(X, Y):
    return np.c_[np.ones(len(X)), X, Y, X * X, X * Y, Y * Y]


def superficies_ojos(E):
    """Por ojo: superficie cuadrática z(x, y) ajustada al anillo de piel alrededor de la cuenca."""
    H = next(E.leer(p)[0] for p in E.prims(PIEL) if es_cabeza(E.leer(p)[0]))
    sup = {}
    for mat in OJOS:
        caja = _caja_placa(E, mat, 0.0)
        d = _dist_caja(H, caja)
        anillo = (d > 0.10 * ED) & (d < 0.30 * ED) & (H[:, 2] > 0.09)
        c, *_ = np.linalg.lstsq(_cuad(H[anillo, 0], H[anillo, 1]), H[anillo, 2], rcond=None)
        sup[mat] = (caja, c)
    return sup


def campo_rellenar_cuencas(sup):
    def f(V):
        V1 = V.copy()
        for caja, c in sup.values():
            d = _dist_caja(V, caja)
            w = S((0.12 * ED - d) / (0.08 * ED)) * (V[:, 2] > 0.09)
            z = _cuad(V[:, 0], V[:, 1]) @ c
            V1[:, 2] = V1[:, 2] + (z - V1[:, 2]) * w
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


def campo_apoyar(c, sobre=0.0015):
    def f(V):
        V1 = V.copy(); V1[:, 2] = _cuad(V[:, 0], V[:, 1]) @ c + sobre
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


def campo_apoyar_local(H, sobre):
    """z de cada vértice = z de la piel debajo (promedio ponderado de los 8 vecinos más cercanos en x, y) + sobre."""
    Hf = H[H[:, 2] > 0.09]

    def f(V):
        V1 = V.copy()
        for i in range(0, len(V), 2000):
            B = V[i:i + 2000]
            d2 = ((B[:, None, :2] - Hf[None, :, :2]) ** 2).sum(-1)
            idx = np.argsort(d2, 1)[:, :8]
            w = 1 / (np.take_along_axis(d2, idx, 1) + 1e-10)
            V1[i:i + 2000, 2] = (Hf[idx, 2] * w).sum(1) / w.sum(1) + sobre
        return V1, np.tile(np.eye(3), (len(V), 1, 1))
    return f


def parpados_bajo_placa(E, sup, debajo=0.002):
    """Los párpados (4 piezas con morph de parpadeo) asomaban por la placa del ojo y dibujaban un marco.
    Abiertos quedan bajo la superficie de la placa; al morph se le suma lo que se bajó, así el
    parpadeo cerrado queda exactamente igual que antes."""
    n = 0
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not (len(V) == 1377 and V[:, 1].min() > 0.55):
            continue
        mat = OJOS[0] if V[:, 0].mean() > 0 else OJOS[1]
        caja, c = sup[mat]
        dentro = _dist_caja(V, caja) < 0.02 * ED
        zt = _cuad(V[:, 0], V[:, 1]) @ c - debajo
        dz = np.where(dentro, np.maximum(V[:, 2] - zt, 0), 0)
        V1 = V.copy(); V1[:, 2] -= dz
        T1 = []
        for D in T:
            D1 = D.copy()
            if np.abs(D).max() > 0:
                D1[:, 2] += dz
            T1.append(D1)
        E.escribir(p, V1, T1)
        n += int((dz > 0).sum())
    E.log.append({"operacion": "párpados abiertos bajo la placa del ojo (parpadeo intacto)", "material": PIEL, "vertices_movidos": n})


def superficie_frente(E):
    """Superficie suave de la frente (para apoyar las cejas)."""
    H = next(E.leer(p)[0] for p in E.prims(PIEL) if es_cabeza(E.leer(p)[0]))
    v = (YC - H[:, 1]) / ED
    m = (v > -0.85) & (v < -0.25) & (np.abs(H[:, 0]) < 1.0 * ED) & (H[:, 2] > 0.09)
    c, *_ = np.linalg.lstsq(_cuad(H[m, 0], H[m, 1]), H[m, 2], rcond=None)
    return c


def peso_boca(V):
    v = (YC - V[:, 1]) / ED
    return S(1 - np.sqrt((V[:, 0] / (0.75 * ED)) ** 2 + ((v - 0.58) / 0.32) ** 2)) * S((V[:, 2] - 0.08) / 0.02)


def campo_boca_al_frente(E):
    """dz(x, y) = superficie suave de la cara baja − versión suavizada de la malla actual (solo hacia afuera)."""
    for p in E.prims(PIEL):
        V, _ = E.leer(p)
        if es_cabeza(V):
            F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
            break
    v = (YC - V[:, 1]) / ED
    u = np.abs(V[:, 0]) / ED
    anillo = (v > 0.25) & (v < 1.0) & (u < 1.1) & (V[:, 2] > 0.08) & (peso_boca(V) < 0.05)
    A = lambda X, Y: np.c_[np.ones(len(X)), X ** 2, Y, Y ** 2, X ** 2 * Y, X ** 4]  # noqa: E731
    c, *_ = np.linalg.lstsq(A(V[anillo, 0], V[anillo, 1]), V[anillo, 2], rcond=None)
    # versión de baja frecuencia de z (quita el detalle de labios)
    z = V[:, 2].copy()
    E2 = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); E2 = np.concatenate([E2, E2[:, ::-1]])
    cnt = np.bincount(E2[:, 0], minlength=len(V))
    for _ in range(40):
        s = np.bincount(E2[:, 0], weights=z[E2[:, 1]], minlength=len(V))
        z = 0.5 * z + 0.5 * s / np.maximum(cnt, 1)
    zfit = A(V[:, 0], V[:, 1]) @ c
    detalle = V[:, 2] - z                              # labios y abertura (alta frecuencia)
    dz = (zfit + 0.35 * detalle - V[:, 2]) * peso_boca(V)  # zona = superficie suave + 35 % del detalle
    # interpolador por (x, y) para mover interior y fondo de la boca igual que la piel
    sel = np.abs(dz) > 1e-5
    pts, val = V[sel, :2], dz[sel]

    def f(W):
        if len(pts) == 0:
            return W.copy(), np.tile(np.eye(3), (len(W), 1, 1))
        d2 = ((W[:, None, :2] - pts[None]) ** 2).sum(-1)
        idx = np.argsort(d2, 1)[:, :6]
        wgt = 1 / (np.take_along_axis(d2, idx, 1) + 1e-10)
        dzw = (val[idx] * wgt).sum(1) / wgt.sum(1)
        cerca = np.take_along_axis(d2, idx[:, :1], 1)[:, 0] < (0.06 * ED) ** 2
        W1 = W.copy(); W1[:, 2] += np.where(cerca, dzw, 0)
        return W1, np.tile(np.eye(3), (len(W), 1, 1))

    def f_piel(W):
        W1 = W.copy(); W1[:, 2] += dz
        return W1, np.tile(np.eye(3), (len(W), 1, 1))
    return f_piel, f, float(np.abs(dz).max() / ED)


def main(src, dst, identidad=True):
    E = re.Editor(src)
    cr = campo_craneo(E)
    E.deformar(PIEL, cr, "cráneo: caja redondeada (ancho 1.24 ED en v −1.0…−0.5, sienes sin pellizco)", primitiva=es_cabeza)
    for mat in PELO:
        E.deformar(mat, cr, f"cráneo: {mat} sigue la forma")
    sup = superficies_ojos(E)
    E.deformar(PIEL, campo_rellenar_cuencas(sup), "cuencas de los ojos rellenas (sin marco)", primitiva=es_cabeza)
    for mat in OJOS:
        E.deformar(mat, campo_apoyar(sup[mat][1]), f"{mat}: apoyada sobre la cara (+1.5 mm)")
    parpados_bajo_placa(E, sup)
    H = next(E.leer(p)[0] for p in E.prims(PIEL) if es_cabeza(E.leer(p)[0]))
    for mat in CEJAS:
        caja = _caja_placa(E, mat, 0.08 * ED)
        m = (_dist_caja(H, caja) == 0) & (H[:, 2] > 0.09)
        c, *_ = np.linalg.lstsq(_cuad(H[m, 0], H[m, 1]), H[m, 2], rcond=None)  # superficie suave bajo la ceja
        loc = campo_apoyar_local(H, 0.0)

        def f(V, c=c, loc=loc):
            zq = _cuad(V[:, 0], V[:, 1]) @ c
            zl = loc(V)[0][:, 2]
            V1 = V.copy(); V1[:, 2] = np.maximum(zq, zl) + 0.002   # suave, pero nunca bajo la piel
            return V1, np.tile(np.eye(3), (len(V), 1, 1))
        E.deformar(mat, f, f"{mat}: apoyada sobre la frente (+2 mm, superficie suave sin quedar bajo la piel)")
    f_piel, f_boca, dzmax = campo_boca_al_frente(E)
    E.deformar(PIEL, f_piel, f"boca: zona llevada a la superficie de la cara con 35 % del detalle (máx. {dzmax:.2f} ED)", primitiva=es_cabeza)
    E.deformar(BOCA, f_boca, "boca: interior y fondo se mueven igual")
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    E.recalcular_normales(BOCA, None, "normales recalculadas: boca")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V08" if identidad else "Adán V15") + ": cráneo, contorno de ojos y boca (CHXP + SENKU). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
