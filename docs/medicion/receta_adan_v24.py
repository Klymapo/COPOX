"""Adán V24 (sobre Adán V22 HABLA): todo lo de V23 + párpado fundido con la cara, ojo feliz y boca para hablar.

V24 sobre V23:
  - La piel del párpado toma normal y color (rubor) de la cara: sin contorno ni línea bajo el ojo.
  - ojo_feliz_X: ojo cerrado en arco hacia arriba (guiño/risa, como en las referencias); los guiños de
    G23_3 y G23_5 lo usan.
  - Boca: visemas A E I O U MBP FV redefinidos con aperturas grandes (forma D, O redonda, U en trompa,
    MBP labios apretados), boca_sonrisa_abierta y boca_dientes nuevas; dientes de arriba (fijos),
    dientes de abajo y lengua (siguen a la mandíbula en todos los morphs).

Lo que sigue es la descripción de V23:
Adán V23 (sobre Adán V22 HABLA): párpados de malla con línea de pestaña.

Hallazgo (pruebas de movimiento, 17 oct 2026): al cerrar, el párpado era una placa color piel sin línea de
pestaña, casi en el mismo plano que la placa del ojo (parche y ruido de pixeles en Godot).

Nuevo párpado, por ojo, en tres capas que copian la curvatura de la placa del ojo (por su UV) y flotan
delante de ella (piel superior +1.2 mm·u, piel inferior +1.0, pestaña +1.8):
  - PESTAÑA (material nuevo PESTANA_ALTH, del mismo color que la banda pintada): en reposo está plegada en el
    borde de arriba (se ve la banda de la textura); al cerrar baja y se vuelve un arco grueso (ojo cerrado chibi).
  - PIEL SUPERIOR: en reposo está plegada (área cero) en el borde de arriba; se despliega detrás de la pestaña.
  - PIEL INFERIOR: plegada en el borde de abajo; sube.
Morphs (L y R):
  parpado_X        (se redefine) cierre completo; el borde de abajo sube un poco a recibirlo.
  alegre_X         (se redefine) párpado inferior en arco (ojo feliz).
  parpado_inf_X    nuevo: párpado inferior recto (entrecerrar, sospecha).
  parpado_enojo_X  nuevo: párpado superior en diagonal, más bajo por dentro.
  parpado_triste_X nuevo: párpado superior en diagonal, más bajo por fuera.
Las piezas viejas (piel 34/35 y línea 36) se pliegan a un punto y la placa del ojo ya no se deforma.

Cachetes y boca (campos suaves en el marco de rostro, ED = 0.1348, v hacia abajo desde YC = 0.6252):
  cachete_inflar_X  inflar (soplar con un lado o ambos).
  cachete_subir_X   el cachete sube y se adelanta (sonrisa grande, guiño).
  comisura_arriba_X / comisura_abajo_X   cada esquina de la boca por separado.
  boca_ancha / boca_estrecha             ancho de la boca.
Uso: python receta_adan_v24.py ADAN_V22_HABLA.glb ADAN_V24.glb
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion import gestos  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402

PIEL, PESTANA = "PIEL_REFERENCIAS_THEO_ALASTOR_v04", "PESTANA_ALTH"
# color de la banda pintada en la textura del ojo (sRGB 34,21,15) pasado a lineal: la pestaña 3D no se distingue de ella
PESTANA_LINEAL = [0.0159, 0.0073, 0.0048, 1.0]
BANDA_RGB = np.array([0.133, 0.082, 0.059])
OFF_SUP, OFF_INF, OFF_PEST = 0.0012, 0.0010, 0.0018
NC, R_SUP, R_PEST, R_INF = 40, 8, 3, 7
NUEVOS = ["parpado_inf", "parpado_enojo", "parpado_triste", "ojo_feliz"]


# --- geometría de la placa del ojo (rejilla 33×33 en UV) ----------------------
class Placa:
    def __init__(self, E, p):
        j, b = E.j, E.b
        V = accesor(j, b, p["attributes"]["POSITION"]).astype(float)
        UV = accesor(j, b, p["attributes"]["TEXCOORD_0"]).astype(float)
        us, vs = np.unique(UV[:, 0].round(5)), np.unique(UV[:, 1].round(5))
        self.n = (len(vs), len(us))
        G = np.zeros((len(vs), len(us), 3))
        G[np.searchsorted(vs, UV[:, 1].round(5)), np.searchsorted(us, UV[:, 0].round(5))] = V
        self.G, self.us, self.vs = G, us, vs
        dv, du = np.gradient(G, vs, us, axis=(0, 1))
        N = np.cross(du, dv)
        N /= np.linalg.norm(N, axis=2, keepdims=True)
        if N[..., 2].mean() < 0:
            N = -N
        self.N = N
        mat = j["materials"][p["material"]]
        img = j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
        bv = j["bufferViews"][j["images"][img]["bufferView"]]
        import io
        from PIL import Image
        o = bv.get("byteOffset", 0)
        self.tex = np.asarray(Image.open(io.BytesIO(b[o:o + bv["byteLength"]])).convert("RGBA")).astype(float) / 255
        # lado de adentro (hacia la nariz) = u con |x| menor
        self.dentro_en_u0 = abs(G[len(vs) // 2, 0, 0]) < abs(G[len(vs) // 2, -1, 0])

    def _bil(self, A, u, v):
        u = np.clip(u, 0, 1) * (self.n[1] - 1); v = np.clip(v, 0, 1) * (self.n[0] - 1)
        i0 = np.clip(np.floor(v).astype(int), 0, self.n[0] - 2); k0 = np.clip(np.floor(u).astype(int), 0, self.n[1] - 2)
        fv, fu = (v - i0)[..., None], (u - k0)[..., None]
        return (A[i0, k0] * (1 - fv) * (1 - fu) + A[i0 + 1, k0] * fv * (1 - fu)
                + A[i0, k0 + 1] * (1 - fv) * fu + A[i0 + 1, k0 + 1] * fv * fu)

    def punto(self, u, v, off):
        N = self._bil(self.N, u, v)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        return self._bil(self.G, u, v) + off * N, N

    def contornos(self):
        T = self.tex; h, w = T.shape[:2]
        alfa = T[..., 3] > 0.5
        cols = np.where(alfa.any(0))[0]
        # se pasa unos pixeles de cada lado para que no queden rendijas en las esquinas al cerrar
        u = np.linspace(max(cols.min() - 8, 0) / (w - 1), min(cols.max() + 8, w - 1) / (w - 1), NC)
        vt, vb, vbot = [], [], []
        for uu in u:
            c = int(np.clip(round(uu * (w - 1)), cols.min() + 2, cols.max() - 2))
            filas = np.where(alfa[:, c])[0]
            t0, t1 = filas.min(), filas.max()
            banda = np.abs(T[:, c, :3] - BANDA_RGB).max(1) < 0.02
            r = t0
            while r < t1 and (banda[r] or r < t0 + 2):
                r += 1
            vt.append(t0 / (h - 1)); vb.append(r / (h - 1)); vbot.append(t1 / (h - 1))
        vt, vb, vbot = np.array(vt), np.array(vb), np.array(vbot)
        vb = np.maximum(vb, vt + 0.02)   # en las esquinas la banda casi desaparece
        # la piel se pasa un poco del borde para no dejar rendijas (sin salirse de la placa: v en 0.005–0.985)
        return u, np.clip(vt - 0.012, 0.0, 1), vb, np.clip(vbot + 0.012, 0, 1.0)


def _rejilla(nr, nc):
    F = []
    for r in range(nr - 1):
        for c in range(nc - 1):
            a, b = r * nc + c, r * nc + c + 1
            d, e = (r + 1) * nc + c, (r + 1) * nc + c + 1
            F += [[a, d, b], [b, d, e]]
    return np.array(F)


def capas(pl: Placa):
    """Devuelve {capa: (V_reposo, N, F, {morph: V_objetivo})} en coordenadas de la placa."""
    u, vt, vb, vbot = pl.contornos()
    alto = vbot - vt
    t_rep = vb - vt
    s = np.linspace(-1, 1, NC)                       # -1..1 de una esquina a otra
    adentro = (1 - s) / 2 if pl.dentro_en_u0 else (1 + s) / 2   # 1 = lado de la nariz

    # bordes (fracción desde arriba) del párpado superior para cada morph, y su grosor
    def sup(frac, grosor):
        return vt + frac * alto, grosor

    borde_rep = (vb, t_rep)
    sup_m = {
        "parpado": sup(0.66 * np.ones(NC), 0.80 * t_rep.max() * np.sqrt(np.clip(alto / alto.max(), 0, 1))),
        "parpado_enojo": sup(0.22 + 0.22 * adentro, t_rep),
        "parpado_triste": sup(0.44 - 0.22 * adentro, t_rep),
        # ojo cerrado feliz (guiño, risa): arco hacia arriba, como en las referencias ALTH
        "ojo_feliz": sup(0.66 - 0.16 * (1 - s ** 2), 0.80 * t_rep.max() * np.sqrt(np.clip(alto / alto.max(), 0, 1))),
    }
    inf_m = {
        "parpado": vt + 0.62 * alto,                 # sube a esconderse detrás de la pestaña
        "alegre": vt + (0.62 - 0.24 * (1 - s ** 2)) * alto,
        "parpado_inf": vt + 0.60 * alto,
        "ojo_feliz": vt + (0.62 - 0.16 * (1 - s ** 2)) * alto,
    }
    out = {}

    def malla(Uv, Vv, off):
        P, N = pl.punto(Uv, Vv, off)
        return P.reshape(-1, 3), N.reshape(-1, 3)

    U = np.tile(u, (R_PEST, 1))
    # pestaña: filas de (borde - grosor) a borde
    fr = np.linspace(0, 1, R_PEST)[:, None]

    def pest(borde, grosor):
        return (borde - grosor)[None, :] + fr * grosor[None, :]
    # en reposo la pestaña 3D queda plegada en el borde de arriba (grosor ~0): se ve la banda pintada de la textura
    Vrep = vt[None, :] + 0.003 * fr
    P0, N0 = malla(U, Vrep, OFF_PEST)
    out["pestana"] = (P0, N0, _rejilla(R_PEST, NC),
                      {m: malla(U, pest(b, g), OFF_PEST)[0] for m, (b, g) in sup_m.items()})
    # piel superior: de vt a (borde - grosor + traslape)
    U = np.tile(u, (R_SUP, 1)); fr2 = np.r_[0.0, np.linspace(0, 1, R_SUP - 1)][:, None]   # fila 0 = falda que baja a la piel

    def piel_sup(borde, grosor):
        fondo = np.maximum(borde - grosor + 0.35 * grosor, vt)
        return vt[None, :] + fr2 * (fondo - vt)[None, :]
    # en reposo la piel queda plegada en el borde (filas separadas 0.003 en v: sin vértices encimados)
    P0, N0 = malla(U, vt[None, :] + 0.003 * fr2, OFF_SUP)
    out["piel_sup"] = (P0, N0, _rejilla(R_SUP, NC),
                       {m: malla(U, piel_sup(b, g), OFF_SUP)[0] for m, (b, g) in sup_m.items()})
    # piel inferior: de vbot hacia arriba
    U = np.tile(u, (R_INF, 1)); fr3 = np.r_[0.0, np.linspace(0, 1, R_INF - 1)][:, None]   # fila 0 = falda que baja a la piel
    P0, N0 = malla(U, vbot[None, :] - 0.003 * fr3, OFF_INF)
    out["piel_inf"] = (P0, N0, _rejilla(R_INF, NC)[:, ::-1],   # filas hacia arriba: se invierte para mirar al frente
                       {m: malla(U, vbot[None, :] + fr3 * (tope - vbot)[None, :], OFF_INF)[0] for m, tope in inf_m.items()})
    return out


# --- cachetes y boca ----------------------------------------------------------
ED, YC = 0.1348, 0.6252
S = re._suave
V_BOCA, U_COMISURA = 0.53, 0.28


def _uv(V):
    return V[:, 0] / ED, (YC - V[:, 1]) / ED


def _frente(V):
    return S((V[:, 2] - 0.06) / 0.03)


def campo_cachete(signo, modo, k=1.0):
    def f(V):
        u, v = _uv(V)
        d = np.sqrt(((u - signo * 0.62) / 0.42) ** 2 + ((v - 0.32) / 0.34) ** 2)
        w = S(1 - d) * _frente(V) * k * S((v - 0.21) / 0.10)   # no sube hasta el ojo
        D = np.zeros_like(V)
        if modo == "inflar":
            r = np.stack([V[:, 0], np.zeros(len(V)), V[:, 2]], 1)
            r /= np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-9)
            D = 0.075 * ED * w[:, None] * r
        else:   # subir
            D[:, 1] = 0.07 * ED * w
            D[:, 2] = 0.03 * ED * w
            D[:, 0] = 0.02 * ED * w * signo
        return D
    return f


def campo_comisura(signo, dy):
    def f(V):
        u, v = _uv(V)
        d = np.sqrt(((u - signo * U_COMISURA) / 0.30) ** 2 + ((v - V_BOCA) / 0.20) ** 2)
        w = S(1 - d) * _frente(V)
        D = np.zeros_like(V)
        D[:, 1] = dy * ED * w
        D[:, 0] = 0.02 * ED * w * signo * (1 if dy > 0 else -0.5)
        D[:, 2] = -0.015 * ED * w
        return D
    return f


def campo_ancho(k):
    def f(V):
        u, v = _uv(V)
        w = S(1 - np.sqrt((u / 0.62) ** 2 + ((v - V_BOCA) / 0.20) ** 2)) * _frente(V)
        D = np.zeros_like(V)
        D[:, 0] = (k - 1) * V[:, 0] * w
        return D
    return f


def _solo_cara(p, V):
    """Solo la piel grande de la cabeza: los ojos, párpados y cejas no se deforman con los cachetes."""
    return len(V) > 5000


def cachetes_y_boca(E):
    for lado, sg in (("L", 1), ("R", -1)):   # L = +x, como los ojos del modelo
        gestos.agregar_morph(E, f"cachete_inflar_{lado}", {}, campo_cachete(sg, "inflar"), elegible=_solo_cara, suavizar=6)
        gestos.agregar_morph(E, f"cachete_subir_{lado}", {}, campo_cachete(sg, "subir"), elegible=_solo_cara, suavizar=6)
        gestos.agregar_morph(E, f"comisura_arriba_{lado}", {}, campo_comisura(sg, 0.075), suavizar=4)
        gestos.agregar_morph(E, f"comisura_abajo_{lado}", {}, campo_comisura(sg, -0.065), suavizar=4)
    gestos.agregar_morph(E, "boca_ancha", {}, campo_ancho(1.30), suavizar=4)
    gestos.agregar_morph(E, "boca_estrecha", {}, campo_ancho(0.78), suavizar=4)


# --- expresiones G: ahora también mueven boca, cachetes y párpados nuevos -------
# (valores al final del clip; los pares sin lado se aplican a L y R)
EXTRA_G = {
    "G23_1_Saludo": {"comisura_arriba": .7, "cachete_subir": .4},
    "G23_2_EscuchaActiva": {"comisura_arriba": .3},
    "G23_3_RespuestaAmable": {"comisura_arriba": .6, "cachete_subir": .3},
    "G23_4_SorpresaLeve": {"boca_estrecha": .4},
    "G23_5_RisaContenida": {"comisura_arriba": .9, "boca_ancha": .4, "cachete_subir": .7, "cachete_inflar": .3},
    "G24_1_Observador": {"parpado_inf": .4},
    "G24_2_Curioso": {"comisura_arriba_L": .4},
    "G24_3_Duda": {"comisura_abajo_R": .5, "comisura_arriba_L": .2},
    "G24_4_Confundido": {"comisura_abajo_L": .4, "boca_estrecha": .3},
    "G24_5_Sospecha": {"parpado_inf": .6, "comisura_abajo_L": .3, "comisura_arriba_R": .3},
    "G25_1_Frio": {"parpado_inf": .3, "boca_estrecha": .2},
    "G25_2_Desafiante": {"parpado_enojo": .5, "comisura_arriba_R": .5},
    "G25_3_Amenazante": {"parpado_enojo": .7, "comisura_abajo": .5, "boca_ancha": .2},
    "G25_4_Desprecio": {"comisura_arriba_L": .6, "comisura_abajo_R": .4, "parpado_inf": .3},
    "G25_5_Dominante": {"parpado_enojo": .3, "comisura_arriba": .25},
    "G26_1_Concentrado": {"parpado_enojo": .35, "boca_estrecha": .3},
    "G26_2_Realizacion": {"comisura_arriba": .4, "boca_ancha": .2},
    "G26_3_Incomodidad": {"comisura_abajo": .5, "boca_ancha": .3, "parpado_triste": .3},
    "G26_4_Fastidio": {"parpado_inf": .4, "comisura_abajo": .6},
    "G26_5_Determinacion": {"parpado_enojo": .4, "comisura_abajo": .2},
}
# V24: bocas abiertas y dientes en algunas expresiones; los guiños sonrientes usan el ojo feliz (arco)
EXTRA_G_V24 = {
    "G23_1_Saludo": {"boca_sonrisa_abierta": .45},
    "G23_4_SorpresaLeve": {"vis_O": .35},
    "G26_2_Realizacion": {"vis_O": .25, "boca_sonrisa_abierta": .2},
    "G25_3_Amenazante": {"boca_dientes": .6},
    "G26_4_Fastidio": {"boca_dientes": .3},
}
GUINO_FELIZ = ["G23_3_RespuestaAmable", "G23_5_RisaContenida"]


def expresiones(E):
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    ni = E.j["nodes"].index(nodo)
    for a in E.j["animations"]:
        extra = dict(EXTRA_G.get(a.get("name"), {}))
        extra.update(EXTRA_G_V24.get(a.get("name"), {}))
        if not extra:
            continue
        ch = next(c for c in a["channels"] if c["target"]["path"] == "weights" and c["target"]["node"] == ni)
        sm = a["samplers"][ch["sampler"]]
        t = accesor(E.j, E.b, sm["input"]).astype(float).reshape(-1)
        O = accesor(E.j, E.b, sm["output"]).astype(float).reshape(len(t), -1)
        rampa = (t - t.min()) / max(t.max() - t.min(), 1e-9)
        pesos = {nm: O[:, i] for i, nm in enumerate(nombres) if np.abs(O[:, i]).max() > 0}
        for k, val in extra.items():
            for nm in ([k] if k[-2:] in ("_L", "_R") or k.startswith(("boca_", "vis_")) else [k + "_L", k + "_R"]):
                pesos[nm] = np.clip(pesos.get(nm, 0) + val * rampa, 0, 1)
        if a["name"] in GUINO_FELIZ:
            for lado in "LR":
                k = f"parpado_{lado}"
                if k in pesos and pesos[k].max() > 0.8:      # el ojo cerrado del guiño pasa a ojo feliz
                    pesos[f"ojo_feliz_{lado}"] = pesos.pop(k)
                    pesos.pop(f"alegre_{lado}", None)
        gestos.pista_pesos(E, a["name"], t, pesos)


# --- boca reconstruida para hablar --------------------------------------------
# Rendija de la boca de Adán (medida en V22): ancho ±0.031, centro y = 0.5325 con curva de sonrisa
# y_rendija(x) = 0.5325 + 8.75·x²; labio de arriba en 0.5341, de abajo en 0.5306 (centro).
XW, Y0, KY = 0.031, 0.5325, 8.75
Z_LABIO, Z_DIENTES, HONDO = 0.147, 0.137, 2.5   # cavidad 2.5 veces más honda; dientes 10 mm·u detrás del labio
BOCA_INT = "BOCA_INTERIOR_NEGRO"
DIENTES, LENGUA = "DIENTES_ALTH", "LENGUA_ALTH"
DIENTES_LINEAL = [0.88, 0.86, 0.80, 1.0]     # marfil claro (sRGB ~ 242,239,231)
LENGUA_LINEAL = [0.55, 0.13, 0.12, 1.0]      # rosa-rojo (sRGB ~ 194,100,97)

# forma de cada boca (ED): arriba = labio de arriba; abajo = mandíbula (baja barbilla, dientes de abajo y
# lengua) + labio (solo el labio, descubre los dientes de abajo); perfil del labio de abajo (0 = plano,
# 0.5 = D); ancho (factor); comisuras (+ arriba); trompa (hacia el frente)
FORMAS = {
    "vis_A": dict(arriba=.05, mand=.22, labio=.08, perfil=.5, ancho=1.00, comisuras=.00, trompa=.00),
    "vis_E": dict(arriba=.04, mand=.08, labio=.07, perfil=.4, ancho=1.12, comisuras=.02, trompa=.00),
    "vis_I": dict(arriba=.035, mand=.03, labio=.05, perfil=.3, ancho=1.18, comisuras=.04, trompa=.00),
    "vis_O": dict(arriba=.07, mand=.14, labio=.08, perfil=.9, ancho=0.72, comisuras=.00, trompa=.05),
    "vis_U": dict(arriba=.03, mand=.04, labio=.05, perfil=.9, ancho=0.58, comisuras=.00, trompa=.08),
    "vis_MBP": dict(arriba=-.012, mand=.0, labio=-.016, perfil=0, ancho=1.00, comisuras=.00, trompa=.02),
    "vis_FV": dict(arriba=.05, mand=.0, labio=.015, perfil=.3, ancho=1.05, comisuras=.00, trompa=.00),
    "boca_sonrisa_abierta": dict(arriba=.05, mand=.12, labio=.08, perfil=.6, ancho=1.15, comisuras=.10, trompa=.00),
    "boca_dientes": dict(arriba=.045, mand=.0, labio=.05, perfil=0, ancho=1.12, comisuras=-.02, trompa=.00),
}
REDEFINIDOS = ["vis_A", "vis_E", "vis_I", "vis_O", "vis_U", "vis_MBP", "vis_FV"]


def y_rendija(x):
    return Y0 + KY * x ** 2


# caídas (ED) del campo de la boca; V25 las ensancha para que no queden surcos al abrir
CAIDA_SUP, CAIDA_LABIO, CAIDA_COMISURA = 0.12, 0.08, 0.15


def campo_boca(arriba, mand, labio, perfil, ancho, comisuras, trompa):
    def f(V):
        x, y = V[:, 0], V[:, 1]
        sx = x / XW
        sc = np.clip(sx, -1, 1)
        g_lat = np.where(np.abs(sx) <= 1, 1.0, np.exp(-((np.abs(sx) - 1) / 0.35) ** 2))
        g_mand = np.where(np.abs(sx) <= 1, 1.0, np.exp(-((np.abs(sx) - 1) / 1.2) ** 2))
        d = (y - y_rendija(x)) / ED                       # + arriba, - abajo (en ED)
        sup = d >= 0
        forma = np.clip(1 - sc ** 2, 0, 1) ** perfil if perfil > 0 else np.ones_like(sc)
        dy_sup = arriba * np.exp(-(d / CAIDA_SUP) ** 2) * g_lat
        dy_inf = -(mand * np.exp(-(d / 0.60) ** 2) * g_mand + labio * forma * np.exp(-(d / CAIDA_LABIO) ** 2) * g_lat)
        dy = np.where(sup, dy_sup, dy_inf) + comisuras * sc ** 2 * np.exp(-(d / CAIDA_COMISURA) ** 2) * g_lat
        # ancho: escala en x cerca de la rendija; más allá de las comisuras se desvanece
        xs = np.where(np.abs(sx) <= 1, x, np.sign(x) * XW * np.exp(-((np.abs(sx) - 1) / 0.5) ** 2))
        dx = (ancho - 1) * xs * np.exp(-(d / 0.25) ** 2)
        dz = trompa * np.clip(1 - (sx / 1.3) ** 2, 0, 1) * np.exp(-(d / 0.18) ** 2)
        D = np.zeros_like(V)
        D[:, 0] = dx
        D[:, 1] = dy * ED
        D[:, 2] = dz * ED
        return D * _frente(V)[:, None]
    return f


def _boca_elegible(p, V):
    return len(V) > 5000 or (abs(V[:, 0]).max() < 0.1 and V[:, 1].min() > 0.51 and V[:, 1].max() < 0.57 and V[:, 2].max() > 0.08)


def reemplazar_morph(E, nombre, campo, elegible, suavizar=4):
    nodo, malla = _malla_rostro(E)
    i = malla["extras"]["targetNames"].index(nombre)
    for p in malla["primitives"]:
        V, _ = E.leer(p)
        D = campo(V) if elegible(p, V) else np.zeros_like(V)
        if suavizar and len(V) > 1000 and np.abs(D).max() > 0:
            D = gestos.suavizar_delta(E, p, V, D, suavizar)
        p["targets"][i]["POSITION"] = E._add(D, "VEC3", None, True) if np.abs(D).max() > 0 else _ceros(E, len(V))
    E.b = bytes(E.out)
    E.log.append({"operacion": f"morph redefinido {nombre}"})


def _materiales_boca(E):
    for nombre, col in ((DIENTES, DIENTES_LINEAL), (LENGUA, LENGUA_LINEAL)):
        if not any(m["name"] == nombre for m in E.j["materials"]):
            E.j["materials"].append({"name": nombre, "doubleSided": True,
                                     "pbrMetallicRoughness": {"baseColorFactor": col, "metallicFactor": 0.0, "roughnessFactor": 0.85}})


def _bordes_rendija(E):
    """Borde de arriba y de abajo del hueco de la boca, por x (de la piel grande, antes de cualquier morph)."""
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    V = accesor(E.j, E.b, q["attributes"]["POSITION"]).astype(float)
    F = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
    k = np.round(V / 1e-6).astype(np.int64); _, w = np.unique(k, axis=0, return_inverse=True); w = w.ravel()
    Fw = w[F]; Ed = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
    e, c = np.unique(Ed, axis=0, return_counts=True)
    Pw = np.zeros((w.max() + 1, 3)); Pw[w] = V
    b = np.unique(e[c == 1])
    B = Pw[b]; B = B[(B[:, 2] > 0.1) & (np.abs(B[:, 1] - Y0) < 0.02) & (np.abs(B[:, 0]) < 0.05)]
    xs = np.linspace(-XW, XW, 25); arr, aba = [], []
    for x in xs:
        m = np.abs(B[:, 0] - x) < 0.004
        arr.append(B[m, 1].max() if m.any() else y_rendija(x)); aba.append(B[m, 1].min() if m.any() else y_rendija(x))
    return xs, np.array(arr), np.array(aba)


def _tira_dientes(E, arriba: bool, n=24):
    """Banda curva de dientes (frente + canto), detrás del labio, pegada al borde real del hueco + 1.2 mm·u:
    en reposo no se ven; se descubren cuando el labio se separa."""
    xs, b_arr, b_aba = _bordes_rendija(E)
    x = np.linspace(-0.026, 0.026, n)
    z_fr = Z_DIENTES - 0.010 * (x / XW) ** 2
    if arriba:
        y_borde = np.interp(x, xs, b_arr) + 0.0012
        y_otro = y_borde + 0.0080
    else:
        y_borde = np.interp(x, xs, b_aba) - 0.0050   # más abajo: con la cámara del juego mirando desde arriba no asoman
        y_otro = y_borde - 0.0055
    filas = [(y_otro, z_fr), (y_borde, z_fr), (y_borde, z_fr - 0.004)]
    V = np.concatenate([np.stack([x, yy, zz], 1) for yy, zz in filas])
    F = _rejilla(len(filas), n)
    if not arriba:
        F = F[:, ::-1]
    N = np.tile([0.0, 0.0, 1.0], (len(V), 1))
    N[2 * n:] = [0.0, -1.0 if arriba else 1.0, 0.0]
    return V, F, N


def _lengua():
    Vv, Fv = re.elipsoide((0.0, y_rendija(0) - 0.0150, Z_DIENTES - 0.014), (0.019, 0.0045, 0.0085), nu=20, nv=10)
    T = Vv[Fv]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    N = np.zeros_like(Vv)
    for i in range(3):
        np.add.at(N, Fv[:, i], n)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return Vv, Fv, N


def _anclas_mandibula(E):
    """Vértices de la barbilla (piel grande, 2–3 cm·u bajo la rendija) y sus deltas por morph:
    los dientes de abajo y la lengua siguen a la mandíbula, no al labio."""
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    p = max(malla["primitives"], key=lambda q: E.j["accessors"][q["attributes"]["POSITION"]]["count"])
    V, T = E.leer(p)
    yr = y_rendija(V[:, 0])
    m = (np.abs(V[:, 0]) < XW * 1.1) & (V[:, 2] > 0.12) & (V[:, 1] < yr - 0.018) & (V[:, 1] > yr - 0.030)
    return V[m], {nm: T[i][m] for i, nm in enumerate(nombres)}


def _seguir(Vp, anclas, deltas, factor=1.0):
    """Delta de cada vértice de la pieza = promedio (por distancia en x) de las anclas de la barbilla."""
    dx = np.abs(Vp[:, None, 0] - anclas[None, :, 0])
    w = np.exp(-(dx / 0.006) ** 2) + 1e-9
    w /= w.sum(1, keepdims=True)
    return {nm: factor * (w @ D) for nm, D in deltas.items() if np.abs(D).max() > 1e-7}


def ahondar_cavidad(E):
    """La copa negra de la boca era de 2.5 cm: se hace más honda para que quepan dientes y lengua.
    El borde (pegado a los labios) no se mueve; los morphs se conservan."""
    for p in E.prims(BOCA_INT):
        V, T = E.leer(p)
        if len(V) < 300:
            continue
        prof = np.clip(Z_LABIO - V[:, 2], 0, None)
        V2 = V.copy(); V2[:, 2] = Z_LABIO - prof * HONDO
        V2[:, 2] = np.where(V[:, 2] > 0.1445, V[:, 2], V2[:, 2])
        E.escribir(p, V2, T)
    E.log.append({"operacion": "cavidad de la boca más honda", "factor": HONDO})


def boca(E):
    _materiales_boca(E)
    ahondar_cavidad(E)
    for nm in REDEFINIDOS:
        reemplazar_morph(E, nm, campo_boca(**FORMAS[nm]), _boca_elegible)
    for nm in ("boca_sonrisa_abierta", "boca_dientes"):
        gestos.agregar_morph(E, nm, {}, campo_boca(**FORMAS[nm]), elegible=_boca_elegible, suavizar=4)
    anclas, deltas = _anclas_mandibula(E)
    from scipy.spatial import cKDTree
    q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
    Vp = accesor(E.j, E.b, q["attributes"]["POSITION"]).astype(float); Vp = Vp[Vp[:, 2] > 0.09]
    arbol = cKDTree(Vp[:, :2])

    def adentro(V, margen=0.004):
        """Ningún vértice de dientes/lengua queda a menos de 4 mm·u de la piel de enfrente (no atraviesa la barbilla)."""
        d, i = arbol.query(V[:, :2], k=6)
        z = Vp[i, 2].min(1)
        V = V.copy(); V[:, 2] = np.minimum(V[:, 2], z - margen)
        return V
    # dientes de arriba: fijos al cráneo (el labio sube y los descubre)
    V, F, N = _tira_dientes(E, True); V = adentro(V)
    agregar_capa(E, DIENTES, V, N, F, "Head", {}, "dientes de arriba")
    # dientes de abajo y lengua: siguen a la mandíbula (barbilla) en todos los morphs
    V, F, N = _tira_dientes(E, False); V = adentro(V)
    agregar_capa(E, DIENTES, V, N, F, "Head", {k: V + d for k, d in _seguir(V, anclas, deltas).items()}, "dientes de abajo")
    V, F, N = _lengua(); V = adentro(V)
    agregar_capa(E, LENGUA, V, N, F, "Head", {k: V + d for k, d in _seguir(V, anclas, deltas, 0.9).items()}, "lengua")


# --- escritura en el GLB ------------------------------------------------------
from copox.medicion.glb_util import add_raw as _add_raw  # noqa: E402,F401  (movido a la librería)


def _malla_rostro(E):
    for n in E.j["nodes"]:
        if "mesh" in n and E.j["meshes"][n["mesh"]].get("extras", {}).get("targetNames"):
            return n, E.j["meshes"][n["mesh"]]


def _ceros(E, n):
    E._ceros = getattr(E, "_ceros", {})
    if n not in E._ceros:
        E._ceros[n] = E._add(np.zeros((n, 3), np.float32), "VEC3", None, True)
    return E._ceros[n]


def piel_vecina(E):
    """Árbol de la piel grande de la cabeza (posición, normal, color) para que el párpado se funda con ella."""
    from scipy.spatial import cKDTree
    p = max((q for q in E.prims(PIEL)), key=lambda q: E.j["accessors"][q["attributes"]["POSITION"]]["count"])
    V = accesor(E.j, E.b, p["attributes"]["POSITION"]).astype(float)
    N = accesor(E.j, E.b, p["attributes"]["NORMAL"]).astype(float)
    C = accesor(E.j, E.b, p["attributes"]["COLOR_0"]).astype(float) if "COLOR_0" in p["attributes"] else None
    if C is not None and C.max() > 1.5:
        C = C / 65535.0
    return cKDTree(V), N, C


def pegar_borde(E, P, nr, nc, dy):
    """La fila fija del párpado (borde de arriba o de abajo) sale de la placa del ojo 2 mm·u (dy) y se apoya
    en la piel de la cara: el párpado baja en rampa hasta la piel, sin cruzar la placa ni dejar escalón
    (el escalón hacía una línea de sombra bajo el ojo)."""
    from scipy.spatial import cKDTree
    if not hasattr(E, "_piel2d"):
        q = max((x for x in E.prims(PIEL)), key=lambda x: E.j["accessors"][x["attributes"]["POSITION"]]["count"])
        V = accesor(E.j, E.b, q["attributes"]["POSITION"]).astype(float)
        V = V[V[:, 2] > 0.09]
        E._piel2d = (cKDTree(V[:, :2]), V[:, 2])
    arbol, Z = E._piel2d
    P = P.reshape(nr, nc, 3).copy()
    P[0, :, 1] += dy
    d, idx = arbol.query(P[0, :, :2], k=4)
    wi = 1 / np.maximum(d, 1e-6)
    P[0, :, 2] = (Z[idx] * wi).sum(1) / wi.sum(1) + 0.0003
    return P.reshape(-1, 3)


def fundir(arbol, N_piel, C_piel, P_muestra, F, iteraciones=3):
    """Normal y color de la piel más cercana, suavizados sobre la rejilla del párpado."""
    _, idx = arbol.query(P_muestra, k=6)
    N = N_piel[idx].mean(1)
    for _ in range(iteraciones):
        S_ = np.zeros_like(N); c = np.zeros(len(N))
        for a, b in ((0, 1), (1, 2), (2, 0), (1, 0), (2, 1), (0, 2)):
            np.add.at(S_, F[:, a], N[F[:, b]]); np.add.at(c, F[:, a], 1)
        N = 0.5 * N + 0.5 * S_ / np.maximum(c, 1)[:, None]
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    C = None if C_piel is None else C_piel[idx].mean(1)
    return N, C


def agregar_capa(E, material, V, N, F, hueso, objetivos: dict, nombre, color=None):
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    mat = next(i for i, m in enumerate(E.j["materials"]) if m["name"] == material)
    jn = [E.j["nodes"][k]["name"] for k in E.j["skins"][0]["joints"]].index(hueso)
    J = np.zeros((len(V), 4), np.uint16); J[:, 0] = jn
    W = np.zeros((len(V), 4), np.float32); W[:, 0] = 1
    at = {"POSITION": E._add(V, "VEC3", 34962, True), "NORMAL": E._add(N, "VEC3", 34962),
          "JOINTS_0": _add_raw(E, J, 5123, "VEC4", 34962), "WEIGHTS_0": _add_raw(E, W, 5126, "VEC4", 34962)}
    if color is not None:
        C = np.ones((len(V), 4), np.float32); C[:, :color.shape[1]] = color
        at["COLOR_0"] = E._add(C, "VEC4", 34962)
    prim = {"attributes": at, "indices": _add_raw(E, F.astype(np.uint32).ravel(), 5125, "SCALAR", 34963),
            "material": mat, "targets": []}
    for nm in nombres:
        if nm in objetivos:
            prim["targets"].append({"POSITION": E._add(objetivos[nm] - V, "VEC3", None, True)})
        else:
            prim["targets"].append({"POSITION": _ceros(E, len(V))})
    malla["primitives"].append(prim)
    E.b = bytes(E.out)
    E.log.append({"operacion": nombre, "material": material, "vertices": int(len(V)), "triangulos": int(len(F)),
                  "morphs": sorted(objetivos)})


def main(src, dst):
    E = re.Editor(src)
    base = next(m for m in E.j["materials"] if m["name"] == "LINEA_PARPADO_CAFE")
    E.j["materials"].append({**base, "name": PESTANA, "doubleSided": True,
                             "pbrMetallicRoughness": {"baseColorFactor": PESTANA_LINEAL, "metallicFactor": 0.0, "roughnessFactor": 1.0}})
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    # 1) morphs nuevos, vacíos por ahora (se llenan en las capas)
    for lado in "LR":
        for m in NUEVOS:
            gestos.agregar_morph(E, f"{m}_{lado}", {})
    nombres = malla["extras"]["targetNames"]
    # 2) quitar el párpado viejo: piezas de piel/línea plegadas a un punto y placa sin deformar
    placas = {}
    for k, p in enumerate(malla["primitives"]):
        mn = E.j["materials"][p["material"]]["name"]
        V, T = E.leer(p)
        afecta = {nombres[i] for i, D in enumerate(T) if np.abs(D).max() > 1e-7}
        par = {f"parpado_{x}" for x in "LR"} | {f"alegre_{x}" for x in "LR"}
        if mn.startswith("C7V2_eye_BAKE_"):
            placas[mn[-1]] = p
            for i, nm in enumerate(nombres):
                if nm in par:
                    p["targets"][i]["POSITION"] = _ceros(E, len(V))
        elif afecta and afecta <= par:
            centro = V.mean(0) - np.array([0, 0, 0.03])   # dentro de la cabeza, detrás de la placa
            p["attributes"]["POSITION"] = E._add(np.tile(centro, (len(V), 1)), "VEC3", 34962, True)
            for i in range(len(p.get("targets", []))):
                p["targets"][i]["POSITION"] = _ceros(E, len(V))
    E.b = bytes(E.out)
    E.log.append({"operacion": "párpado viejo retirado (piezas plegadas, placa del ojo sin deformar)"})
    # 3) capas nuevas por ojo
    arbol, N_piel, C_piel = piel_vecina(E)
    for lado in "LR":
        pl = Placa(E, placas[lado])
        for capa, (V, N, F, obj) in capas(pl).items():
            objetivos = {f"{m}_{lado}": P for m, P in obj.items()}
            color = None
            if capa != "pestana":
                nr, dy = (R_SUP, 0.002) if capa == "piel_sup" else (R_INF, -0.002)
                V = pegar_borde(E, V, nr, NC, dy)
                obj = {m: pegar_borde(E, P, nr, NC, dy) for m, P in obj.items()}
                objetivos = {f"{m}_{lado}": P for m, P in obj.items()}
                # la piel del párpado toma normal y color (rubor incluido) de la piel de la cara: no se ve el borde
                N, color = fundir(arbol, N_piel, C_piel, obj["parpado"], F)
            agregar_capa(E, PESTANA if capa == "pestana" else PIEL, V, N, F, "Head", objetivos, f"párpado {capa} {lado}", color)
    cachetes_y_boca(E)
    boca(E)
    gestos.rellenar_pesos(E)
    expresiones(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V24: párpados fundidos, ojo feliz, cachetes, comisuras y boca para hablar (dientes y lengua). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
