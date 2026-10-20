"""Theo vestido v3 sobre Adán V50: la ropa con la técnica del short (Admin, 19 oct 2026: "El short queda muy bien";
"Podemos darle un repaso a la ropa?"). Cada prenda es un volumen limpio de secciones superelípticas ajustadas al cuerpo
medido y suavizadas (copox/medicion/ropa_tubos.py); capas = el mismo volumen con más holgura. Se conservan de v2: las
piezas explícitas (puntas del cuello, botones, nudo y hoja de la corbata), las texturas de tela, el límite con el
zapato y la piel oculta por paridad. Brief: docs/investigacion/ropa_capas.md.
Uso: GODOT_BIN=… [ALTH_CALIDAD=borrador] python vestir_theo_v3.py ADAN_V50.glb THEO_VESTIDO_V3.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v49 as v49  # noqa: E402
import vestir_theo_capas as v2  # noqa: E402

CAM = dict(borde=0.215, cuello=0.474, manga=0.272, puno=0.016, hol=0.0060, hol_manga=0.0065, codo=0.206,
           hol_codo=0.0040, k=0.012, cuello_banda=(0.470, 0.497), hol_cuello=0.0040)
CHA = dict(capa=0.0042, borde_lado=0.246, borde_punta=0.226, hombro_x=0.112, cuello=0.476, v_fondo=0.372,
           v_ancho=0.040, botones=(0.357, 0.322, 0.287, 0.252))
PAN = dict(cintura=0.280, pretina=0.014, hem=0.056, vuelta=0.016, hol_pelvis=0.0088, hol_pierna=0.0066,
           recto_desde=0.150, k=0.022)
TRIS = dict(camisa=7000, chaleco=5000, pantalon=7000)
CORB = dict(grosor=0.0030, arista=0.0012, separa=0.0025, nudo=(0.012, 0.0095, 0.0072))


def _pts(E, n, y0=-1, y1=9, x0=None, x1=None):
    V = v39._leer(E, v49._prims(E)[n], "POSITION").astype(float)
    s = (V[:, 1] > y0) & (V[:, 1] < y1)
    if x0 is not None:
        s &= (V[:, 0] > x0) & (V[:, 0] < x1)
    return V[s]


def _articulacion(E, nombre):
    """Posición en el mundo (pose de reposo) de un nodo del rig."""
    ns = E.j["nodes"]
    padre = {c: i for i, n in enumerate(ns) for c in n.get("children", [])}

    def mat(n):
        t = np.array(n.get("translation", [0, 0, 0]), float); x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        s = np.array(n.get("scale", [1, 1, 1]), float)
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m = np.eye(4); m[:3, :3] = R * s; m[:3, 3] = t
        return m
    i = next(k for k, n in enumerate(ns) if n.get("name") == nombre)
    m = mat(ns[i])
    while i in padre:
        i = padre[i]; m = mat(ns[i]) @ m
    return m[:3, 3]


def _malla(f, lo, hi, n_tris, carpeta, paso=0.0011):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import short_geo as sg
    V, T = sg.malla_sdf(f, lo, hi, paso=paso, pulido=3)
    V, T = ra.solo_mayor(V, T)
    if len(T) > n_tris:
        V, T = v36.simplificar(V, T, n_tris, carpeta)
    N = v49._normales_sdf(f, V)
    return V, v49._orientar(V, T, N), N


def vestir(E, carpeta):
    from copox.medicion import ropa_capas as rc
    from copox.medicion import ropa_tubos as rt
    from copox.medicion import texturas_tela as tt
    import pie_calzado as pc
    nombres, _ = v40.v38_skin(E)
    pz = {n: v49._pieza(E, n) for n in ("Torso_PIEL", "Cuello", "BrazoL", "BrazoR", "Pelvis_PIEL", "PiernaL_PIEL",
                                         "PiernaR_PIEL")}
    mats = {k: tt.material_textura(E, f"THEO_{k.upper()}", v2.COL[k], v2.TELA[k]) for k in v2.COL}
    log, nodos = {"operacion": "Theo v3 (volúmenes limpios)"}, {}
    c = CAM

    # ── camisa: torso + mangas + puños + cuello ────────────────────────────────────────────────────────────────────
    torso_v = np.vstack([_pts(E, "Torso_PIEL"), _pts(E, "Pelvis_PIEL", y0=0.20), _pts(E, "Cuello", y1=0.500)])
    torso_v = torso_v[np.abs(torso_v[:, 0]) < 0.125]
    t_cam = rt.Tubo(torso_v, 1, c["borde"] - 0.01, 0.500, c["hol"], n=32, suavizar=3)
    mangas = []
    for lado, n in ((1, "BrazoL"), (-1, "BrazoR")):
        bv = _pts(E, n)
        bv = bv[(lado * bv[:, 0] > 0.08) & (lado * bv[:, 0] < c["manga"] + 0.01)]
        hf = lambda ts: c["hol_manga"] + c["hol_codo"] * np.exp(-((ts - c["codo"]) / 0.040) ** 2)   # noqa: E731
        mangas.append(rt.Tubo(bv, 0, 0.09, c["manga"], 0, n=24, suavizar=2, lado=lado, holgura_fn=hf))
    cuerpo_cam = rt.union([t_cam.sdf, mangas[0].sdf, mangas[1].sdf], c["k"])

    if c.get("bajo_chaleco", 0.0):                 # la región del chaleco (sisa medida del rig) ya se necesita aquí
        _hx, _hy, _hz = _articulacion(E, "LeftUpperArm")
        v2.CHALECO.update(sisa_x=abs(_hx) - 0.005, axila=(_hy - 0.030, _hz), tope=0.506)

    def camisa(P):
        x, y = np.abs(P[:, 0]), P[:, 1]
        # arriba la camisa sube por los hombros hasta el cuello (no un corte horizontal que deja piel en el hombro)
        hueco = np.where(y > 0.455, 0.036 - np.hypot(x, (P[:, 2] - 0.012) * 0.85), -1.0)
        # metida: bajo la cintura la camisa se ciñe `meter` (más lejos del pantalón, que no se asome al moverse)
        metida = c.get("meter", 0.0) * v2._ss((PAN["cintura"] - 0.005 - y) / 0.012)
        # bajo el chaleco la camisa no se ve: se ciñe `bajo_chaleco` para que al mover el brazo no lo atraviese por la sisa
        bajo = 0.0
        if c.get("bajo_chaleco", 0.0) and "sisa_x" in v2.CHALECO:
            bajo = c["bajo_chaleco"] * v2._ss(-v2._region_chaleco(P) / 0.006)
        d = np.maximum.reduce([cuerpo_cam(P) + metida + bajo, c["borde"] - y, y - 0.490, hueco])   # bajo la banda del cuello
        d = np.maximum(d, x - c["manga"])
        for m in mangas:                                          # puño arremangado: banda más gruesa
            d = np.minimum(d, np.maximum.reduce([m.sdf(P) - 0.003, x - c["manga"], c["manga"] - c["puno"] - x]))
        return d
    cuello_v = _pts(E, "Cuello", y0=c["cuello_banda"][0] - 0.01, y1=c["cuello_banda"][1] + 0.01)
    t_cuello = rt.Tubo(cuello_v, 1, *c["cuello_banda"], c["hol_cuello"], n=8, suavizar=1)

    def camisa_total(P):
        return np.minimum(camisa(P), t_cuello.sdf(P))
    V, T, N = _malla(camisa_total, (-0.30, c["borde"] - 0.01, -0.09), (0.30, 0.505, 0.14), TRIS["camisa"], carpeta)
    # la parte metida en el pantalón se mueve con la PELVIS (como el pantalón): sin esto la camisa se asomaba por la
    # pretina al caminar o sentarse (capas_visibles, 19 oct)
    nodos["CAPA_CAMISA"] = [v2._prim(E, V, T, N, [pz["Torso_PIEL"], pz["Cuello"], pz["BrazoL"], pz["BrazoR"]]
                                     + ([pz["Pelvis_PIEL"]] if CAM.get("pelvis_pesos", True) else []), nombres,
                                     mats["camisa"], "THEO_CAMISA", tt.ESCALAS["tafetan_suave"])]
    log["camisa"] = int(len(T))

    # ── pantalón: pelvis + piernas rectas, pretina, vuelta; termina sobre el zapato ───────────────────────────────
    p = PAN
    pel_v = np.vstack([_pts(E, "Pelvis_PIEL"), _pts(E, "Torso_PIEL", y1=p["cintura"] + 0.01)])
    t_pel = rt.Tubo(pel_v, 1, 0.176, p["cintura"], p["hol_pelvis"], n=16, suavizar=2)   # baja hasta cubrir el glúteo
    piernas = []
    for lado, n in ((1, "PiernaL_PIEL"), (-1, "PiernaR_PIEL")):
        lv = _pts(E, n, y0=p["hem"] - 0.01, y1=0.215)
        lv = lv[lado * lv[:, 0] > 0]
        piernas.append(rt.Tubo(lv, 1, p["hem"], 0.215, p["hol_pierna"], n=24, suavizar=3, recto_desde=p["recto_desde"]))
    t_cam_in = t_cam.inflado(0.0035)                 # la camisa va metida: el pantalón la envuelve con su capa
    cuerpo_pan0 = rt.union([t_pel.sdf, piernas[0].sdf, piernas[1].sdf], p["k"])

    def cuerpo_pan(P):
        return np.minimum(cuerpo_pan0(P), t_cam_in.sdf(P))
    zap = []
    for pzn, pie_n in (("PiernaL_PIEL", "PieL_PIEL"), ("PiernaR_PIEL", "PieR_PIEL")):
        Vp = pz[pzn].V0[pz[pzn].V0[:, 1] < pc.PRESETS["ZAPATO"]["collar"]]
        if pie_n in v49._prims(E):
            Vp = np.vstack([Vp, v49._pieza(E, pie_n).V0])
        zap.append(pc.Calzado(Vp, pc.PRESETS["ZAPATO"]))

    def pantalon(P):
        y = P[:, 1]
        d = np.maximum(cuerpo_pan(P), np.maximum(p["hem"] - y, y - p["cintura"]))
        pre = np.maximum.reduce([cuerpo_pan(P) - 0.0018, y - p["cintura"], p["cintura"] - p["pretina"] - y])
        vue = np.maximum.reduce([np.minimum(piernas[0].sdf(P), piernas[1].sdf(P)) - 0.003, p["hem"] - y,
                                 y - p["hem"] - p["vuelta"]])
        d = np.minimum.reduce([d, pre, vue])
        fz = np.minimum(zap[0].sdf(P), zap[1].sdf(P))
        return np.maximum(d, -(fz - 0.0018))                      # nunca dentro del zapato
    V, T, N = _malla(pantalon, (-0.17, p["hem"] - 0.01, -0.09), (0.17, p["cintura"] + 0.01, 0.13), TRIS["pantalon"],
                     carpeta)
    nodos["CAPA_PANTALON"] = [v2._prim(E, V, T, N, [pz["Pelvis_PIEL"], pz["PiernaL_PIEL"], pz["PiernaR_PIEL"]], nombres,
                                       mats["pantalon"], "THEO_PANTALON", tt.ESCALAS["sarga"])]
    log["pantalon"] = int(len(T))

    # ── chaleco: el tubo de la camisa con una capa más, cortado; va sobre camisa y pretina ─────────────────────────
    ch = CHA
    t_cha = t_cam.inflado(ch["capa"])
    # esquina del hombro y axila medidas en el rig (sirve igual para Alastor): T-pose, brazo a lo largo de x
    hx, hy, hz = _articulacion(E, "LeftUpperArm")
    v2.CHALECO.update(sisa_x=abs(hx) - 0.005, axila=(hy - 0.030, hz), tope=0.506)                     # el tubo del torso termina en 0.500: el chaleco lo cubre entero
    log["hombro"] = dict(sisa_x=round(abs(hx), 4), axila_y=round(hy - 0.030, 4))

    def chaleco(P):
        # sobre TODA la camisa (también el abultado del hombro donde entra la manga); la sisa corta la manga
        base = np.minimum(cuerpo_cam(P) - ch["capa"], cuerpo_pan(P) - 0.0018 - ch["capa"])
        # hasta el cuello: sube sobre la camisa; sólo deja libre la banda del cuello de la camisa
        collar = np.where(P[:, 1] > 0.460, 0.0025 - t_cuello.sdf(P), -1.0)
        return np.maximum.reduce([base, v2._region_chaleco(P), collar])
    V, T, N = _malla(chaleco, (-0.16, 0.21, -0.09), (0.16, 0.512, 0.14), TRIS["chaleco"], carpeta)
    from copox.medicion import mano_geo as mg  # noqa: F401
    prims_ch = [v2._prim(E, V, T, N, [pz["Torso_PIEL"], pz["Cuello"]], nombres, mats["chaleco"], "THEO_CHALECO",
                         tt.ESCALAS["lana_cerrada"])]
    Vb, Tb, o = [], [], 0
    for yb in ch["botones"]:
        z0 = rt.superficie_z(chaleco, 0.0, yb)
        v, t = rc.disco(np.array([0.0, yb, z0 - 0.0004]), np.array([0, 0, 1.0]), 0.0042, 0.0016)
        Vb.append(v); Tb.append(t + o); o += len(v)
    Vb, Tb = np.vstack(Vb), np.vstack(Tb)
    prims_ch.append(v2._prim(E, Vb, Tb, None, [pz["Torso_PIEL"]], nombres, mats["boton"], "THEO_BOTONES",
                             tt.ESCALAS["cuero"]))
    nodos["CAPA_CHALECO"] = prims_ch
    log["chaleco"] = int(len(T))

    # ── puntas del cuello y corbata (entre camisa y chaleco) ───────────────────────────────────────────────────────
    def z_sobre(xv, yv):
        return max(rt.superficie_z(chaleco, xv, yv) or -1, rt.superficie_z(camisa_total, xv, yv) or -1) + 0.0009
    Vc, Tc, o = [], [], 0
    for sg in (1, -1):
        izq = [(sg * 0.011, 0.477), (sg * 0.019, 0.452)]
        der = [(sg * 0.042, 0.474), (sg * 0.026, 0.450)]
        L = np.array([[x_, y_, z_sobre(x_, y_)] for x_, y_ in izq])
        R = np.array([[x_, y_, z_sobre(x_, y_)] for x_, y_ in der])
        v, tq = rc.placa(L, R, 0.0012, lambda q: np.array([0, 0.25, 1.0]) / np.hypot(0.25, 1.0))
        Vc.append(v); Tc.append(tq + o); o += len(v)
    Vc, Tc = np.vstack(Vc), np.vstack(Tc)
    nodos["CAPA_CAMISA"].append(v2._prim(E, Vc, Tc, None, [pz["Torso_PIEL"], pz["Cuello"]], nombres, mats["camisa"],
                                         "THEO_CUELLO_PUNTAS", tt.ESCALAS["tafetan_suave"]))
    k = v2.CORBATA
    ys = np.linspace(k["nudo_y"] - 0.010, k["punta_y"], 16)
    zc = np.array([rt.superficie_z(camisa_total, 0.0, v) for v in ys]) + k["sobre"]
    zc = np.maximum.accumulate(zc) * (ys > ch["v_fondo"]) + zc * (ys <= ch["v_fondo"])
    t = (k["nudo_y"] - ys) / (k["nudo_y"] - k["punta_y"])
    w = k["ancho_nudo"] + (k["ancho"] - k["ancho_nudo"]) * v2._ss(t / 0.4)
    w = np.where(t > 0.92, w * (1 - (t - 0.92) / 0.08 * 0.98), w)
    # hoja con volumen (Admin: "la corbata se ve pintada"): sección hexagonal con arista al centro y bordes biselados,
    # separada del pecho (cuelga) — no una lámina pegada
    zc = zc + CORB["separa"] * v2._ss((ys[0] - ys) / 0.02)
    sec = np.array([[-1.0, 0.0], [-0.72, 0.85], [0.0, 1.0 + CORB["arista"] / CORB["grosor"]], [0.72, 0.85], [1.0, 0.0],
                    [0.0, -0.25]])
    anillos = [np.c_[sec[:, 0] * w[i], np.full(len(sec), ys[i]), zc[i] + sec[:, 1] * CORB["grosor"]] for i in range(len(ys))]
    Vh = np.vstack(anillos)
    nk = len(sec)
    Th = []
    for i in range(len(ys) - 1):
        a0, b0 = i * nk, (i + 1) * nk
        for e in range(nk):
            f = (e + 1) % nk
            Th += [(a0 + e, b0 + e, b0 + f), (a0 + e, b0 + f, a0 + f)]
    for e in range(1, nk - 1):
        Th += [(0, e, e + 1), (len(Vh) - nk, len(Vh) - nk + e + 1, len(Vh) - nk + e)]
    Th = np.array(Th)
    cen = np.c_[np.zeros(len(ys)), ys, zc + 0.3 * CORB["grosor"]]
    ref = np.repeat(cen, nk, axis=0)
    fn = np.cross(Vh[Th[:, 1]] - Vh[Th[:, 0]], Vh[Th[:, 2]] - Vh[Th[:, 0]])
    malo = np.einsum("ij,ij->i", fn, Vh[Th].mean(1) - ref[Th].mean(1)) < 0
    Th[malo] = Th[malo][:, ::-1]
    zn = rt.superficie_z(camisa_total, 0.0, k["nudo_y"]) + CORB["nudo"][2] * 0.75
    Vn, Tn = rc.caja_redondeada(np.array([0, k["nudo_y"], zn]), np.eye(3), np.array(CORB["nudo"]))
    Vt = np.vstack([Vh, Vn]); Tt = np.vstack([Th, Tn + len(Vh)])
    nodos["CAPA_CORBATA"] = [v2._prim(E, Vt, Tt, None, [pz["Torso_PIEL"], pz["Cuello"]], nombres, mats["corbata"],
                                      "THEO_CORBATA", tt.ESCALAS["saten"])]
    for nombre, prims in nodos.items():
        v49._nodo(E, nombre, prims)
    v49._limpiar(carpeta)
    return log


def ocultar_tobillo(E):
    """Revisor visual (19 oct): se veía piel en el talón, entre el dobladillo y el zapato. La pierna bajo el dobladillo
    queda siempre tapada por la vuelta y el zapato: fuera esos triángulos (sólo en el derivado vestido)."""
    import receta_adan_v24 as v24
    import receta_adan_v39 as v39
    from copox.medicion.gltf import accesor
    y_max = PAN["hem"] + PAN.get("tobillo_extra", 0.012)
    log = {"operacion": "tobillo bajo el dobladillo", "y_max": y_max}
    for n in ("PiernaL_PIEL", "PiernaR_PIEL"):
        q = v49._prims(E).get(n)
        if q is None:
            continue
        V = v39._leer(E, q, "POSITION").astype(float)
        T = accesor(E.j, E.b, q["indices"]).reshape(-1, 3)
        quedan = ~(V[T][:, :, 1] < y_max).all(1)
        q["indices"] = v24._add_raw(E, np.ascontiguousarray(T[quedan].ravel(), np.uint32), 5125, "SCALAR", 34963)
        E.b = bytes(E.out)
        log[n] = int((~quedan).sum())
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [vestir(E, os.path.dirname(os.path.abspath(dst))), v2.ocultar_piel(E), ocultar_tobillo(E), v2.elegir(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Theo vestido v3 (volúmenes limpios como el short) sobre Adán V50. theo_alpha.glb no se toca.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
