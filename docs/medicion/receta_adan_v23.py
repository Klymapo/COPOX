"""Adán V23 (sobre Adán V22 HABLA): párpados de malla con línea de pestaña.

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
Uso: python receta_adan_v23.py ENTRADA SALIDA
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
NC, R_SUP, R_PEST, R_INF = 40, 7, 3, 6
NUEVOS = ["parpado_inf", "parpado_enojo", "parpado_triste"]


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
        return u, np.clip(vt - 0.012, 0.005, 1), vb, np.clip(vbot + 0.012, 0, 0.985)


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
    }
    inf_m = {
        "parpado": vt + 0.62 * alto,                 # sube a esconderse detrás de la pestaña
        "alegre": vt + (0.62 - 0.24 * (1 - s ** 2)) * alto,
        "parpado_inf": vt + 0.60 * alto,
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
    U = np.tile(u, (R_SUP, 1)); fr2 = np.linspace(0, 1, R_SUP)[:, None]

    def piel_sup(borde, grosor):
        fondo = np.maximum(borde - grosor + 0.35 * grosor, vt)
        return vt[None, :] + fr2 * (fondo - vt)[None, :]
    # en reposo la piel queda plegada en el borde (filas separadas 0.003 en v: sin vértices encimados)
    P0, N0 = malla(U, vt[None, :] + 0.003 * fr2, OFF_SUP)
    out["piel_sup"] = (P0, N0, _rejilla(R_SUP, NC),
                       {m: malla(U, piel_sup(b, g), OFF_SUP)[0] for m, (b, g) in sup_m.items()})
    # piel inferior: de vbot hacia arriba
    U = np.tile(u, (R_INF, 1)); fr3 = np.linspace(0, 1, R_INF)[:, None]
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


def expresiones(E):
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    ni = E.j["nodes"].index(nodo)
    for a in E.j["animations"]:
        extra = EXTRA_G.get(a.get("name"))
        if not extra:
            continue
        ch = next(c for c in a["channels"] if c["target"]["path"] == "weights" and c["target"]["node"] == ni)
        sm = a["samplers"][ch["sampler"]]
        t = accesor(E.j, E.b, sm["input"]).astype(float).reshape(-1)
        O = accesor(E.j, E.b, sm["output"]).astype(float).reshape(len(t), -1)
        rampa = (t - t.min()) / max(t.max() - t.min(), 1e-9)
        pesos = {nm: O[:, i] for i, nm in enumerate(nombres) if np.abs(O[:, i]).max() > 0}
        for k, val in extra.items():
            for nm in ([k] if k[-2:] in ("_L", "_R") or k.startswith("boca_") else [k + "_L", k + "_R"]):
                pesos[nm] = np.clip(pesos.get(nm, 0) + val * rampa, 0, 1)
        gestos.pista_pesos(E, a["name"], t, pesos)


# --- escritura en el GLB ------------------------------------------------------
def _add_raw(E, arr, ctype, typ, target=None):
    arr = np.ascontiguousarray(arr)
    while len(E.out) % 4:
        E.out.append(0)
    v = {"buffer": 0, "byteOffset": len(E.out), "byteLength": arr.nbytes}
    if target:
        v["target"] = target
    E.out.extend(arr.tobytes()); E.j["bufferViews"].append(v)
    E.j["accessors"].append({"bufferView": len(E.j["bufferViews"]) - 1, "componentType": ctype, "count": len(arr), "type": typ})
    return len(E.j["accessors"]) - 1


def _malla_rostro(E):
    for n in E.j["nodes"]:
        if "mesh" in n and E.j["meshes"][n["mesh"]].get("extras", {}).get("targetNames"):
            return n, E.j["meshes"][n["mesh"]]


def _ceros(E, n):
    E._ceros = getattr(E, "_ceros", {})
    if n not in E._ceros:
        E._ceros[n] = E._add(np.zeros((n, 3), np.float32), "VEC3", None, True)
    return E._ceros[n]


def agregar_capa(E, material, V, N, F, hueso, objetivos: dict, nombre):
    nodo, malla = _malla_rostro(E)
    nombres = malla["extras"]["targetNames"]
    mat = next(i for i, m in enumerate(E.j["materials"]) if m["name"] == material)
    jn = [E.j["nodes"][k]["name"] for k in E.j["skins"][0]["joints"]].index(hueso)
    J = np.zeros((len(V), 4), np.uint16); J[:, 0] = jn
    W = np.zeros((len(V), 4), np.float32); W[:, 0] = 1
    at = {"POSITION": E._add(V, "VEC3", 34962, True), "NORMAL": E._add(N, "VEC3", 34962),
          "JOINTS_0": _add_raw(E, J, 5123, "VEC4", 34962), "WEIGHTS_0": _add_raw(E, W, 5126, "VEC4", 34962)}
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
    for lado in "LR":
        pl = Placa(E, placas[lado])
        for capa, (V, N, F, obj) in capas(pl).items():
            objetivos = {f"{m}_{lado}": P for m, P in obj.items()}
            agregar_capa(E, PESTANA if capa == "pestana" else PIEL, V, N, F, "Head", objetivos, f"párpado {capa} {lado}")
    cachetes_y_boca(E)
    gestos.rellenar_pesos(E)
    expresiones(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V23: párpados de malla con pestaña, cachetes y comisuras. SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
