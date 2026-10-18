"""Adán V25 (sobre V22 HABLA → V24): boca sin surcos y orejas nuevas medidas con SENKU.

Boca:
  - En reposo había un surco arriba y otro abajo del labio (curvatura de CHXP: bandas cóncavas). Se suaviza
    la piel en un anillo alrededor de la boca (Taubin, conserva volumen) sin tocar el borde de la rendija.
  - Al abrir, el labio de arriba arrastraba una banda angosta (surco). Las caídas del campo de la boca se
    ensanchan (CAIDA_SUP 0.12→0.24, CAIDA_LABIO 0.08→0.16, CAIDA_COMISURA 0.15→0.25 ED).
Orejas (SENKU, copox/medicion/orejas.py, contra la Hoja de vistas de perfil):
  V24 medía 1.03 ojos de alto (ref 1.39), quedaba 0.30 ojos bajo el ojo (ref 0.22) y sobresalía 9 % de la
  cabeza (ref 8 %). Se retira la oreja de caja y se hace una nueva que sigue la piel de la cabeza:
  rectángulo vertical con esquinas redondeadas (superelipse), bisel suave, hueco (concha) de 0.27 × 0.46
  corrido hacia la cara, inclinada 6° hacia atrás, pesada 100 % a Head.
Uso: python receta_adan_v25.py ADAN_V22_HABLA.glb ADAN_V25.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion import gestos  # noqa: E402
from copox.medicion import orejas  # noqa: E402
from copox.medicion.gltf import Modelo, accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402

PIEL = v24.PIEL
S = re._suave

# --- oreja (medidas en unidades del ojo visible de Adán) ------------------------
INCLINA = np.radians(6.0)
NU, NV = 28, 36            # rejilla de la cara exterior de la oreja
BISEL = 0.22               # fracción del radio donde baja el bisel
REDONDEZ = 5.0             # exponente de la superelipse (2 = elipse, ∞ = rectángulo)
HUECO_CENTRO = (0.18, 0.0) # (hacia la cara, arriba) en fracción del semiancho/semialto
HUECO_PROF = 0.45          # fracción del grosor


def _superelipse(a, b):
    """Rejilla cuadrada [-1,1]² → rectángulo redondeado unitario (misma topología)."""
    r = np.maximum(np.abs(a), np.abs(b))
    with np.errstate(invalid="ignore", divide="ignore"):
        da, db = a / np.where(r == 0, 1, r), b / np.where(r == 0, 1, r)
        s = (np.abs(da) ** REDONDEZ + np.abs(db) ** REDONDEZ) ** (-1 / REDONDEZ)
    return r * da * s, r * db * s, r


def oreja(alto, ancho, grosor, centro_yz, lado, piel_x):
    """Malla de la oreja: cara exterior como campo de alturas sobre la piel (+x hacia afuera para lado=1)."""
    a, b = np.meshgrid(np.linspace(-1, 1, NU), np.linspace(-1, 1, NV))
    qa, qb, r = _superelipse(a, b)
    hz, hy = ancho / 2, alto / 2
    # u: hacia la cara (+z), v: arriba (+y)
    u, v = qa, qb
    ca, sa = np.cos(INCLINA), np.sin(INCLINA)
    z = centro_yz[1] + (u * hz) * ca - (v * hy) * sa       # la parte de arriba se va hacia atrás
    y = centro_yz[0] + (u * hz) * sa + (v * hy) * ca
    # altura: bisel suave en el borde; el borde mismo queda 1.5 mm·u metido en la piel
    h = grosor * np.clip((1 - r) / BISEL, 0, 1) ** 0.6
    h = h - 0.0015 * (r > 0.999)
    # hueco
    pu, pv = HUECO_CENTRO
    du = (u - pu) / (orejas.REF["hueco_ancho"]); dv = (v - pv) / (orejas.REF["hueco_alto"])
    dentro = np.maximum(np.abs(du), np.abs(dv))
    h = h - HUECO_PROF * grosor * S((1 - dentro) / 0.25)
    x = piel_x(y.ravel(), z.ravel()).reshape(y.shape) + lado * h
    V = np.stack([x, y, z], -1).reshape(-1, 3)
    F = []
    for i in range(NV - 1):
        for k in range(NU - 1):
            p0 = i * NU + k
            F += [[p0, p0 + NU, p0 + 1], [p0 + 1, p0 + NU, p0 + NU + 1]]
    F = np.array(F)
    if lado < 0:
        F = F[:, ::-1]
    # orientación: la normal debe apuntar hacia afuera (±x)
    T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    if (n[:, 0] * lado).mean() < 0:
        F = F[:, ::-1]
    sombra = 1 - 0.18 * S((1 - dentro) / 0.25).ravel()      # el hueco un poco más oscuro (oclusión pintada)
    return V, F, sombra


def piel_x_func(E, lado):
    from scipy.spatial import cKDTree
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V = accesor(E.j, E.b, q["attributes"]["POSITION"]).astype(float)
    V = V[lado * V[:, 0] > 0.10]
    arbol = cKDTree(V[:, 1:])

    def f(y, z):
        d, i = arbol.query(np.stack([y, z], 1), k=6)
        w = 1 / np.maximum(d, 1e-6)
        return (V[i, 0] * w).sum(1) / w.sum(1)
    return f


def nuevas_orejas(E, med):
    ojo_alto = med["ojo_alto"]
    alto = orejas.REF["alto_ojos"] * ojo_alto
    ancho = orejas.REF["ancho_sobre_alto"] * alto
    arriba = med["ojo_arriba"] - orejas.REF["arriba_bajo_ojo"] * ojo_alto
    centro_y = arriba - alto / 2
    grosor = orejas.REF["sobresale_cabeza"] * med["cabeza_ancho"]
    centro_z = med["oreja_z"]
    # retirar la oreja vieja (caja + ranura en C): plegada dentro de la cabeza
    nodo, malla = v24._malla_rostro(E)
    for p in malla["primitives"]:
        if E.j["materials"][p["material"]]["name"] != PIEL:
            continue
        V, T = E.leer(p)
        c = V.mean(0)
        if len(V) < 200 and abs(c[0]) > 0.12 and 0.55 < c[1] < 0.67:
            p["attributes"]["POSITION"] = E._add(np.tile(c * [0.5, 1, 1], (len(V), 1)), "VEC3", 34962, True)
    E.b = bytes(E.out)
    E.log.append({"operacion": "oreja vieja retirada (caja y ranura plegadas dentro de la cabeza)"})
    for lado in (1, -1):
        px = piel_x_func(E, lado)
        # "sobresale" se mide en la silueta de frente: desde lo más ancho de la cabeza, no desde la piel bajo la oreja
        hundida = med["cabeza_ancho"] / 2 - abs(float(px(np.array([centro_y]), np.array([centro_z]))[0]))
        V, F, sombra = oreja(alto, ancho, grosor + max(hundida, 0.0), (centro_y, centro_z), lado, px)
        re.agregar_malla(E, "ADAN_CUERPO", PIEL, V, F, "Head", f"oreja nueva {'L' if lado > 0 else 'R'}",
                         color=None)
        # color por vértice (sombra del hueco), en el mismo formato que la piel
        prim = malla["primitives"][-1]
        C = np.ones((len(V), 4), np.float32); C[:, :3] = sombra[:, None]
        prim["attributes"]["COLOR_0"] = E._add(C, "VEC4", 34962)
    E.b = bytes(E.out)
    E.log.append({"operacion": "orejas nuevas", "alto": alto, "ancho": ancho, "grosor": grosor,
                  "centro_y": centro_y, "centro_z": centro_z})


def _soldar(V):
    k = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(k, axis=0, return_inverse=True)
    return w.ravel()


def suavizar_boca(E):
    """Los "surcos": el borde de la rendija era dentado (vértices a alturas desparejas) y alrededor de los labios
    había bandas cóncavas. 1) el borde de arriba y el de abajo se ajustan a curvas suaves (y = a + b·x² + c·x⁴),
    y en las comisuras se juntan (sin muescas); 2) se suaviza la piel en un anillo alrededor de la boca: los
    vértices del borde solo se mueven en z; 3) la copa negra de adentro sigue a su borde; 4) normales
    recalculadas soldando costuras.
    Probado y descartado: aplanar los labios contra un ajuste de superficie (la boca quedaba hundida o se veía
    la pared de adentro) y pintar la pared de adentro (manchas)."""
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V, T = E.leer(q)
    F = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
    w = _soldar(V); n = w.max() + 1
    P = np.zeros((n, 3)); np.add.at(P, w, V); P /= np.bincount(w, minlength=n)[:, None]
    Fw = w[F]
    Ed = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
    e, c = np.unique(Ed, axis=0, return_counts=True)
    bnd = np.unique(e[c == 1])
    yr = v24.y_rendija(P[bnd, 0])
    en_boca = (np.abs(P[bnd, 0]) < v24.XW * 1.3) & (np.abs(P[bnd, 1] - yr) < 0.008) & (P[bnd, 2] > 0.10)
    bnd = bnd[en_boca]
    arriba = bnd[P[bnd, 1] >= v24.y_rendija(P[bnd, 0])]
    abajo = bnd[P[bnd, 1] < v24.y_rendija(P[bnd, 0])]
    P0 = P.copy()
    curvas = []
    for grupo in (arriba, abajo):
        x = P[grupo, 0]
        A = np.stack([np.ones_like(x), x ** 2, x ** 4], 1)
        coef, *_ = np.linalg.lstsq(A, P[grupo, 1], rcond=None)
        curvas.append(coef)
    def curva(coef, x):
        return coef[0] + coef[1] * x ** 2 + coef[2] * x ** 4
    for grupo, coef in zip((arriba, abajo), curvas):
        x = P[grupo, 0]
        medio = (curva(curvas[0], x) + curva(curvas[1], x)) / 2
        cierre = S((np.abs(x) / v24.XW - 0.80) / 0.15)        # en las comisuras los dos bordes se juntan: sin muescas
        P[grupo, 1] = (1 - cierre) * curva(coef, x) + cierre * medio
    # anillo alrededor de la boca suavizado (Taubin: no encoge); el borde de la rendija solo se mueve en z
    u = P[:, 0] / v24.ED
    dy = P[:, 1] - v24.y_rendija(P[:, 0])
    W = S(1 - np.sqrt((u / 0.75) ** 2 + ((dy / v24.ED) / 0.32) ** 2)) * S((P[:, 2] - 0.10) / 0.02)
    es_borde = np.zeros(n, bool); es_borde[bnd] = True
    E2 = np.concatenate([e, e[:, ::-1]])
    deg = np.bincount(E2[:, 0], minlength=n)[:, None]
    # primero Laplaciano simple (aplana el bulto de los labios y el surco de encima), luego Taubin (pule sin encoger)
    for _ in range(12):
        for f in (0.5,):
            Sm = np.zeros_like(P); np.add.at(Sm, E2[:, 0], P[E2[:, 1]])
            L = Sm / np.maximum(deg, 1) - P
            L[es_borde, :2] = 0
            P = P + f * W[:, None] * L
    for _ in range(15):
        for f in (0.5, -0.53):
            Sm = np.zeros_like(P); np.add.at(Sm, E2[:, 0], P[E2[:, 1]])
            L = Sm / np.maximum(deg, 1) - P
            L[es_borde, :2] = 0
            P = P + f * W[:, None] * L
    V1 = P[w]
    E.escribir(q, V1, T)
    movidos = int((np.abs(V1 - V).max(1) > 1e-7).sum())
    # copa negra: cada vértice de su borde sigue al vértice del borde de la piel más cercano
    from scipy.spatial import cKDTree
    arbol = cKDTree(P0[bnd]); mov = P[bnd] - P0[bnd]
    for p in E.prims(v24.BOCA_INT):
        Vc, Tc = E.leer(p)
        if len(Vc) < 300:
            continue
        dd, i = arbol.query(Vc)
        peso = np.exp(-(dd / 0.0015) ** 2)[:, None]
        E.escribir(p, Vc + peso * mov[i], Tc)
    # normales soldando costuras (si no, se ven líneas)
    Pn = P
    Tn = Pn[Fw]; Nf = np.cross(Tn[:, 1] - Tn[:, 0], Tn[:, 2] - Tn[:, 0])
    N = np.zeros((n, 3))
    for k in range(3):
        np.add.at(N, Fw[:, k], Nf)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    viejo = accesor(E.j, E.b, q["attributes"]["NORMAL"]).astype(float)
    tocado = (W[w] > 1e-3)[:, None]
    q["attributes"]["NORMAL"] = E._add(np.where(tocado, N[w], viejo), "VEC3", 34962)
    E.b = bytes(E.out)
    E.log.append({"operacion": "boca sin surcos (borde regular + anillo suavizado + normales)", "vertices": movidos,
                  "borde_arriba": int(len(arriba)), "borde_abajo": int(len(abajo))})


def dientes_adentro(E, margen=0.004):
    """Tras alisar la boca, dientes y lengua se vuelven a meter 4 mm·u detrás de la piel (no asoman en reposo)."""
    from scipy.spatial import cKDTree
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    Vp = accesor(E.j, E.b, q["attributes"]["POSITION"]).astype(float); Vp = Vp[Vp[:, 2] > 0.09]
    # solo la cara de enfrente: fuera de la rendija (la pared de adentro de la boca empujaría los dientes al fondo)
    rend = (np.abs(Vp[:, 0]) < v24.XW * 1.1) & (np.abs(Vp[:, 1] - v24.y_rendija(Vp[:, 0])) < 0.004)
    Vp = Vp[~rend]
    arbol = cKDTree(Vp[:, :2])
    for mat in (v24.DIENTES, v24.LENGUA):
        for p in E.prims(mat):
            V, T = E.leer(p)
            d, i = arbol.query(V[:, :2], k=6)
            V2 = V.copy(); V2[:, 2] = np.minimum(V[:, 2], np.median(Vp[i, 2], 1) - margen)
            E.escribir(p, V2, T)
    E.log.append({"operacion": "dientes y lengua detrás de la piel nueva"})


def medir_base(src):
    M = Modelo(src)
    m = orejas.medir(M)
    P = M.posar(None)
    ojo = next(k for k, p in enumerate(M.prims) if p.material.get("name") == "C7V2_eye_BAKE_L")
    po = M.prims[ojo]
    m["ojo_arriba"] = float(P[ojo][po.uv[:, 1] > 0.08][:, 1].max())
    cab = max(range(len(P)), key=lambda k: len(P[k]))
    m["cabeza_ancho"] = float(np.ptp(P[cab][:, 0]))
    O = np.concatenate([P[k] for k in m["primitivas"]])
    m["oreja_z"] = float((O[:, 2].max() + O[:, 2].min()) / 2) - 0.012   # un poco más atrás (ref: 2.7 ojos tras la nariz)
    return m


def main(src, dst):
    v24.CAIDA_SUP, v24.CAIDA_LABIO, v24.CAIDA_COMISURA = 0.24, 0.16, 0.25
    tmp24 = dst + ".v24.glb"
    v24.main(src, tmp24)
    med = medir_base(tmp24)
    E = re.Editor(tmp24)
    suavizar_boca(E)
    dientes_adentro(E)
    nuevas_orejas(E, med)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V25: V24 + boca sin surcos + orejas nuevas medidas con SENKU. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(tmp24)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
