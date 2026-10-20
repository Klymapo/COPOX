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
    (-30, 66, 70, 60, 120, 32, 0.0), (-10, 74, 110, 52, 120, 32, 0.0), (-50, 66, 40, 76, 100, 30, 0.0),
    (0, 76, 150, 70, 120, 32, 0.0),
    (-14, 82, -34, 40, 72, 36, 0.030, -35),                       # el rizo en «C» sobre la frente (despegado)
    (70, 60, 96, 14, 90, 30, 0.010), (-70, 60, -92, 12, 60, 20, 0.004),
    (110, 52, 118, -8, 70, 22, 0.004), (-110, 52, -118, -8, 70, 22, 0.004),
    (-140, 64, -146, -34, 110, 26, 0.008), (140, 64, 146, -34, 110, 26, 0.008), (180, 68, 180, -38, 116, 26, 0.008),
]
PELO = dict(color="#69472D", escala=1.75, afilar=0.15, punta=0.60,           # marron_calido/4
            volumen=dict(corona=0.034, lados=0.004, el0=10.0, el1=70.0))


def pelo(E, carpeta):
    import pelo_personaje as pp
    return pp.pelo(E, V47, carpeta, None, MECHONES, PELO["color"], nodo="CAPA_PELO_ALASTOR", pieza="PELO_ALASTOR",
                   prefijo="PeloA", escala=PELO["escala"], afilar=PELO["afilar"], punta=PELO["punta"],
                   volumen=PELO["volumen"])


RIZO = dict(centro=(-0.048, 0.712), radio=0.042, z=0.150, ang=(40.0, 290.0), ancho=(0.032, 0.012), grueso=0.024, n=14)


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
    C = np.c_[r["centro"][0] + rad * np.cos(th), r["centro"][1] + rad * np.sin(th), r["z"] + np.linspace(0.006, -0.002, r["n"])]
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


def solo_pelo(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [pelo(E, os.path.dirname(os.path.abspath(dst))), rizo(E)]
    for n in E.j["nodes"]:
        if n.get("name") == "CAPA_PELO_THEO":
            n.setdefault("extensions", {})["KHR_node_visibility"] = {"visible": False}
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Prueba: pelo de Alastor sobre la base congelada. SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return log


# ── ropa: camisa + corbata + pantalón (traje_chaleco sin chaleco) + abrigo + cinturón + gafas ──────────────────────
COL = {"camisa": "#FBEFE1", "corbata": "#232026", "pantalon": "#2C2320", "boton": "#2C2320",     # camisa_blanca,
       "abrigo": "#3A2F2A", "solapa": "#2C2320", "cinturon": "#5F4338", "hebilla": "#9A7B3C",   # uniforme_policia,
       "gafas": "#1F1916"}                                                                       # negro_calido 3/4/5…
TELA = {"abrigo": "lana_cerrada", "solapa": "lana_cerrada", "cinturon": "cuero", "hebilla": "cuero", "gafas": "cuero"}
ABRIGO = dict(capa=0.0070, y_bajo=0.118, cintura=0.300, vuelo=0.030, k=0.012, manga=0.256, cuello=0.0075,
              abertura=((0.10, 0.062), (0.22, 0.046), (0.30, 0.040), (0.40, 0.030), (0.47, 0.040)),
              solapa_ancho=0.032, solapa_y=(0.474, 0.355), tris=8000)
CINTURON = dict(y=0.274, alto=0.013, sobre=0.0030, hebilla=(0.018, 0.013, 0.0035))
GAFAS = dict(ancho=0.106, alto=0.086, grueso=0.0125, fondo=0.010, radio=0.015, sobre=0.011, puente=0.012,
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
        cue = np.maximum.reduce([U["t_cuello"].sdf(P) - a["cuello"], np.abs(y - 0.488) - 0.020,
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
        v, t = rc.placa(L, R, 0.0022, lambda q: np.array([0, 0.2, 1.0]) / np.hypot(0.2, 1.0))
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
    Vh, Th = rc.caja_redondeada(np.array([0.0, c["y"], zc + c["hebilla"][2] * 0.6]), np.eye(3), np.array(c["hebilla"]) / 2 * np.array([1, 1, 1]))
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
        piezas.append(_viga(np.array([sg * x_lado, yv, min(z_frente_lado, z - 0.01)]),
                            np.array([sg * x_lado, yv - 0.004, g["z_oreja"]]), g["varilla"]))
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
    return {"operacion": "gafas", "tris": int(len(T)), "z": round(float(z), 4),
            "centro": [round(float(x), 4) for x in c0]}


def main(src, dst):
    """Alastor completo sobre la base congelada. Los parámetros los pone la ficha (copox.avatar)."""
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    import vestir_theo_capas as v2
    import vestir_theo_v3 as v3
    carpeta = os.path.dirname(os.path.abspath(dst))
    E = re.Editor(src)
    log = [pelo(E, carpeta), rizo(E)]
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
