"""Adán V26 (sobre V22 HABLA → V25): boca y labios sin bultos.

SENKU (copox/medicion/rugosidad.py): desviación de la curvatura en el anillo de la boca contra la mejilla.
V25: reposo 4.1× la mejilla, boca_sonrisa 8.7×, vis_A 8.9×, boca_o 8.7×. Los picos estaban en la cresta del
labio de arriba (y ≈ 0.547, 13 mm·u sobre la rendija) y en las comisuras; los gestos viejos de boca (de V13)
hacían grumos en las esquinas.

1) Labios al ras: cada vértice del anillo (fuera de la franja de la rendija, |dy| > 2.5 mm·u) toma la altura
   de un ajuste cuadrático local (mínimos cuadrados móviles) hecho con la piel de AFUERA de la franja de
   los labios; la pared de adentro de la boca (más de 1.5 mm·u detrás del ajuste) no se toca. Luego Taubin.
2) Gestos viejos de boca rehechos con campos limpios (los mismos de V24): boca_sonrisa, boca_triste,
   boca_tensa, boca_lado_L/R, boca_o, boca_abrir, boca_soplar.
3) Todos los morphs de boca (visemas, comisuras, ancha/estrecha, dientes, sonrisa abierta) con el delta
   suavizado sobre la malla (sin escalones).
Uso: python receta_adan_v26.py ADAN_V22_HABLA.glb ADAN_V26.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion import gestos  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402
import receta_adan_v25 as v25  # noqa: E402

PIEL = v24.PIEL
S = re._suave

VIEJOS = {
    "boca_sonrisa": dict(arriba=.0, mand=.0, labio=.0, perfil=0, ancho=1.10, comisuras=.12, trompa=.0),
    "boca_triste": dict(arriba=-.012, mand=.0, labio=-.014, perfil=0, ancho=0.96, comisuras=-.07, trompa=.0),
    "boca_tensa": dict(arriba=-.010, mand=.0, labio=-.010, perfil=0, ancho=1.04, comisuras=-.02, trompa=.0),
    "boca_o": dict(arriba=.04, mand=.06, labio=.05, perfil=.9, ancho=0.70, comisuras=.0, trompa=.04),
    "boca_abrir": dict(arriba=.03, mand=.14, labio=.05, perfil=.5, ancho=1.0, comisuras=.0, trompa=.0),
    "boca_soplar": dict(arriba=.0, mand=.0, labio=.0, perfil=0, ancho=0.80, comisuras=.0, trompa=.06),
}
APLANAR = False   # probado: el ajuste local dejaba un hundido arriba del labio (rugosidad 4.1→8.4); descartado
SUAVIZAR = ["vis_A", "vis_E", "vis_I", "vis_O", "vis_U", "vis_MBP", "vis_FV", "mandibula", "boca_sonrisa_abierta",
            "boca_dientes", "boca_ancha", "boca_estrecha", "comisura_arriba_L", "comisura_arriba_R",
            "comisura_abajo_L", "comisura_abajo_R"]


def campo_lado(signo):
    """La boca se corre hacia un lado (signo +1 = +x) y esa comisura sube un poco."""
    def f(V):
        u = V[:, 0] / v24.ED
        d = (V[:, 1] - v24.y_rendija(V[:, 0])) / v24.ED
        w = S(1 - np.sqrt((u / 0.70) ** 2 + (d / 0.30) ** 2)) * v24._frente(V)
        D = np.zeros_like(V)
        D[:, 0] = signo * 0.10 * v24.ED * w
        D[:, 1] = 0.04 * v24.ED * w * S(signo * u / 0.3)
        return D
    return f


def aplanar_labios(E):
    from scipy.spatial import cKDTree
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V, T = E.leer(q)
    F = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
    w = v25._soldar(V); n = w.max() + 1
    P = np.zeros((n, 3)); np.add.at(P, w, V); P /= np.bincount(w, minlength=n)[:, None]
    dy = P[:, 1] - v24.y_rendija(P[:, 0])
    u = P[:, 0] / v24.ED
    r = np.sqrt((u / 0.75) ** 2 + ((dy / v24.ED) / 0.40) ** 2)
    frente = P[:, 2] > 0.11
    fuera = frente & (r < 2.3) & ((dy > 0.024) | (dy < -0.022) | (np.abs(u) > 0.55))
    Q = P[fuera]; arbol = cKDTree(Q[:, :2])
    z_fit = P[:, 2].copy(); ok = np.zeros(n, bool)
    for i in np.where(frente & (r < 1.05) & (np.abs(dy) > 0.0025))[0]:
        idx = arbol.query_ball_point(P[i, :2], 0.032)
        if len(idx) < 15:
            continue
        X = Q[idx, :2] - P[i, :2]
        wq = np.exp(-(np.linalg.norm(X, axis=1) / 0.020) ** 2)
        A = np.stack([np.ones(len(X)), X[:, 0], X[:, 1], X[:, 0] ** 2, X[:, 0] * X[:, 1], X[:, 1] ** 2], 1)
        sw = np.sqrt(wq)[:, None]
        cf, *_ = np.linalg.lstsq(A * sw, Q[idx, 2] * sw[:, 0], rcond=None)
        z_fit[i] = cf[0]; ok[i] = True
    pared = P[:, 2] < z_fit - 0.0015
    b = S((1.05 - r) / 0.35) * ok * ~pared
    # cerca de la rendija la orilla queda apenas metida (0.6 mm·u): se lee como línea, no como labio
    z_obj = z_fit - 0.0006 * np.exp(-(dy / 0.004) ** 2) * (np.abs(P[:, 0]) < v24.XW * 1.05)
    P0 = P.copy()
    P[:, 2] = (1 - b) * P[:, 2] + b * z_obj
    # pulido Taubin en el anillo (los vértices de la rendija no se mueven en x-y)
    Ed = np.sort(np.concatenate([w[F][:, [0, 1]], w[F][:, [1, 2]], w[F][:, [2, 0]]]), 1)
    e = np.unique(Ed, axis=0); E2 = np.concatenate([e, e[:, ::-1]])
    deg = np.bincount(E2[:, 0], minlength=n)[:, None]
    W = S((1.0 - r) / 0.3) * frente * ~pared
    cerca = np.abs(dy) < 0.0025
    for _ in range(10):
        for f in (0.5, -0.53):
            Sm = np.zeros_like(P); np.add.at(Sm, E2[:, 0], P[E2[:, 1]])
            L = Sm / np.maximum(deg, 1) - P
            L[cerca, :2] = 0
            P = P + f * W[:, None] * L
    E.escribir(q, P[w], T)
    # normales soldadas donde se movió
    Fw = w[F]; Tn = P[Fw]; Nf = np.cross(Tn[:, 1] - Tn[:, 0], Tn[:, 2] - Tn[:, 0])
    N = np.zeros((n, 3))
    for k in range(3):
        np.add.at(N, Fw[:, k], Nf)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    viejo = accesor(E.j, E.b, q["attributes"]["NORMAL"]).astype(float)
    mov = (np.abs(P - P0).max(1) > 1e-7)
    # las normales cambian también un anillo de vecinos
    for _ in range(2):
        m2 = mov.copy(); m2[E2[mov[E2[:, 0]], 1]] = True; mov = m2
    q["attributes"]["NORMAL"] = E._add(np.where(mov[w][:, None], N[w], viejo), "VEC3", 34962)
    E.b = bytes(E.out)
    E.log.append({"operacion": "labios al ras (ajuste local + Taubin)", "vertices": int(mov.sum())})


def main(src, dst):
    tmp25 = dst + ".v25.glb"
    v25.main(src, tmp25)
    E = re.Editor(tmp25)
    if APLANAR:
        aplanar_labios(E)
        v25.dientes_adentro(E)
    for nm, forma in VIEJOS.items():
        v24.reemplazar_morph(E, nm, v24.campo_boca(**forma), v24._boca_elegible, suavizar=6)
    v24.reemplazar_morph(E, "boca_lado_L", campo_lado(1), v24._boca_elegible, suavizar=6)
    v24.reemplazar_morph(E, "boca_lado_R", campo_lado(-1), v24._boca_elegible, suavizar=6)
    # suavizar deltas de los demás morphs de boca
    nodo, malla = v24._malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    q = max(malla["primitives"], key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V, T = E.leer(q)
    for nm in SUAVIZAR:
        i = nombres.index(nm)
        if np.abs(T[i]).max() == 0:
            continue
        D = gestos.suavizar_delta(E, q, V, T[i], 8)
        q["targets"][i]["POSITION"] = E._add(D, "VEC3", None, True)
    E.b = bytes(E.out)
    E.log.append({"operacion": "deltas de boca suavizados", "morphs": SUAVIZAR})
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V26: V25 + labios al ras y gestos de boca limpios. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(tmp25)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
