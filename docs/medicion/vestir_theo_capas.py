"""Theo vestido por capas (v2) sobre Adán V50. Admin (19 oct 2026): ropa por capas, cada pieza, holgura leve, textura
por tela, respetar el límite del pantalón con el zapato. Brief: docs/investigacion/ropa_capas.md.

Capas (de adentro hacia afuera): piel → camisa (tafetán blanco; cuello, puños arremangados) → corbata (satén azul;
nudo + hoja) → chaleco (lana cerrada negra; escote en V, puntas abajo, 4 botones) ; pantalón (sarga azul; pretina,
vuelta) ; zapatos (pieza de V50). Cada prenda en su nodo, encendida/apagada por separado (KHR_node_visibility).
Uso: GODOT_BIN=… [ALTH_CALIDAD=borrador] python vestir_theo_capas.py ADAN_V50.glb THEO_VESTIDO_V2.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v49 as v49  # noqa: E402

COL = {"camisa": "#FBEFE1", "chaleco": "#302E2D", "corbata": "#41598D", "pantalon": "#4A5770", "boton": "#2C2320"}
TELA = {"camisa": "tafetan_suave", "chaleco": "lana_cerrada", "corbata": "saten", "pantalon": "sarga", "boton": "cuero"}
CAMISA = dict(holgura=0.0035, cierre=0.006, borde=0.215, cuello_y=(0.474, 0.497), cuello_extra=0.0025, manga=0.272,
              puno=0.016, puno_extra=0.003)
CHALECO = dict(holgura=0.0042, borde_lado=0.246, borde_punta=0.226, hombro_x=0.110, cuello=0.476, v_fondo=0.372,
               v_ancho=0.040, botones=(0.357, 0.322, 0.287, 0.252))
CORBATA = dict(nudo_y=0.465, punta_y=0.318, ancho_nudo=0.009, ancho=0.019, sobre=0.0012, grosor=0.0016)
PANT = dict(holgura=0.0035, holgura_bajo=0.0045, cierre=0.012, recto_desde=0.150, cintura=0.278, pretina=0.014, dobladillo=0.070,
            vuelta=0.016, vuelta_extra=0.003)
FRENTE_Z = 0.030
TRIS = dict(camisa=10000, chaleco=7000, pantalon=10000)
VISIBLE = {"CAPA_SHORT": False, "PIES_DESCALZOS": False, "PIES_TENIS": False, "PIES_ZAPATO": True,
           "CAPA_GUIA_CAPILAR": False, "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": False, "CAPA_PELO_THEO": True}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _region_camisa(P):
    c = CAMISA
    x, y = np.abs(P[:, 0]), P[:, 1]
    return np.maximum.reduce([c["borde"] - y, y - c["cuello_y"][0], x - c["manga"]])


def _region_chaleco(P):
    c = CHALECO
    x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
    frente = _ss((z - FRENTE_Z) / 0.02)
    # orilla de abajo: puntas al frente (más bajas junto al centro), recta atrás
    borde = c["borde_lado"] - (c["borde_lado"] - c["borde_punta"]) * frente * _ss(1 - np.abs(x - 0.018) / 0.05)
    t = np.clip((y - c["v_fondo"]) / (c["cuello"] - c["v_fondo"]), 0, 1)
    v_abierta = np.where((z > FRENTE_Z) & (y > c["v_fondo"]), c["v_ancho"] * t - x, -1.0)
    cuello = 0.042 - np.hypot(x, (z - 0.01) * 0.8)                    # hueco del cuello (también atrás)
    # sisa curva alrededor de la raíz del brazo (Admin: "los hombros se ven blancos"): arriba el chaleco cubre el
    # hombro hasta donde empieza la manga; la abertura es una elipse en (y, z) para |x| > 0.098
    # Admin (19 oct, 2.ª): "sigo viendo los hombros blancos" → el tirante llega a la ESQUINA del hombro (x de la
    # articulación del brazo, medida en el rig: sisa_x) y la sisa sólo se abre ABAJO, en la axila (elipse bajo el brazo)
    sx = c.get("sisa_x", 0.136)
    ay, az = c.get("axila", (0.400, 0.014))
    axila = 1 - np.hypot((y - ay) / 0.030, (z - az) / 0.046)
    sisa = np.maximum(np.where(x > sx - 0.020, axila * 0.03, -1.0), x - sx)
    return np.maximum.reduce([borde - y, y - c.get("tope", c["cuello"]), sisa, v_abierta,
                              np.where(y > 0.455, cuello, -1.0)])


def _region_pantalon(P):
    c = PANT
    return np.maximum(c["dobladillo"] - P[:, 1], P[:, 1] - c["cintura"])


def _prim(E, V, T, N, piezas, nombres, mat, pieza, escala_uv):
    """N=None → normales por cara (piezas explícitas delgadas: botones, nudo, hoja, puntas del cuello)."""
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import texturas_tela as tt
    import receta_adan_v41 as v41
    J4, W4 = ra.pesos_por_piel_visible(V, piezas, len(nombres))
    V2, T2 = V[T].reshape(-1, 3), np.arange(len(T) * 3).reshape(-1, 3)
    if N is None:
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        N2 = np.repeat(fn, 3, axis=0)
    else:
        N2 = N[T].reshape(-1, 3)
    J2, W2 = J4[T].reshape(-1, 4), W4[T].reshape(-1, 4)
    UV = tt.uv_caja(V2, T2, escala_uv)
    p = v41._prim_nueva(E, V2, T2, N2, J2, W2, mat, pieza)
    p["attributes"]["TEXCOORD_0"] = E._add(UV.astype(np.float32), "VEC2", 34962)
    return p


def _simplificar(V, T, n, carpeta):
    import receta_adan_v36 as v36
    return v36.simplificar(V, T, n, carpeta) if len(T) > n else (V, T)


def vestir(E, carpeta):
    from copox.medicion import ropa_capas as rc
    from copox.medicion import texturas_tela as tt
    nombres, _ = v40.v38_skin(E)
    pz = {n: v49._pieza(E, n) for n in ("Torso_PIEL", "Cuello", "BrazoL", "BrazoR", "Pelvis_PIEL", "PiernaL_PIEL",
                                         "PiernaR_PIEL")}
    mats = {k: tt.material_textura(E, f"THEO_{k.upper()}", COL[k], TELA[k]) for k in COL}
    log, nodos = {"operacion": "Theo por capas"}, {}

    # ── camisa ─────────────────────────────────────────────────────────────────────────────────────────────────────
    c = CAMISA
    R = rc.Rejilla((-0.40, 0.20, -0.10), (0.40, 0.52, 0.15), 0.0016)   # brazos completos: el relleno del sólido necesita la mano cerrada
    torso_brazos = [pz["Torso_PIEL"], pz["Cuello"], pz["BrazoL"], pz["BrazoR"], pz["Pelvis_PIEL"]]
    occ = R.ocupacion(torso_brazos)
    occ = R.cerrar(occ, c["cierre"])
    sd = R.distancia(occ)
    reg = R.campo(_region_camisa)
    x, y = np.abs(R.P[:, 0]).reshape(R.n), R.P[:, 1].reshape(R.n)
    hol_c = c["holgura"] + 0.0018 * _ss((x - 0.13) / 0.03)          # la manga un poco más suelta (codo al caminar)
    F = np.maximum(sd - hol_c, reg)
    puno = np.maximum.reduce([sd - hol_c - c["puno_extra"], x - c["manga"], c["manga"] - c["puno"] - x])
    cuello = np.maximum.reduce([sd - c["holgura"] - c["cuello_extra"], y - c["cuello_y"][1], c["cuello_y"][0] - 0.004 - y,
                                x - 0.07])
    F = np.minimum.reduce([F, puno, cuello])
    occ_camisa = (F < 0) | occ
    V, T = R.malla(F)
    V, T = _simplificar(V, T, TRIS["camisa"], carpeta)
    N = rc.normales_campo(R, F, V); T = rc.orientar(V, T, N)
    nodos["CAPA_CAMISA"] = [_prim(E, V, T, N, torso_brazos[:4], nombres, mats["camisa"], "THEO_CAMISA",
                                  tt.ESCALAS["tafetan"])]
    log["camisa"] = int(len(T))
    sd_cam = R.distancia(occ_camisa)

    # ── pantalón ───────────────────────────────────────────────────────────────────────────────────────────────────
    p = PANT
    Rp = rc.Rejilla((-0.17, 0.05, -0.10), (0.17, 0.30, 0.15), 0.0016)
    piernas = [pz["Pelvis_PIEL"], pz["PiernaL_PIEL"], pz["PiernaR_PIEL"], pz["Torso_PIEL"]]
    occ_p = Rp.ocupacion(piernas)
    # la camisa va metida en el pantalón: su sólido (debajo de la cintura) cuenta como cuerpo
    dentro = ((Rp.P >= R.lo) & (Rp.P <= R.lo + R.paso * (R.n - 1))).all(1)
    f_cam = np.ones(len(Rp.P), np.float32); f_cam[dentro] = R.muestrear(F, Rp.P[dentro])
    occ_p |= (f_cam < 0).reshape(Rp.n)
    # caída recta: debajo de la rodilla cada pierna del pantalón es la columna del corte del muslo
    j0 = int(round((p["recto_desde"] - Rp.lo[1]) / Rp.paso))
    for j in range(0, j0):
        occ_p[:, j, :] |= occ_p[:, j0, :]
    occ_p = Rp.cerrar(occ_p, p["cierre"])
    sdp = Rp.distancia(occ_p)
    yp = Rp.P[:, 1].reshape(Rp.n)
    hol = p["holgura"] + (p["holgura_bajo"] - p["holgura"]) * _ss((0.17 - yp) / 0.10)   # cae recto abajo
    # límite con el zapato (Admin: "respeta el límite del pantalón y zapatos"): la tela termina SOBRE el zapato, nunca
    # dentro; donde el zapato sube, el dobladillo sube con él
    import pie_calzado as pc
    zap = []
    for pzn, pie_n in (("PiernaL_PIEL", "PieL_PIEL"), ("PiernaR_PIEL", "PieR_PIEL")):
        Pp = v49._pieza(E, pzn)
        Vp = Pp.V0[Pp.V0[:, 1] < pc.PRESETS["ZAPATO"]["collar"]]
        if pie_n in v49._prims(E):
            Vp = np.vstack([Vp, v49._pieza(E, pie_n).V0])
        zap.append(pc.Calzado(Vp, pc.PRESETS["ZAPATO"]))
    f_zap = Rp.campo(lambda Q: np.minimum(zap[0].sdf(Q), zap[1].sdf(Q)))
    Fp = np.maximum.reduce([sdp - hol, Rp.campo(_region_pantalon), -(f_zap - 0.0018)])
    pretina = np.maximum.reduce([sdp - hol - 0.002, yp - p["cintura"], p["cintura"] - p["pretina"] - yp])
    vuelta = np.maximum.reduce([sdp - hol - p["vuelta_extra"], p["dobladillo"] - yp, yp - p["dobladillo"] - p["vuelta"]])
    Fp = np.minimum.reduce([Fp, pretina, np.maximum(vuelta, -(f_zap - 0.0018))])
    V, T = Rp.malla(Fp)
    V, T = _simplificar(V, T, TRIS["pantalon"], carpeta)
    N = rc.normales_campo(Rp, Fp, V); T = rc.orientar(V, T, N)
    nodos["CAPA_PANTALON"] = [_prim(E, V, T, N, piernas[:3], nombres, mats["pantalon"], "THEO_PANTALON",
                                    tt.ESCALAS["sarga"])]
    log["pantalon"] = int(len(T))
    # el chaleco va sobre la camisa Y sobre la pretina del pantalón
    dentro = ((R.P >= Rp.lo) & (R.P <= Rp.lo + Rp.paso * (Rp.n - 1))).all(1)
    f_pan = np.ones(len(R.P), np.float32); f_pan[dentro] = Rp.muestrear(Fp, R.P[dentro])
    occ_camisa = occ_camisa | (f_pan < 0).reshape(R.n)
    sd_cam = R.distancia(occ_camisa)
    # ── chaleco (sobre la camisa) ──────────────────────────────────────────────────────────────────────────────────
    ch = CHALECO
    Fv = np.maximum(sd_cam - ch["holgura"], R.campo(_region_chaleco))
    V, T = R.malla(Fv)
    V, T = _simplificar(V, T, TRIS["chaleco"], carpeta)
    N = rc.normales_campo(R, Fv, V); T = rc.orientar(V, T, N)
    prims_ch = [_prim(E, V, T, N, torso_brazos[:2], nombres, mats["chaleco"], "THEO_CHALECO", tt.ESCALAS["lana_cerrada"])]
    log["chaleco"] = int(len(T))
    # botones: en la superficie del chaleco, al centro
    occ_v = (Fv < 0) | occ_camisa
    sd_v = R.distancia(occ_v)
    Vb, Tb, o = [], [], 0
    for yb in ch["botones"]:
        zs = np.linspace(0.16, 0.0, 400)
        q = np.c_[np.zeros_like(zs), np.full_like(zs, yb), zs]
        z0 = zs[np.argmax(R.muestrear(sd_v, q) < 0)]
        v, t = rc.disco(np.array([0.0, yb, z0 - 0.0004]), np.array([0, 0, 1.0]), 0.0042, 0.0016)
        Vb.append(v); Tb.append(t + o); o += len(v)
    Vb, Tb = np.vstack(Vb), np.vstack(Tb)
    from copox.medicion import mano_geo as mg
    prims_ch.append(_prim(E, Vb, Tb, None, torso_brazos[:1], nombres, mats["boton"], "THEO_BOTONES",
                          tt.ESCALAS["cuero"]))
    nodos["CAPA_CHALECO"] = prims_ch

    # ── corbata (entre camisa y chaleco): nudo + hoja ──────────────────────────────────────────────────────────────
    k = CORBATA

    def z_camisa(yv, xv=0.0):
        zs = np.linspace(0.16, 0.0, 600)
        q = np.c_[np.full_like(zs, xv), np.full_like(zs, yv), zs]
        return zs[np.argmax(R.muestrear(sd_cam, q) < 0)]
    ys = np.linspace(k["nudo_y"] - 0.010, k["punta_y"], 16)
    zc = np.array([z_camisa(v) for v in ys]) + k["sobre"]
    zc = np.maximum.accumulate(zc) * (ys > ch["v_fondo"]) + zc * (ys <= ch["v_fondo"])   # cuelga solo en la V
    t = (k["nudo_y"] - ys) / (k["nudo_y"] - k["punta_y"])
    w = k["ancho_nudo"] + (k["ancho"] - k["ancho_nudo"]) * _ss(t / 0.4)
    w = np.where(t > 0.92, w * (1 - (t - 0.92) / 0.08 * 0.98), w)                          # punta en pico
    izq = np.c_[-w, ys, zc]; der = np.c_[w, ys, zc]
    Vh, Th = rc.placa(izq, der, k["grosor"], lambda p: np.array([0, 0, 1.0]))
    zn = z_camisa(k["nudo_y"]) + 0.0045
    Vn, Tn = rc.caja_redondeada(np.array([0, k["nudo_y"], zn]), np.eye(3), np.array([0.0105, 0.0085, 0.0055]))
    Vt = np.vstack([Vh, Vn]); Tt = np.vstack([Th, Tn + len(Vh)])
    # puntas del cuello de la camisa: sobre el chaleco, a cada lado del nudo
    def z_sobre(xv, yv):
        zs = np.linspace(0.16, 0.0, 600)
        q = np.c_[np.full_like(zs, xv), np.full_like(zs, yv), zs]
        return zs[np.argmax(R.muestrear(sd_v, q) < 0)] + 0.0009
    Vc, Tc, o = [], [], 0
    for sg in (1, -1):
        izq = [(sg * 0.011, 0.477), (sg * 0.019, 0.452)]
        der = [(sg * 0.042, 0.474), (sg * 0.026, 0.450)]
        L = np.array([[x_, y_, z_sobre(x_, y_)] for x_, y_ in izq])
        Rr = np.array([[x_, y_, z_sobre(x_, y_)] for x_, y_ in der])
        v, tq = rc.placa(L, Rr, 0.0012, lambda q: np.array([0, 0.25, 1.0]) / np.hypot(0.25, 1.0))
        if sg < 0:
            tq = tq[:, ::-1]
        Vc.append(v); Tc.append(tq + o); o += len(v)
    Vc, Tc = np.vstack(Vc), np.vstack(Tc)
    nodos["CAPA_CAMISA"].append(_prim(E, Vc, Tc, None, torso_brazos[:2], nombres, mats["camisa"],
                                      "THEO_CUELLO_PUNTAS", tt.ESCALAS["tafetan"]))
    nodos["CAPA_CORBATA"] = [_prim(E, Vt, Tt, None, torso_brazos[:2], nombres, mats["corbata"],
                                   "THEO_CORBATA", tt.ESCALAS["saten"])]
    log["corbata"] = int(len(Tt))

    E._campos_ropa = [(R, F, _region_camisa), (Rp, Fp, _region_pantalon)]
    for nombre, prims in nodos.items():
        v49._nodo(E, nombre, prims)
    v49._limpiar(carpeta)
    return log


def ocultar_piel(E, margen=0.008):
    """Solo en este derivado: fuera la piel que queda DENTRO del sólido de una prenda (paridad de rayo contra la malla
    cerrada de la camisa y del pantalón), lejos de puños, cuello y dobladillo (`margen`)."""
    import receta_adan_v24 as v24
    import receta_adan_v39 as v39
    from copox.medicion.gltf import accesor
    from copox.render.auditoria import _dentro_por_paridad
    prendas = []
    for m in E.j["meshes"]:
        for p in m["primitives"]:
            pz = p.get("extras", {}).get("pieza")
            if pz in ("THEO_CAMISA", "THEO_PANTALON"):
                prendas.append((v39._leer(E, p, "POSITION").astype(float),
                                accesor(E.j, E.b, p["indices"]).reshape(-1, 3),
                                _region_camisa if pz == "THEO_CAMISA" else _region_pantalon))
    log = {"operacion": "piel bajo la ropa"}
    for n in ("Torso_PIEL", "BrazoL", "BrazoR", "PiernaL_PIEL", "PiernaR_PIEL", "Pelvis_PIEL"):
        q = v49._prims(E).get(n)
        if q is None:
            continue
        V = v39._leer(E, q, "POSITION").astype(float)
        T = accesor(E.j, E.b, q["indices"]).reshape(-1, 3)
        tapado = np.zeros(len(V), bool)
        for Vp, Tp, region in prendas:
            lo, hi = Vp.min(0), Vp.max(0)
            cand = ((V >= lo) & (V <= hi)).all(1) & (region(V) < -margen) & ~tapado
            if cand.any():
                idx = np.nonzero(cand)[0]
                tapado[idx[_dentro_por_paridad(V[idx], Vp, Tp)]] = True
        quedan = ~tapado[T].all(1)
        if not quedan.any():
            for m in E.j["meshes"]:
                if q in m["primitives"]:
                    m["primitives"].remove(q)
            log[n] = "toda"
            continue
        q["indices"] = v24._add_raw(E, np.ascontiguousarray(T[quedan].ravel(), np.uint32), 5125, "SCALAR", 34963)
        E.b = bytes(E.out)
        log[n] = int((~quedan).sum())
    return log


def elegir(E):
    usados = E.j.setdefault("extensionsUsed", [])
    if "KHR_node_visibility" not in usados:
        usados.append("KHR_node_visibility")
    for n in E.j["nodes"]:
        if n.get("name") in VISIBLE:
            ext = n.setdefault("extensions", {})
            if VISIBLE[n["name"]]:
                ext.pop("KHR_node_visibility", None)
                if not ext:
                    n.pop("extensions")
            else:
                ext["KHR_node_visibility"] = {"visible": False}
    return {"operacion": "piezas elegidas"}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [vestir(E, os.path.dirname(os.path.abspath(dst))), ocultar_piel(E), elegir(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Theo vestido por capas (v2) sobre Adán V50. Derivado de entrega; theo_alpha.glb no se toca.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
