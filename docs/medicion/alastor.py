"""Alastor Kleinteil (19 oct 2026) · piezas propias sobre la base congelada: pelo, abrigo, cinturón y gafas.
Admin: «Básate en los renders originales, en donde se ve a Alastor original» → refs/personajes/alastor/originales/
(3/4 de cuerpo completo = principal, frente de la comparativa, ícono). Briefs: docs/investigacion/{pelo_alastor,
abrigo,gafas}.md. Ficha: personajes/alastor.json (python -m copox.avatar).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

V47 = os.environ.get("ALTH_ADAN_V47", "/home/claude/build43/ADAN_V47.glb")   # base del cráneo del pelo (como Theo)
# Pelo (originales): bloques facetados grandes y romos que barren hacia SU izquierda (+x), donde abultan; un rizo en «C»
# cae sobre la frente a su derecha; lados cortos sobre la oreja. Sin espalda en los originales: bloques a la nuca.
# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm, despega[, giro]); az 0 = frente, +90 = su izquierda (+x)
MECHONES = [
    # v02 (revisor: «bloques grandes y romos, frente despejada, volumen a su izquierda»): pocos bloques anchos y altos
    (-30, 70, 10, 92, 170, 52, 0.0), (-10, 74, 60, 86, 170, 52, 0.0),            # copete: sube desde la frente
    (20, 70, 110, 60, 160, 50, 0.0), (60, 62, 120, 30, 150, 50, 0.014),         # su izquierda: masa que abulta
    (-60, 66, -110, 40, 130, 42, 0.004), (0, 84, 180, 62, 170, 50, 0.0),
    (-120, 60, -150, -30, 150, 40, 0.006), (120, 60, 150, -30, 150, 40, 0.006), (180, 66, 180, -36, 160, 40, 0.006),
]
PELO = dict(color="#4A3220", escala=1.55, afilar=0.0, punta=1.0,              # marron_calido/5 (chocolate)
            volumen=dict(corona=0.050, lados=0.004, el0=10.0, el1=70.0))


def pelo(E, carpeta):
    import pelo_personaje as pp
    return pp.pelo(E, V47, carpeta, None, MECHONES, PELO["color"], nodo="CAPA_PELO_ALASTOR", pieza="PELO_ALASTOR",
                   prefijo="PeloA", escala=PELO["escala"], afilar=PELO["afilar"], punta=PELO["punta"],
                   volumen=PELO["volumen"])


RIZO = dict(centro=(-0.040, 0.727), radio=0.044, z=0.186, ang=(75.0, 315.0), ancho=(0.030, 0.013), grueso=0.024, n=18)


def _barrido(C, anchos, gruesos, eje_z=np.array([0, 0, 1.0])):
    """Barrido de sección rectangular a lo largo de la curva C (n, 3) en el plano xy, facetado."""
    tang = np.gradient(C, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    nrm = np.cross(eje_z, tang); nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    an = []
    for i in range(len(C)):
        a_, g_ = anchos[i] / 2, gruesos[i] / 2
        an.append([C[i] + nrm[i] * a_ + eje_z * g_, C[i] - nrm[i] * a_ + eje_z * g_,
                   C[i] - nrm[i] * a_ - eje_z * g_, C[i] + nrm[i] * a_ - eje_z * g_])
    V = np.array(an).reshape(-1, 3); T = []
    for i in range(len(C) - 1):
        for k in range(4):
            a0, a1, b0, b1 = 4 * i + k, 4 * i + (k + 1) % 4, 4 * (i + 1) + k, 4 * (i + 1) + (k + 1) % 4
            T += [(a0, b0, b1), (a0, b1, a1)]
    T += [(0, 2, 1), (0, 3, 2)]
    e = 4 * (len(C) - 1); T += [(e, e + 1, e + 2), (e, e + 2, e + 3)]
    return V, np.array(T)


def rizo(E):
    """El rizo en «C» de los originales como pieza explícita (PLATEAU de 3 iteraciones con mechones → cambio de técnica,
    brief pelo_alastor.md): barrido de sección rectangular que se afina, sobre la frente, rígido a Head, mismo color."""
    import receta_adan_v41 as v41
    import receta_adan_v49 as v49
    r = RIZO
    th = np.radians(np.linspace(r["ang"][0], r["ang"][1], r["n"]))
    rad = r["radio"] * np.linspace(1.0, 0.75, r["n"])
    hund = np.interp(np.arange(r["n"]), [0, r["n"] / 4, r["n"]], [-0.050, 0.0, 0.004])   # la raíz nace DENTRO del copete
    C = np.c_[r["centro"][0] + rad * np.cos(th), r["centro"][1] + rad * np.sin(th), r["z"] + hund]
    an = np.linspace(r["ancho"][0], r["ancho"][1], r["n"]); gr = np.linspace(r["grueso"], r["grueso"] * 0.6, r["n"])
    V, T = _barrido(C, an, gr)
    c0 = C.mean(0)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    cen = np.repeat(C, 4, axis=0)
    malo = np.einsum("ij,ij->i", fn, V[T].mean(1) - cen[T].mean(1)) < 0
    T[malo] = T[malo][:, ::-1]
    V, T, N = v49._facetado(V, T)
    sk = E.j["skins"][0]
    nombres = [E.j["nodes"][k]["name"] for k in sk["joints"]]
    J = np.zeros((len(V), 4), np.uint16); J[:, 0] = nombres.index("Head")
    W = np.zeros((len(V), 4), np.float32); W[:, 0] = 1
    malla = next(m for m in E.j["meshes"] if m.get("name") == "CAPA_PELO_ALASTOR")
    mat = malla["primitives"][0]["material"]
    malla["primitives"].append(v41._prim_nueva(E, V, T, N, J, W, mat, "PELO_ALASTOR_RIZO"))
    E.b = bytes(E.out)
    return {"operacion": "rizo en C", "tris": int(len(T)), "centro": [round(float(x), 3) for x in c0]}


# ── pelo v03: MASAS esculpidas (brief pelo_alastor.md rev. 2, aprobado por Admin 20 oct 2026) ─────────────────────
# Cada masa = unión suave de gotas elipsoidales (centro x, y, z; semiejes rx, ry, rz) en metros del modelo (cabeza:
# x ±0.162, y 0.488–0.766, frente z 0.154, nuca z −0.136). Tomadas a ojo de la vista 3/4 y del ícono.
MASAS = {
    # v03.2: más volumen arriba (el original sube ~1/4 de la cabeza sobre el cráneo) y el copete más alto
    "copete": [((-0.045, 0.800, 0.100), (0.080, 0.056, 0.066)), ((0.025, 0.842, 0.076), (0.096, 0.064, 0.080)),
               ((0.100, 0.820, 0.036), (0.084, 0.060, 0.080))],
    "lado_izq": [((0.152, 0.736, 0.018), (0.052, 0.068, 0.090)), ((0.162, 0.670, -0.012), (0.040, 0.054, 0.074))],
    "lado_der": [((-0.150, 0.732, 0.030), (0.040, 0.058, 0.080)), ((-0.157, 0.678, 0.000), (0.030, 0.044, 0.064))],
    "coronilla": [((0.010, 0.822, -0.040), (0.138, 0.068, 0.100)), ((0.020, 0.784, -0.104), (0.136, 0.066, 0.076))],
    "nuca_alta": [((0.000, 0.694, -0.132), (0.152, 0.066, 0.048))],
    "nuca_baja": [((0.000, 0.606, -0.136), (0.128, 0.052, 0.038))],
}
RIZO_V3 = dict(centro=(-0.040, 0.727), z=0.186, radio=0.046, ang=(75.0, 315.0), grueso=(0.0135, 0.0075), n=28)
FRENTE = dict(z=0.095, y_linea=0.748, x=0.135)          # zona de la cara que el pelo no cruza (salvo el rizo)
MASAS_K = 0.016                                          # unión suave entre masas
PELO_V3 = dict(color="#4A3220", tris=2600, paso=0.0018, rigidez=7.0, arrastre=0.7, gravedad=0.06)


def _gota(P, c, r):
    q = (P - np.asarray(c)) / np.asarray(r)
    return (np.linalg.norm(q, axis=1) - 1.0) * min(r)


def _masa(P, gotas, k=0.012):
    from copox.medicion.ropa_tubos import smin
    d = _gota(P, *gotas[0])
    for g_ in gotas[1:]:
        d = smin(d, _gota(P, *g_), k)
    return d


def _rizo_curva():
    r = RIZO_V3
    th = np.radians(np.linspace(r["ang"][0], r["ang"][1], r["n"]))
    rad = r["radio"] * np.linspace(1.0, 0.72, r["n"])
    z = r["z"] + np.interp(np.arange(r["n"]), [0, r["n"] * 0.25, r["n"]], [-0.050, 0.0, 0.004])   # raíz dentro del copete; se despega de la frente
    return np.c_[r["centro"][0] + rad * np.cos(th), r["centro"][1] + rad * np.sin(th), z]


def _rizo_sdf(P, C):
    """Tubo que se afina a lo largo de la curva C (distancia al segmento más cercano − radio)."""
    g0, g1 = RIZO_V3["grueso"]
    best = np.full(len(P), 9.0)
    n = len(C) - 1
    for i in range(n):
        a, b = C[i], C[i + 1]
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        rr = g0 + (g1 - g0) * (i + t) / n
        best = np.minimum(best, d - rr)
    return best


def pelo_masas(E, carpeta):
    """Pelo de Alastor por masas esculpidas: 6 masas + rizo en «C» que nace del copete + relleno del cráneo (cobertura),
    malla única facetada; pesos por masa a su cadena de resorte (rigidez alta: el pelo de bloque se mece poco)."""
    import receta_adan_v36 as v36  # noqa: F401
    import receta_adan_v39 as v39
    import receta_adan_v41 as v41
    import receta_adan_v49 as v49
    import vestir_theo_v3 as v3
    from copox.medicion import pelo_huesos as ph
    from copox.medicion.ropa_tubos import smin
    from scipy.spatial import cKDTree
    P_ = v49._prims(E)
    cab = v39._leer(E, P_["Cabeza_PIEL_EXPUESTA_v04"], "POSITION").astype(float)
    guia = np.vstack([v39._leer(E, P_[n], "POSITION").astype(float) for n in P_ if n and n.startswith("GUIA_CAPILAR")])
    arbol_g = cKDTree(guia)
    c_cab = (cab.min(0) + cab.max(0)) / 2
    C_rizo = _rizo_curva()
    nombres_m = list(MASAS)

    def campos(P):
        return [_masa(P, MASAS[n]) for n in nombres_m]

    def sdf(P):
        d_g, _ = arbol_g.query(P)
        relleno = d_g - 0.010                                    # capa sobre la guía capilar: cobertura total
        d = relleno
        for dm in campos(P):
            d = smin(d, dm, MASAS_K)
        f = FRENTE
        cara = np.maximum.reduce([f["z"] - P[:, 2], P[:, 1] - f["y_linea"], np.abs(P[:, 0]) - f["x"]])
        d = np.maximum(d, -cara)                                 # frente despejada
        return d                                                 # el rizo va aparte (barrido nítido, no se simplifica)
    lo = c_cab - np.array([0.25, 0.20, 0.22]); hi = c_cab + np.array([0.25, 0.30, 0.22])
    V, T, N = v3._malla(sdf, lo, hi, PELO_V3["tris"], carpeta, paso=PELO_V3["paso"])
    # pesos: masa más cercana → su cadena; el relleno pegado al cráneo y la parte cercana a la raíz → Head
    M = np.stack(campos(V), 1)
    ids = M.argmin(1)
    sk = E.j["skins"][0]
    nombres_j = [E.j["nodes"][k]["name"] for k in sk["joints"]]
    curvas = []
    for i, n in enumerate(nombres_m):
        if True:
            gotas = np.array([g_[0] for g_ in MASAS[n]])
            fin = gotas.mean(0); d0 = fin - c_cab
            raiz = c_cab + d0 / np.linalg.norm(d0) * 0.10
            pts = np.linspace(raiz, fin + (fin - c_cab) / np.linalg.norm(fin - c_cab) * 0.02, 4)
        curvas.append(pts)
    cadenas, jh = ph.agregar_cadenas(E, curvas, prefijo="PeloA")
    radio = np.linalg.norm(V - c_cab, axis=1)
    s_ = np.clip((radio - 0.13) / 0.08, 0, 1)
    d_g, _ = arbol_g.query(V)
    fijo = (d_g < 0.006) | (M.min(1) > 0.004)                    # relleno pegado al cráneo
    ids = np.where(fijo, len(cadenas), ids)
    J, W = ph.pesos(ids, s_, cadenas, jh, n_base=0)
    J, W = J[T].reshape(-1, 4), W[T].reshape(-1, 4)
    Vf, Tf, Nf = v49._facetado(V, T)
    sk_ib = __import__("copox.medicion.gltf", fromlist=["accesor"]).accesor(E.j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    c_local = (sk_ib[jh] @ np.append(c_cab, 1.0))[:3]
    extras = ph.config([[nombres_j[k] if k < len(nombres_j) else E.j["nodes"][sk["joints"][k]]["name"] for k in cad]
                        for cad in cadenas], c_local, 0.12,
                       rigidez=PELO_V3["rigidez"], arrastre=PELO_V3["arrastre"], gravedad=PELO_V3["gravedad"])
    mat = v41._material(E, "PELO_ALASTOR_COLOR", PELO_V3["color"])
    E.j["materials"][mat]["doubleSided"] = False
    v49._nodo(E, "CAPA_PELO_ALASTOR", [v41._prim_nueva(E, Vf, Tf, Nf, J, W, mat, "PELO_ALASTOR")], junto_a="CAPA_GUIA_CAPILAR")
    E.j["nodes"][-1]["extras"] = extras
    v49._limpiar(carpeta)
    log_r = rizo(E)                                          # rizo en «C»: barrido explícito, raíz dentro del copete
    return {"operacion": "pelo de Alastor por masas", "tris": int(len(T)), "masas": nombres_m, "rizo": log_r,
            "huesos_pelo": 4 * len(cadenas)}


def solo_pelo(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [pelo_masas(E, os.path.dirname(os.path.abspath(dst)))]
    for n in E.j["nodes"]:
        if n.get("name") == "CAPA_PELO_THEO":
            n.setdefault("extensions", {})["KHR_node_visibility"] = {"visible": False}
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Prueba: pelo de Alastor sobre la base congelada. SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return log


# ── ropa: camisa + corbata + pantalón (traje_chaleco sin chaleco) + abrigo + cinturón + gafas ──────────────────────
COL = {"camisa": "#FBEFE1", "corbata": "#232026", "pantalon": "#2C2320", "boton": "#2C2320",     # camisa_blanca,
       "abrigo": "#3A2F2A", "solapa": "#1F1916", "cinturon": "#5F4338", "hebilla": "#9A7B3C",   # uniforme_policia,
       "gafas": "#1F1916"}                                                                       # negro_calido 3/4/5…
TELA = {"abrigo": "lana_cerrada", "solapa": "lana_cerrada", "cinturon": "cuero", "hebilla": "cuero", "gafas": "cuero"}
ABRIGO = dict(capa=0.0070, y_bajo=0.118, cintura=0.300, vuelo=0.030, k=0.012, manga=0.282, cuello=0.0110,
              abertura=((0.10, 0.062), (0.22, 0.046), (0.30, 0.040), (0.40, 0.030), (0.47, 0.040)),
              solapa_ancho=0.042, solapa_y=(0.474, 0.355), tris=8000)
CINTURON = dict(y=0.274, alto=0.016, sobre=0.0030, hebilla=(0.028, 0.021, 0.0055))
GAFAS = dict(ancho=0.106, alto=0.086, grueso=0.0150, fondo=0.012, radio=0.015, sobre=0.005, puente=0.012,
             varilla=0.0070, z_oreja=0.010)


def _w_abertura(y):
    ys, ws = zip(*ABRIGO["abertura"])
    return np.interp(y, ys, ws)


def abrigo(E, carpeta):
    import vestir_theo_capas as v2
    import vestir_theo_v3 as v3
    from copox.medicion import ropa_capas as rc
    from copox.medicion import ropa_tubos as rt
    from copox.medicion import texturas_tela as tt
    import receta_adan_v49 as v49
    U = v3.ULTIMO
    a = ABRIGO
    pz, nombres = U["piezas"], U["nombres"]
    mats = {k: tt.material_textura(E, f"ALASTOR_{k.upper()}", COL[k], TELA[k]) for k in ("abrigo", "solapa", "cinturon", "hebilla")}
    t_ab = U["t_cam"].inflado(a["capa"])
    mangas = [m.inflado(a["capa"]) for m in U["mangas"]]
    pel_v = np.vstack([v3._pts(E, "Pelvis_PIEL"), v3._pts(E, "PiernaL_PIEL", y1=0.30), v3._pts(E, "PiernaR_PIEL", y1=0.30),
                       v3._pts(E, "Torso_PIEL", y1=a["cintura"] + 0.01)])
    hf = lambda ts: 0.012 + a["vuelo"] * np.clip((a["cintura"] - ts) / (a["cintura"] - a["y_bajo"]), 0, 1)   # noqa: E731
    falda = rt.Tubo(pel_v, 1, a["y_bajo"], a["cintura"] + 0.01, 0, n=20, suavizar=3, recto_desde=0.20, holgura_fn=hf)
    cuerpo = rt.union([t_ab.sdf, mangas[0].sdf, mangas[1].sdf, falda.sdf], a["k"])

    def sdf(P):
        x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
        d = np.maximum.reduce([cuerpo(P), a["y_bajo"] - y, y - 0.492, x - a["manga"]])
        hueco = np.where(y > 0.455, 0.040 - np.hypot(x, (z - 0.012) * 0.85), -1.0)        # cuello
        abierto = np.maximum(x - _w_abertura(y), 0.004 - z)                              # abierto al frente
        d = np.maximum.reduce([d, hueco, -abierto])
        # cuello del abrigo: banda alta alrededor del cuello de la camisa, abierta al frente
        cue = np.maximum.reduce([U["t_cuello"].sdf(P) - a["cuello"], np.abs(y - 0.492) - 0.024,
                                 -np.maximum(x - 0.030, 0.010 - z), -(U["t_cuello"].sdf(P) - 0.0015)])
        return np.minimum(d, cue)
    V, T, N = v3._malla(sdf, (-0.29, a["y_bajo"] - 0.01, -0.10), (0.29, 0.515, 0.15), a["tris"], carpeta)
    prims = [v2._prim(E, V, T, N, [pz["Torso_PIEL"], pz["Cuello"], pz["BrazoL"], pz["BrazoR"], pz["Pelvis_PIEL"],
                                   pz["PiernaL_PIEL"], pz["PiernaR_PIEL"]], nombres, mats["abrigo"], "ALASTOR_ABRIGO",
                     tt.ESCALAS["lana_cerrada"])]
    # solapas: placas anchas en V sobre el abrigo, de la orilla de la abertura hacia afuera
    Vs, Ts, o = [], [], 0
    y0, y1 = a["solapa_y"]
    ys = np.linspace(y0, y1, 6)
    for sg in (1, -1):
        w = _w_abertura(ys)
        anch = a["solapa_ancho"] * (1 - 0.85 * (y0 - ys) / (y0 - y1))
        L = np.array([[sg * (wi + 0.001), yi, (rt.superficie_z(sdf, sg * (wi + 0.004), yi) or 0.05) + 0.0012] for wi, yi in zip(w, ys)])
        R = np.array([[sg * (wi + an), yi, (rt.superficie_z(sdf, sg * (wi + an), yi) or 0.05) + 0.0012] for wi, an, yi in zip(w, anch, ys)])
        v, t = rc.placa(L, R, 0.0040, lambda q: np.array([0, 0.2, 1.0]) / np.hypot(0.2, 1.0))
        Vs.append(v); Ts.append(t + o); o += len(v)
    prims.append(v2._prim(E, np.vstack(Vs), np.vstack(Ts), None, [pz["Torso_PIEL"], pz["Cuello"]], nombres, mats["solapa"],
                          "ALASTOR_SOLAPAS", tt.ESCALAS["lana_cerrada"]))
    v49._nodo(E, "CAPA_ABRIGO", prims)
    # cinturón sobre la pretina (se ve por la abertura) + hebilla dorada
    c = CINTURON
    cp = U["cuerpo_pan"]

    def cint(P):
        return np.maximum(cp(P) - c["sobre"], np.abs(P[:, 1] - c["y"]) - c["alto"] / 2)
    Vc, Tc, Nc = v3._malla(cint, (-0.16, c["y"] - 0.02, -0.10), (0.16, c["y"] + 0.02, 0.13), 1600, carpeta)
    zc = rt.superficie_z(cint, 0.0, c["y"]) or 0.08
    # hebilla rectangular (marco con hueco al centro, como el original): aro de sección cuadrada
    Vh, Th = _marco(0.0, c["y"], zc + c["hebilla"][2] * 0.6, c["hebilla"][0], c["hebilla"][1], 0.003, 0.006, c["hebilla"][2], n=1)
    fnh = np.cross(Vh[Th[:, 1]] - Vh[Th[:, 0]], Vh[Th[:, 2]] - Vh[Th[:, 0]])
    ch_ = np.array([0.0, c["y"], zc + c["hebilla"][2] * 0.6])
    radial = Vh[Th].mean(1) - ch_
    Th[np.einsum("ij,ij->i", fnh, radial) < 0] = Th[np.einsum("ij,ij->i", fnh, radial) < 0][:, ::-1]
    prims_c = [v2._prim(E, Vc, Tc, Nc, [pz["Pelvis_PIEL"], pz["Torso_PIEL"]], nombres, mats["cinturon"], "ALASTOR_CINTURON", tt.ESCALAS["cuero"]),
               v2._prim(E, Vh, Th, None, [pz["Pelvis_PIEL"], pz["Torso_PIEL"]], nombres, mats["hebilla"], "ALASTOR_HEBILLA", tt.ESCALAS["cuero"])]
    v49._nodo(E, "CAPA_CINTURON", prims_c)
    v49._limpiar(carpeta)
    return {"operacion": "abrigo + cinturón", "abrigo": int(len(T)), "cinturon": int(len(Tc))}


def _marco(cx, cy, z, w, h, r, t, d, n=3):
    """Aro rectangular de esquinas redondeadas (sección cuadrada t × d), facetado. -> V, T."""
    pts = []
    for (sx, sy), a0 in zip(((1, 1), (-1, 1), (-1, -1), (1, -1)), (0, 90, 180, 270)):
        ccx, ccy = sx * (w / 2 - r), sy * (h / 2 - r)
        for k in range(n + 1):
            ang = np.radians(a0 + 90 * k / n)
            pts.append((ccx + r * np.cos(ang), ccy + r * np.sin(ang)))
    pts = np.array(pts); m = len(pts)
    nrm = pts / np.maximum(np.linalg.norm(pts, axis=1, keepdims=True), 1e-9)
    anillos = []
    for off, dz in ((t / 2, d / 2), (-t / 2, d / 2), (-t / 2, -d / 2), (t / 2, -d / 2)):
        q = pts + nrm * off
        anillos.append(np.c_[cx + q[:, 0], cy + q[:, 1], np.full(m, z + dz)])
    V = np.vstack(anillos)
    T = []
    for a_ in range(4):
        b_ = (a_ + 1) % 4
        for i in range(m):
            j = (i + 1) % m
            T += [(a_ * m + i, b_ * m + i, b_ * m + j), (a_ * m + i, b_ * m + j, a_ * m + j)]
    return V, np.array(T)


def _caja(c, s):
    V = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * np.asarray(s) / 2 + c
    T = np.array([(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
                  (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)])
    return V, T


def _viga(a, b, t):
    """Prisma de sección cuadrada t × t entre a y b."""
    d = b - a; L = np.linalg.norm(d); u = d / max(L, 1e-9)
    w = np.cross(u, [0, 1.0, 0]); w = w / np.linalg.norm(w) if np.linalg.norm(w) > 1e-6 else np.array([1.0, 0, 0])
    v = np.cross(w, u)
    V = np.array([p + (sw * w + sv * v) * t / 2 for p in (a, b) for sw, sv in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    T = []
    for k in range(4):
        a0, a1, b0, b1 = k, (k + 1) % 4, 4 + k, 4 + (k + 1) % 4
        T += [(a0, b0, b1), (a0, b1, a1)]
    T += [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7)]
    T = np.array(T)
    c = V.mean(0)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, V[T].mean(1) - c) < 0
    T[malo] = T[malo][:, ::-1]
    return V, T


def gafas(E):
    """Pasta gruesa negra (brief gafas.md): dos aros + puente + bisagras + varillas, rígidas a Head."""
    import receta_adan_v39 as v39
    import receta_adan_v41 as v41
    import receta_adan_v49 as v49
    from copox.medicion import texturas_tela as tt
    g = GAFAS
    P = v49._prims(E)
    ojo = v39._leer(E, P["Ojo_C7V2_L"], "POSITION").astype(float)
    cab = v39._leer(E, P["Cabeza_PIEL_EXPUESTA_v04"], "POSITION").astype(float)
    cx, cy = (ojo[:, 0].min() + ojo[:, 0].max()) / 2, (ojo[:, 1].min() + ojo[:, 1].max()) / 2
    z = ojo[:, 2].max() + g["sobre"]
    piezas = []
    for sg in (1, -1):
        piezas.append(_marco(sg * cx, cy, z, g["ancho"], g["alto"], g["radio"], g["grueso"], g["fondo"]))
    xin = cx - g["ancho"] / 2
    piezas.append(_caja(np.array([0, cy + g["alto"] * 0.18, z]), (2 * xin + g["grueso"], g["puente"], g["fondo"])))
    yv = cy + g["alto"] * 0.25
    banda = cab[np.abs(cab[:, 1] - yv) < 0.01]
    xo = cx + g["ancho"] / 2
    for sg in (1, -1):
        # bisagra corta en la esquina del aro + varilla recta que va pegada al lado de la cabeza hasta la oreja
        lado = banda[(sg * banda[:, 0] > 0)]
        x_lado = np.abs(lado[:, 0]).max() + g["varilla"] / 2 + 0.001
        z_frente_lado = lado[np.abs(lado[:, 0]) > np.abs(lado[:, 0]).max() - 0.006][:, 2].max()
        piezas.append(_caja(np.array([sg * (xo + 0.004), yv, z]), (0.010, g["varilla"] * 1.5, g["fondo"])))
        piezas.append(_viga(np.array([sg * (xo + 0.006), yv, z - g["fondo"] / 2]),
                            np.array([sg * x_lado, yv, min(z_frente_lado, z - 0.01)]), g["varilla"]))
        oreja = cab[(sg * cab[:, 0] > np.abs(cab[:, 0]).max() - 0.004)]
        z_or = float(np.median(oreja[:, 2])) if len(oreja) else g["z_oreja"]
        y_or = float(oreja[:, 1].max()) if len(oreja) else yv - 0.004
        piezas.append(_viga(np.array([sg * x_lado, yv, min(z_frente_lado, z - 0.01)]),
                            np.array([sg * x_lado, min(yv, y_or + 0.004), z_or]), g["varilla"]))
    V, T, o = [], [], 0
    for v, t in piezas:
        V.append(v); T.append(t + o); o += len(v)
    V, T = np.vstack(V), np.vstack(T)
    c0 = V.mean(0)
    V, T, N = v49._facetado(V, T)
    sk = E.j["skins"][0]
    nombres = [E.j["nodes"][k]["name"] for k in sk["joints"]]
    J = np.zeros((len(V), 4), np.uint16); J[:, 0] = nombres.index("Head")
    W = np.zeros((len(V), 4), np.float32); W[:, 0] = 1
    mat = v41._material(E, "ALASTOR_GAFAS", COL["gafas"])
    E.j["materials"][mat]["doubleSided"] = False
    E.j["materials"][mat].setdefault("extras", {})["paleta"] = "negro_calido/5"
    v49._nodo(E, "ACC_GAFAS", [v41._prim_nueva(E, V, T, N, J, W, mat, "ALASTOR_GAFAS")])
    E.j["nodes"][-1]["extras"] = {"sin_sombra": True}      # Admin 20 oct: su sombra en la cara se leía como bigote
    return {"operacion": "gafas", "tris": int(len(T)), "z": round(float(z), 4),
            "centro": [round(float(x), 4) for x in c0]}


CARA = dict(morphs={"ceja_ceno_L": 0.85, "ceja_ceno_R": 0.85,          # v03: sin parpado_enojo (tapaba el iris)
                    "comisura_abajo_L": 0.60, "comisura_abajo_R": 0.60, "boca_tensa": 0.45, "boca_estrecha": 0.30},
            ceja_grosor=1.45, ceja_largo=1.12, rubor=False)


def cara(E):
    """Cara propia de Alastor (Admin: opción B; brief cara_alastor.md): hornea pesos de morph en la pose de reposo de la
    cabeza, engrosa los bloques de ceja y quita el rubor. Los morphs siguen encima (la animación facial no se pierde)."""
    import receta_adan_v24 as v24
    import receta_adan_v39 as v39
    from copox.medicion.gltf import accesor
    j = E.j
    malla = next(m for m in j["meshes"] if m.get("name") == "ADAN_CUERPO") if any(m.get("name") == "ADAN_CUERPO" for m in j["meshes"]) else j["meshes"][0]
    nombres_t = malla.get("extras", {}).get("targetNames", [])
    pesos = {nombres_t.index(k): w for k, w in CARA["morphs"].items() if k in nombres_t}
    log = {"operacion": "cara de Alastor", "morphs": {nombres_t[i]: w for i, w in pesos.items()}, "piezas": 0}
    for p in malla["primitives"]:
        if not p.get("targets"):
            continue
        V = v39._leer(E, p, "POSITION").astype(np.float64)
        dV = np.zeros_like(V)
        for i, w in pesos.items():
            t = p["targets"][i]
            if "POSITION" in t:
                dV += w * accesor(j, E.b, t["POSITION"]).astype(np.float64)
        mat = j["materials"][p["material"]]["name"]
        if mat == "CEJA_BLOQUE":                       # cejas más gruesas (alto) y un poco más largas
            Vn = V + dV
            c = Vn.mean(0)
            Vn = c + (Vn - c) * np.array([CARA["ceja_largo"], CARA["ceja_grosor"], 1.0])
            dV = Vn - V
        if not np.abs(dV).max() > 0:
            continue
        acc = j["accessors"][p["attributes"]["POSITION"]]
        Vn = (V + dV).astype(np.float32)
        p["attributes"]["POSITION"] = E._add(Vn, "VEC3", 34962, True)
        log["piezas"] += 1
        if not CARA["rubor"] and "COLOR_0" in p["attributes"] and p.get("extras", {}).get("pieza") == "Cabeza_PIEL_EXPUESTA_v04":
            C = v39._leer(E, p, "COLOR_0").astype(np.float32)
            C[:, :3] = 1.0
            p["attributes"]["COLOR_0"] = v24._add_raw(E, np.ascontiguousarray(C), 5126, "VEC4", 34962)
            log["rubor"] = "fuera"
    E.b = bytes(E.out)
    return log


def main(src, dst):
    """Alastor completo sobre la base congelada. Los parámetros los pone la ficha (copox.avatar)."""
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    import vestir_theo_capas as v2
    import vestir_theo_v3 as v3
    carpeta = os.path.dirname(os.path.abspath(dst))
    E = re.Editor(src)
    log = [cara(E), pelo_masas(E, carpeta)]
    v3.CHA["usar"] = False
    try:
        log.append(v3.vestir(E, carpeta))
        log.append(abrigo(E, carpeta))
        log.append(gafas(E))
        log += [v2.ocultar_piel(E), v3.ocultar_tobillo(E), v2.elegir(E)]
    finally:
        v3.CHA.pop("usar", None)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Alastor Kleinteil desde los originales (pelo, camisa, corbata, pantalón, abrigo, cinturón, gafas). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return log


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "--solo-pelo":
        print(solo_pelo(sys.argv[1], sys.argv[2]))
    else:
        for x in main(sys.argv[1], sys.argv[2]):
            print(x)
