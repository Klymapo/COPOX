"""Adán V36 (sobre V22 HABLA → V35): mano nueva de una sola pieza, con membranas — geometría.

Decisión de Admin (18 oct 2026): "Geometría. Tratemos de llegar al parecido con las referencias visuales".
Antes: la mano eran 7 piezas sueltas por lado (palma, 4 dedos, base y punta del pulgar) metidas una en otra; el puño
no podía cerrar en bloque y la mano abierta tenía un escalón recto entre palma y dedos (visual-critic V34/V35).
Ahora (copox/medicion/mano_geo.py): una superficie implícita alrededor de los huesos en reposo de V35 —palma que se
angosta hacia la muñeca, dedos y pulgar como cápsulas cónicas por falange, eminencia tenar— con unión suave que hace
las membranas en "U" y el nudillo redondeado. Marching cubes + Taubin, y Godot (meshoptimizer) baja los triángulos.
Pesos por cadena (regla V27) suavizados. Medidas de la mano: las de V34–V35 (SENKU mano.py), que ya iban contra la
mano con regla. Las 7 piezas viejas por lado se quitan de la malla (las versiones anteriores quedan intactas).
Uso: python receta_adan_v36.py ADAN_V22_HABLA.glb ADAN_V36.glb
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion import mano_geo as mg  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v35 as v35  # noqa: E402
import receta_adan_v27 as v27  # noqa: E402
import receta_adan_v24 as v24  # noqa: E402

VIEJAS = ("Palma", "DedoIndex", "DedoMiddle", "DedoRing", "DedoLittle", "BasePulgar", "DedoThumb")
DEDO_R = {"Index": 0.0087, "Middle": 0.0090, "Ring": 0.0087, "Little": 0.0080}   # hueco ≈ 0.15 del ancho (mano con regla)
PULGAR_R = 0.0112
PULGAR_PALMA = 0.88
GROSOR = 0.029
RADIO_PALMA = 0.012
ANGOSTA_PULGAR = 0.45       # en la muñeca, el lado del pulgar mide 45 % (diagonal hacia el índice)
K_MEMBRANA = 0.0065
TRIS_META = 2600            # por mano, después de simplificar
GODOT = os.environ.get("GODOT_BIN", "")      # sin Godot no se simplifica (malla densa)


def _piezas(E):
    out = {}
    for i, p in enumerate(E.j["meshes"][0]["primitives"]):
        nm = p.get("extras", {}).get("pieza")
        if nm:
            out[nm] = (i, p)
    return out


def diseno(E):
    j = E.j
    sk = j["skins"][0]
    nombres = [j["nodes"][k]["name"] for k in sk["joints"]]
    ibm = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    H = {n: np.linalg.inv(ibm[i])[:3, 3] for i, n in enumerate(nombres)}
    pz = _piezas(E)
    V = lambda nm: accesor(j, E.b, pz[nm][1]["attributes"]["POSITION"]).astype(float)
    puntas = {}
    for d in DEDO_R:
        P = V(f"Dedo{d}L")
        # la punta sigue la dirección de la falange media (dedo recto, sin gancho), hasta el largo del dedo viejo
        a, b = H[f"Left{d}Intermediate"], H[f"Left{d}Distal"]
        u = (b - a) / np.linalg.norm(b - a)
        largo = (P[:, 0].max() - DEDO_R[d] * 0.85 - b[0]) / max(u[0], 1e-6)
        puntas[d] = b + u * largo
    T = V("DedoThumbL")
    base = H["LeftThumbDistal"]
    u = base - H["LeftThumbProximal"]; u /= np.linalg.norm(u)
    largo = float(((T - base) @ u).max())        # punta = lo más lejos a lo largo de la falange distal
    pulgar_punta = base + u * (largo - PULGAR_R * 0.85)
    # largo total del pulgar (metacarpo → punta) a PULGAR_PALMA del largo de la palma (mano con regla 0.81)
    meta = H["LeftThumbMetacarpal"]
    nud = np.mean([H[f"Left{d}Proximal"] for d in DEDO_R], axis=0)
    palma_L = float(np.linalg.norm(nud - H["LeftHand"]))
    hasta_base = float(np.linalg.norm(base - meta))
    pulgar_punta = base + u * max(PULGAR_PALMA * palma_L - hasta_base - PULGAR_R * 0.4, 0.004)
    palma = V("PalmaL")
    zs = [puntas[d][2] for d in DEDO_R]
    z0 = H["LeftLittleProximal"][2] - DEDO_R["Little"] * 0.95
    z1 = H["LeftIndexProximal"][2] + DEDO_R["Index"] * 0.95
    del zs
    meta = H["LeftThumbMetacarpal"]
    tenar = (meta + np.array([0.004, -0.002, -0.009]), np.array([0.017, 0.0115, 0.013]))
    e = ESCALA_R
    extra = {k: (v(H) if callable(v) else v) for k, v in DISENO_EXTRA.items()}
    return mg.Diseno(H, puntas, pulgar_punta, palma_x0=float(palma[:, 0].min()), palma_y=float(H["LeftHand"][1]),
                     palma_z=(float(z0), float(z1)), grosor=GROSOR * e, dedo_r={k: v * e * DEDO_R_FACTOR for k, v in DEDO_R.items()},
                     pulgar_r=PULGAR_R * e * PULGAR_R_FACTOR, tenar=(tenar[0], tenar[1] * e), k_membrana=K_MEMBRANA * e,
                     radio_palma=RADIO_PALMA * e, angosta_pulgar=ANGOSTA_PULGAR, **extra), nombres


def simplificar(V, T, meta, carpeta):
    """meshoptimizer vía Godot (ImporterMesh.generate_lods): se elige el LOD más cercano a `meta` triángulos.
    En ALTH_CALIDAD=borrador no se simplifica (iteración rápida; la malla sale más pesada)."""
    from copox.medicion.malla_rapida import simplificar_activo
    if not simplificar_activo() or not GODOT or not os.path.exists(GODOT):
        return V, T
    np.save(os.path.join(carpeta, "V.npy"), V.astype(np.float32)); np.save(os.path.join(carpeta, "T.npy"), T.astype(np.int32))
    with open(os.path.join(carpeta, "malla.json"), "w") as f:
        json.dump({"V": V.astype(float).round(7).tolist(), "T": T.astype(int).tolist(), "meta": int(meta)}, f)
    gd = os.path.join(os.path.dirname(__file__), "..", "..", "copox", "godot", "herramientas", "simplificar.gd")
    proy = os.path.join(os.path.dirname(__file__), "..", "..", "copox", "godot")
    r = subprocess.run(["xvfb-run", "-a", GODOT, "--headless", "--path", proy, "--script", gd, "--",
                        os.path.join(carpeta, "malla.json"), os.path.join(carpeta, "lod.json")],
                       capture_output=True, text=True, timeout=600)
    out = os.path.join(carpeta, "lod.json")
    if not os.path.exists(out):
        raise RuntimeError("Godot no simplificó: " + r.stdout[-500:] + r.stderr[-500:])
    d = json.load(open(out))
    V2 = np.array(d["V"], float); T2 = np.array(d["T"], np.int64).reshape(-1, 3)
    usados = np.unique(T2)
    mapa = -np.ones(len(V2), np.int64); mapa[usados] = np.arange(len(usados))
    # Godot guarda los triángulos en sentido horario visto de frente; la malla de entrada iba antihorario
    T3 = mapa[T2]
    return V2[usados], T3


def mano_nueva(E, carpeta):
    D, nombres = diseno(E)
    V, T = D.malla()
    n0 = len(T)
    V, T = simplificar(V, T, TRIS_META, carpeta)
    N = mg.normales(V, T)
    J4, W4 = mg.pesos(V, T, D, nombres, v27.pesos_cadena)
    pz = _piezas(E)
    prims = E.j["meshes"][0]["primitives"]
    mat = pz["PalmaL"][1]["material"]
    ntar = len(pz["PalmaL"][1].get("targets", []))
    nuevas = []
    for lado, (VV, TT, NN, JJ) in (("L", (V, T, N, J4)), ("R", mg.espejo(V, T, N, J4, nombres))):
        ceros = E._add(np.zeros((len(VV), 3), np.float32), "VEC3", None, True)
        p = {"attributes": {"POSITION": E._add(VV.astype(np.float32), "VEC3", 34962, True),
                            "NORMAL": E._add(NN.astype(np.float32), "VEC3", 34962),
                            "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(JJ, np.uint16), 5123, "VEC4", 34962),
                            "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
             "indices": v24._add_raw(E, np.ascontiguousarray(TT.ravel(), np.uint32), 5125, "SCALAR", 34963),
             "material": mat, "extras": {"pieza": "Mano" + lado}, "targets": [{"POSITION": ceros} for _ in range(ntar)]}
        nuevas.append(p)
    quitar = {f"{v}{l}" for v in VIEJAS for l in "LR"}
    E.j["meshes"][0]["primitives"] = [p for p in prims if p.get("extras", {}).get("pieza") not in quitar] + nuevas
    E.b = bytes(E.out)
    E.log.append({"operacion": "mano nueva de una pieza (palma+dedos+pulgar con membranas)", "tris_marching": int(n0),
                  "tris_mano": int(len(T)), "vertices_mano": int(len(V)), "piezas_quitadas": sorted(quitar)})


PULGAR_ARRIBA = 0.006       # u: la base del pulgar sube hacia los nudillos (en la mano con regla nace a 1/3 de la palma)
PULGAR_AFUERA = 0.008       # u: y sale hacia el borde de la palma (nace en el borde, no adentro)
# abanico de los dedos (grados alrededor de la normal de la palma; + = hacia el meñique en la mano izquierda) y
# giro extra del pulgar hacia los dedos: la mano con regla abre los dedos hacia las puntas
ABANICO = {"Index": -3.0, "Middle": 0.0, "Ring": 1.0, "Little": 5.0}
PULGAR_GIRO_EXTRA = 6.0
LARGO = {"Index": 1.04, "Middle": 1.0, "Ring": 0.94, "Little": 0.92}   # largo de cada dedo (silueta de la regla)
ESPACIADO = 0.86            # los dedos se acercan entre sí (palma más angosta, silueta de la mano con regla)
PULGAR_ESCALA = 0.85        # huesos del pulgar más cortos (en el puño sobresalía de la hoja de vistas)


PULGAR_PUNO = {"giro_y": 22.0, "flexion": 28.0}   # en puño el pulgar se acuesta sobre el índice (hoja de vistas)


def _qeje(eje, grados):
    eje = np.asarray(eje, float); eje = eje / np.linalg.norm(eje); h = np.radians(grados) / 2
    return np.r_[eje * np.sin(h), np.cos(h)]


def pulgar_en_puno(E):
    """Donde los dedos hacen puño (misma fracción que receta V35), el pulgar gira hacia los dedos y se flexiona
    sobre el puño: metacarpo q' = Δy·q (marco de la mano); proximal y distal q' = q·Δflex (marco propio)."""
    j = E.j
    nombres = {i: n.get("name", "") for i, n in enumerate(j["nodes"])}
    sk = j["skins"][0]
    ibm = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    Hn = {j["nodes"][k]["name"]: np.linalg.inv(ibm[i])[:3, 3] for i, k in enumerate(sk["joints"])}
    hechos = 0
    for a in j.get("animations", []):
        canales = {nombres[ch["target"]["node"]]: ch for ch in a["channels"] if ch["target"]["path"] == "rotation"}
        for lado, sg in (("Left", 1.0), ("Right", -1.0)):
            ip = canales.get(lado + "IndexProximal") or canales.get(lado + "MiddleProximal")
            if ip is None:
                continue
            Qp = accesor(j, E.b, a["samplers"][ip["sampler"]]["output"]).astype(float).reshape(-1, 4)
            curva = np.degrees(2 * np.arctan2(-sg * Qp[:, 2], Qp[:, 3]))
            u = np.clip((curva - v35.CURVA_ABIERTA) / (v35.CURVA_PUNO - v35.CURVA_ABIERTA), 0, 1)
            f = u * u * (3 - 2 * u)
            if canales.get(lado + "IndexProximal") is None or f.max() < 1e-6:
                continue
            # si el clip ya acomoda el pulgar (metacarpo girado ≥ 25°, p. ej. M31_3_Puno o Punch), no se toca
            cm = canales.get(lado + "ThumbMetacarpal")
            if cm is not None:
                Qm = accesor(j, E.b, a["samplers"][cm["sampler"]]["output"]).astype(float).reshape(-1, 4)
                if len(Qm) == len(f):
                    ang = np.degrees(2 * np.arccos(np.clip(np.abs(Qm[:, 3]), 0, 1)))
                    f = f * np.clip((25.0 - ang) / 10.0, 0, 1)
            if f.max() < 1e-6:
                continue
            d = Hn[lado + "ThumbDistal"] - Hn[lado + "ThumbMetacarpal"]; d /= np.linalg.norm(d)
            eje_flex = np.cross(d, [0.0, -1.0, 0.0])          # la punta baja hacia la palma
            for hueso, modo in ((lado + "ThumbMetacarpal", "y"), (lado + "ThumbProximal", "f"), (lado + "ThumbDistal", "f")):
                ch = canales.get(hueso)
                if ch is None:
                    continue
                sm = a["samplers"][ch["sampler"]]
                Q = accesor(j, E.b, sm["output"]).astype(float).reshape(-1, 4)
                if len(Q) != len(f):
                    continue
                out = []
                for q, fk in zip(Q, f):
                    if modo == "y":
                        out.append(v35._qmul(_qeje([0, 1, 0], sg * PULGAR_PUNO["giro_y"] * fk), q))
                    else:
                        out.append(v35._qmul(q, _qeje(eje_flex, PULGAR_PUNO["flexion"] * fk)))
                sm["output"] = E._add(np.asarray(out, np.float32), "VEC4")
                hechos += 1
    E.b = bytes(E.out)
    E.log.append({"operacion": "pulgar acostado sobre el puño", "canales": hechos})


# Con la mano de una pieza el puño de V35 (85/100/70°) metía las puntas en la palma (puntas dentadas, visual-critic);
# aquí se cierra menos en las falanges finales.
# Ganchos para versiones siguientes (vacíos en V36: no cambian su resultado)
EXTRA_EDICIONES = []         # ediciones de proporciones añadidas antes de construir la mano
DISENO_EXTRA = {}            # parámetros extra para mano_geo.Diseno
ESCALA_R = 1.0               # multiplica radios, grosor y redondeo de la mano
DEDO_R_FACTOR = 1.0          # engrosa sólo dedos (y PULGAR_R_FACTOR el pulgar); V38+
PULGAR_R_FACTOR = 1.0


PUNO_V36 = {"Proximal": 82.0, "Intermediate": 88.0, "Distal": 45.0}


def main(src, dst):
    t35 = dst + ".v35.glb"
    puno_v35 = dict(v35.PUNO)
    v35.PUNO.clear(); v35.PUNO.update(PUNO_V36)
    try:
        v35.main(src, t35)
    finally:
        v35.PUNO.clear(); v35.PUNO.update(puno_v35)
    from copox.medicion import proporciones
    t35b = dst + ".v35b.glb"
    from copox.medicion.gltf import leer_glb
    jj, _ = leer_glb(t35)
    ix = {n.get("name"): i for i, n in enumerate(jj["nodes"])}
    par = {c: i for i, n in enumerate(jj["nodes"]) for c in n.get("children", [])}

    def _mundo(i):
        p_ = np.zeros(3)
        while i is not None:
            p_ += np.array(jj["nodes"][i].get("translation", [0, 0, 0]), float); i = par.get(i)
        return p_
    zc = np.mean([_mundo(ix["LeftMiddleProximal"])[2], _mundo(ix["LeftRingProximal"])[2]])
    juntar = []
    for d in ("Index", "Middle", "Ring", "Little"):
        dz = (ESPACIADO - 1) * (_mundo(ix[f"Left{d}Proximal"])[2] - zc)
        juntar += [{"tipo": "mover", "huesos": f"Left{d}Proximal", "delta": [0, 0, float(dz)]},
                   {"tipo": "mover", "huesos": f"Right{d}Proximal", "delta": [0, 0, float(dz)]}]
    proporciones.editar(t35, t35b, juntar + [{"tipo": "mover", "huesos": "LeftThumbMetacarpal", "delta": [PULGAR_ARRIBA, 0, PULGAR_AFUERA]},
                                    {"tipo": "mover", "huesos": "RightThumbMetacarpal", "delta": [-PULGAR_ARRIBA, 0, PULGAR_AFUERA]},
                                    {"tipo": "escala_eje", "raiz": "LeftThumbMetacarpal", "hacia": "LeftThumbDistal", "factor": PULGAR_ESCALA},
                                    {"tipo": "escala_eje", "raiz": "RightThumbMetacarpal", "hacia": "RightThumbDistal", "factor": PULGAR_ESCALA}],
                        nota="Adán V36: base del pulgar hacia los nudillos.")
    giros = []
    for d, g in ABANICO.items():
        if g:
            giros += [{"tipo": "rotar", "raiz": f"Left{d}Proximal", "eje": [0, 1, 0], "grados": g},
                      {"tipo": "rotar", "raiz": f"Right{d}Proximal", "eje": [0, 1, 0], "grados": -g}]
    giros += [{"tipo": "rotar", "raiz": "LeftThumbMetacarpal", "eje": [0, 1, 0], "grados": PULGAR_GIRO_EXTRA},
              {"tipo": "rotar", "raiz": "RightThumbMetacarpal", "eje": [0, 1, 0], "grados": -PULGAR_GIRO_EXTRA}]
    largos = []
    for d, f in LARGO.items():
        if f != 1.0:
            largos += [{"tipo": "escala_eje", "raiz": f"{l}{d}Proximal", "hacia": f"{l}{d}Distal", "factor": f} for l in ("Left", "Right")]
    t35c = dst + ".v35c.glb"
    proporciones.editar(t35b, t35c, giros + largos + EXTRA_EDICIONES, nota="Adán V36: abanico de dedos y pulgar.")
    proporciones.conjugar_claves(t35c, t35, giros)
    os.remove(t35b); os.remove(t35c)
    E = re.Editor(t35)
    carpeta = os.path.dirname(os.path.abspath(dst))
    mano_nueva(E, carpeta)
    pulgar_en_puno(E)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V36: V35 + mano nueva de una pieza con membranas. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp); os.remove(t35)
    for f in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f)):
            os.remove(os.path.join(carpeta, f))
    return E.log


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2])[-1])
