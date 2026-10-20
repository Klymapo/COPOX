"""Adán V39 (sobre V38): proporciones del cuerpo, torso nuevo con anatomía marcada, hombros y brazos según las
referencias de Adán (refs/personajes/adan/adan-cuerpo-4-vistas.jpg, adan-torso-4-vistas-captura.jpg).

Decisiones de Admin (18 oct 2026): torso "seguir la referencia" (más angosto y más profundo), anatomía "marcada",
grosor del antebrazo "hoja del cuerpo" y proporciones verticales "hacerlo todo ahora".

Medidas en la referencia (fracción del eje del brazo al piso, eje del brazo fijo):
  cintura del short 0.361 (V38 0.232) · entrepierna 0.573 (0.508) · dobladillo 0.689 (0.615) · tobillo 0.842 (0.803)
  torso de frente bajo la axila 0.256 de la envergadura (V38 0.313), cintura 0.233 (0.299); fondo 0.19–0.21 (0.17–0.18)
  antebrazo/codo de frente ~13 % más gruesos que V38 (brazo superior igual)

Pasos:
  1. V38 con el perfil del antebrazo ×1.13 hasta el codo (se desvanece hacia el hombro).
  2. Esqueleto: cadera y piernas bajan CADERA (entrepierna); el tronco de Spine para arriba (brazos, cabeza) no se
     mueve; las piernas se acortan repartiendo entre muslo y espinilla (la rodilla sube); los pies no cambian
     (etapa de pies aparte).
  3. Short: la cintura baja a la altura de la referencia (se comprime la parte de arriba del short) y su boca se
     ajusta al torso nuevo.
  4. Torso nuevo (copox/medicion/torso_geo.py): superficie implícita con el perfil de la referencia y anatomía
     marcada (pectorales con pliegue, esternón, abdomen en 3 filas, línea alba, ombligo, clavículas, omóplatos,
     columna, deltoides y trapecio). Sus orillas terminan dentro del short, del cuello y de los brazos. Pesos
     transferidos de la piel vieja (vecinos más cercanos) y suavizados.
Uso: GODOT_BIN=… python receta_adan_v39.py ADAN_V22_HABLA.glb ADAN_V39.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v38 as v38  # noqa: E402

FACTOR_ANTEBRAZO = [(0.0, 1.13), (1.0, 1.13), (1.6, 1.0)]
EJE_BRAZO = 0.4306           # u: eje del brazo en pose T (no se mueve)
REF = {"cintura": 0.361, "entrepierna": 0.573, "dobladillo": 0.689, "tobillo": 0.842}
CADERA = None                # se calcula: lo que baja la entrepierna para llegar a la referencia
TRIS_TORSO = 7000
CUELLO_DESDE = (0.470, 0.492)
HOMBRO_DESDE = (0.090, 0.118)  # u: el hombro y el brazo pesan en el torso sólo de aquí hacia afuera  # u: el peso del cuello entra en el torso sólo de aquí hacia arriba
SUAVIZADO_PESOS = 8          # pasadas de suavizado de los pesos transferidos al torso
PLIEGUES = (0.25, 0.35)      # pliegues del lado de la palma en los dedos (los picos del puño)
ANCHOS_DEDO = (0.012, 0.007, 0.005)   # rampas de pesos más suaves en el nudillo (los picos del puño bajan un poco)
PRONACION = 0.5              # al apuntar, la mitad del giro de la mano lo hace el antebrazo (muñeca sin pliegues)

# perfil del torso (y, medio ancho, medio fondo, centro z); medido en la referencia y llevado a unidades del modelo
# con la envergadura (0.256 / 0.233 de la envergadura bajo la axila / cintura; fondo 0.19–0.21)
PERFIL = [(0.262, 0.100, 0.080, 0.020), (0.290, 0.098, 0.080, 0.020), (0.330, 0.101, 0.082, 0.021),
          (0.370, 0.106, 0.086, 0.022), (0.400, 0.110, 0.088, 0.023), (0.430, 0.111, 0.084, 0.022),
          (0.455, 0.100, 0.072, 0.020), (0.475, 0.072, 0.058, 0.020), (0.490, 0.056, 0.052, 0.022),
          (0.500, 0.050, 0.050, 0.022)]
EXPONENTE = 2.6
RECORTES = {"x_max": 0.122, "y_min": 0.262, "y_max": 0.494}


def rasgos(T0):
    """Anatomía marcada sobre el torso base T0 (posiciones sobre su superficie)."""
    def borde(y, x, lado):
        a, b, c = [float(np.ravel(v)[0]) for v in T0.seccion(np.array([y]))]
        return c + lado * b * max(1 - (abs(x) / a) ** T0.p, 0) ** (1 / T0.p)
    fr = lambda y, x: borde(y, x, 1)      # noqa: E731
    es = lambda y, x: borde(y, x, -1)     # noqa: E731
    R = []
    # pectorales: volumen amplio con unión suave ancha + pliegue inferior marcado
    R.append(dict(tipo="suma", forma="elipsoide", c=[0.050, 0.412, fr(0.412, 0.050) - 0.009], r=[0.052, 0.034, 0.015], k=0.016))
    for a_, b_ in (((0.008, 0.384), (0.048, 0.379)), ((0.048, 0.379), (0.092, 0.394))):
        R.append(dict(tipo="surco", forma="capsula", a=[a_[0], a_[1], fr(a_[1], a_[0]) + 0.0045],
                      b=[b_[0], b_[1], fr(b_[1], min(b_[0], 0.09)) + 0.0045], r1=0.006, k=0.008))
    R.append(dict(tipo="surco", forma="capsula", a=[0, 0.388, fr(0.388, 0) + 0.004], b=[0, 0.438, fr(0.438, 0) + 0.004], r1=0.0035, k=0.005))
    for y in (0.300, 0.327, 0.354):                                                     # abdomen
        R.append(dict(tipo="suma", forma="elipsoide", c=[0.020, y, fr(y, 0.020) - 0.005], r=[0.018, 0.0125, 0.0085], k=0.007))
    R.append(dict(tipo="surco", forma="capsula", a=[0, 0.286, fr(0.286, 0) + 0.004], b=[0, 0.372, fr(0.372, 0) + 0.004], r1=0.0035, k=0.004))
    R.append(dict(tipo="surco", forma="elipsoide", c=[0, 0.281, fr(0.281, 0) + 0.001], r=[0.004, 0.005, 0.006], k=0.002))
    R.append(dict(tipo="suma", forma="capsula", a=[0.010, 0.461, fr(0.461, 0.010) - 0.0025], b=[0.080, 0.465, 0.052], r1=0.0045, r2=0.0025, k=0.005))
    R.append(dict(tipo="suma", forma="elipsoide", c=[0.054, 0.413, es(0.413, 0.054) + 0.006], r=[0.030, 0.037, 0.010], k=0.022))
    R.append(dict(tipo="hendidura", y=(0.285, 0.465), lado=-1, prof=0.0035, ancho=0.0045, rampa=0.02))          # columna
    R.append(dict(tipo="suma", forma="elipsoide", c=[0.108, 0.434, 0.016], r=[0.035, 0.038, 0.042], k=0.010))     # deltoides
    R.append(dict(tipo="suma", forma="capsula", a=[0.035, 0.478, 0.014], b=[0.105, 0.456, 0.014], r1=0.016, k=0.018))  # trapecio
    return R


def _prim(E, pieza):
    return next(p for p in E.j["meshes"][0]["primitives"] if p.get("extras", {}).get("pieza") == pieza)


from copox.medicion.glb_util import prims_de_pieza as _prims  # noqa: E402,F401  (movido a la librería)


from copox.medicion.glb_util import leer as _leer  # noqa: E402,F401  (movido a la librería)


def esqueleto(src, dst):
    """Paso 2. Devuelve (log, cadera)."""
    from copox.medicion import proporciones
    from copox.medicion.gltf import leer_glb
    j, b = leer_glb(src)
    E0 = type("E", (), {})(); E0.j, E0.b = j, b
    nombres, H = v38._skin(E0)
    L = EJE_BRAZO                                      # del eje del brazo al piso
    ent_ref = EJE_BRAZO - REF["entrepierna"] * L
    # entrepierna actual = lo más bajo del short del torso en el centro
    Vs = _leer(E0, _prims(E0, "Torso_SHORT_AZUL")[0], "POSITION").astype(float)
    ent = float(Vs[np.abs(Vs[:, 0]) < 0.01, 1].min())
    d = ent - ent_ref
    cad = H["LeftUpperLeg"][1]; rod = H["LeftLowerLeg"][1]; pie = H["LeftFoot"][1]
    pierna = cad - pie; nueva = pierna - d
    f = nueva / pierna
    muslo_nuevo = (cad - rod) * f
    # tras bajar todo menos los pies (la espinilla absorbe d), la rodilla sube para repartir: muslo × f
    sube_rodilla = (cad - rod) - muslo_nuevo
    ed = [{"tipo": "acortar", "hasta": ["LeftFoot", "RightFoot"], "fijos": ["Root"], "delta": float(d)},
          {"tipo": "mover", "huesos": "Spine", "delta": [0.0, float(d), 0.0]}]
    t1 = dst + ".e1.glb"
    r1 = proporciones.editar(src, t1, ed, nota="V39: cadera y piernas bajan; el tronco queda")
    r2 = proporciones.editar(t1, dst, [{"tipo": "mover_articulacion", "hueso": f"{l}LowerLeg", "delta": -float(sube_rodilla)}
                                       for l in ("Left", "Right")], nota="V39: rodilla reparte el acortamiento")
    os.remove(t1)
    return [{"operacion": "esqueleto: cadera y piernas", "baja_entrepierna_u": round(float(d), 4),
             "factor_pierna": round(float(f), 3), "sube_rodilla_u": round(float(sube_rodilla), 4),
             "vertices": r1["vertices_movidos"] + r2["vertices_movidos"]}], float(d)


def short(E, T0):
    """Paso 3: la cintura del short baja a la referencia y su boca abraza al torso nuevo."""
    y_cint = EJE_BRAZO - REF["cintura"] * EJE_BRAZO
    p = _prims(E, "Torso_SHORT_AZUL")[0]
    V = _leer(E, p, "POSITION").astype(float)
    top = float(V[:, 1].max()); lo = float(V[:, 1].min())
    V1 = V.copy()
    V1[:, 1] = lo + (V[:, 1] - lo) * (y_cint - lo) / (top - lo)
    t = np.clip((V1[:, 1] - lo) / (y_cint - lo), 0, 1); t = t * t * (3 - 2 * t)
    a, b, c = [np.asarray(v, float) for v in T0.seccion(V1[:, 1])]
    # medio ancho/fondo actual por anillo
    anillo = np.round(V[:, 1] / 0.002).astype(int)
    fx = np.ones(len(V)); fz = np.ones(len(V)); zc = np.zeros(len(V))
    for k_ in np.unique(anillo):
        m = anillo == k_
        ax = np.abs(V1[m, 0]).max(); cz = (V1[m, 2].max() + V1[m, 2].min()) / 2; bz = (V1[m, 2].max() - V1[m, 2].min()) / 2
        objetivo_x = a[m].mean() + 0.012; objetivo_z = b[m].mean() + 0.010
        fx[m] = 1 + (objetivo_x / ax - 1) * t[m]; fz[m] = 1 + (objetivo_z / bz - 1) * t[m]
        zc[m] = cz + (c[m].mean() - cz) * t[m]
        cz_m = cz
        V1[m, 2] = zc[m] + (V1[m, 2] - cz_m) * fz[m]
    V1[:, 0] = V1[:, 0] * fx
    from copox.medicion.gltf import accesor
    Tr = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
    N0 = _leer(E, p, "NORMAL").astype(float)
    N1 = v38._normales(V1, Tr)
    if np.mean(np.einsum("ij,ij->i", N1, N0)) < 0:
        N1 = -N1
    for q in _prims(E, "Torso_SHORT_AZUL"):
        q["attributes"]["POSITION"] = E._add(V1.astype(np.float32), "VEC3", 34962, True)
        q["attributes"]["NORMAL"] = E._add(N1.astype(np.float32), "VEC3", 34962)
    # piernas del short: el dobladillo baja a la referencia (se estira hacia abajo; la boca de arriba no se mueve)
    y_dob = EJE_BRAZO - REF["dobladillo"] * EJE_BRAZO
    dob0 = None
    for lado in "LR":
        for q in _prims(E, f"Pierna{lado}_SHORT_AZUL"):
            Vq = _leer(E, q, "POSITION").astype(float)
            tq, hq = float(Vq[:, 1].max()), float(Vq[:, 1].min()); dob0 = hq
            Vq[:, 1] = tq - (tq - Vq[:, 1]) * (tq - y_dob) / (tq - hq)
            Tq = accesor(E.j, E.b, q["indices"]).reshape(-1, 3).astype(np.int64)
            Nq0 = _leer(E, q, "NORMAL").astype(float); Nq = v38._normales(Vq, Tq)
            if np.mean(np.einsum("ij,ij->i", Nq, Nq0)) < 0:
                Nq = -Nq
            q["attributes"]["POSITION"] = E._add(Vq.astype(np.float32), "VEC3", 34962, True)
            q["attributes"]["NORMAL"] = E._add(Nq.astype(np.float32), "VEC3", 34962)
    E.b = bytes(E.out)
    return {"operacion": "short: cintura, boca y dobladillo", "cintura_u": round(y_cint, 4), "antes_u": round(top, 4),
            "dobladillo_u": round(y_dob, 4), "dobladillo_antes_u": round(dob0, 4)}


def torso(E, carpeta):
    """Paso 4."""
    import receta_adan_v24 as v24
    import receta_adan_v36 as v36
    from copox.medicion import torso_geo as tg
    from copox.medicion import mano_geo as mg
    T0 = tg.Torso(PERFIL, EXPONENTE)
    T = tg.Torso(PERFIL, EXPONENTE, rasgos=rasgos(T0), recortes=RECORTES)
    V, F = T.malla([-0.126, RECORTES["y_min"] - 0.004, -0.085], [0.126, RECORTES["y_max"] + 0.004, 0.135], paso=0.0012)
    n0 = len(F)
    V, F = v36.simplificar(V, F, TRIS_TORSO, carpeta)
    vol = float(np.einsum("ij,ij->i", V[F[:, 0]], np.cross(V[F[:, 1]], V[F[:, 2]])).sum())
    if vol < 0:
        F = F[:, ::-1].copy()
    N = mg.normales(V, F)
    nombres, _ = v38._skin(E)
    fuentes = []
    for pz in ("Torso_PIEL", "Cuello", "BrazoL", "BrazoR", "Torso_SHORT_AZUL"):
        for q in _prims(E, pz)[:1]:
            fuentes.append((_leer(E, q, "POSITION").astype(float), _leer(E, q, "JOINTS_0").astype(int),
                            _leer(E, q, "WEIGHTS_0").astype(float)))
    J4, W4 = tg.transferir_pesos(V, F, fuentes, len(nombres), suavizado=SUAVIZADO_PESOS)
    # el cuello sólo mueve la orilla de arriba del torso: bajo CUELLO_DESDE su peso pasa a Chest (si no, al girar la
    # cabeza se arruga el trapecio — se vio en Godot al apuntar)
    ic, ineck, ihead = nombres.index("Chest"), nombres.index("Neck"), nombres.index("Head")
    r = np.clip((V[:, 1] - CUELLO_DESDE[0]) / (CUELLO_DESDE[1] - CUELLO_DESDE[0]), 0, 1); r = r * r * (3 - 2 * r)
    Wd = np.zeros((len(V), len(nombres)))
    np.add.at(Wd, (np.repeat(np.arange(len(V)), 4), J4.ravel().astype(int)), W4.ravel())
    quita = (Wd[:, ineck] + Wd[:, ihead]) * (1 - r)
    Wd[:, ineck] *= r; Wd[:, ihead] *= r; Wd[:, ic] += quita
    # hombro y brazo sólo cerca del brazo (|x| > HOMBRO_DESDE): como en V38, el resto del torso es del tronco; si no, al
    # apuntar el hombro arruga la espalda
    rh = np.clip((np.abs(V[:, 0]) - HOMBRO_DESDE[0]) / (HOMBRO_DESDE[1] - HOMBRO_DESDE[0]), 0, 1); rh = rh * rh * (3 - 2 * rh)
    for nmb in ("LeftShoulder", "RightShoulder", "LeftUpperArm", "RightUpperArm"):
        ib = nombres.index(nmb); q_ = Wd[:, ib] * (1 - rh); Wd[:, ib] -= q_; Wd[:, ic] += q_
    top = np.argsort(-Wd, axis=1)[:, :4]
    W4 = np.take_along_axis(Wd, top, 1); W4 = (W4 / np.maximum(W4.sum(1, keepdims=True), 1e-9)).astype(np.float32)
    J4 = top.astype(np.uint16)
    vieja = _prim(E, "Torso_PIEL")
    ntar = len(vieja.get("targets", []))
    ceros = E._add(np.zeros((len(V), 3), np.float32), "VEC3", None, True)
    nueva = {"attributes": {"POSITION": E._add(V.astype(np.float32), "VEC3", 34962, True),
                            "NORMAL": E._add(N.astype(np.float32), "VEC3", 34962),
                            "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(J4, np.uint16), 5123, "VEC4", 34962),
                            "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
             "indices": v24._add_raw(E, np.ascontiguousarray(F.ravel(), np.uint32), 5125, "SCALAR", 34963),
             "material": vieja["material"], "extras": {"pieza": "Torso_PIEL"}, "targets": [{"POSITION": ceros} for _ in range(ntar)]}
    prims = E.j["meshes"][0]["primitives"]
    E.j["meshes"][0]["primitives"] = [p for p in prims if p is not vieja] + [nueva]
    E.b = bytes(E.out)
    for f in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f)):
            os.remove(os.path.join(carpeta, f))
    return {"operacion": "torso nuevo con anatomía", "tris_marching": int(n0), "tris_torso": int(len(F))}, T0


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    import receta_adan_v37 as v37
    fp0 = v38.FACTOR_PERFIL
    v38.FACTOR_PERFIL = FACTOR_ANTEBRAZO
    v37.PRONACION_V39 = PRONACION
    v38.PLIEGUES = PLIEGUES
    v38.ANCHOS_DEDO = ANCHOS_DEDO
    t38 = dst + ".v38.glb"
    try:
        log = v38.main(src, t38)
    finally:
        v38.FACTOR_PERFIL = fp0
        v37.PRONACION_V39 = None
        v38.PLIEGUES = None
        v38.ANCHOS_DEDO = None
    te = dst + ".esq.glb"
    l2, _ = esqueleto(t38, te)
    log += l2
    E = re.Editor(te)
    carpeta = os.path.dirname(os.path.abspath(dst))
    lt, T0 = torso(E, carpeta)
    log.append(short(E, T0))
    log.append(lt)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V39: proporciones, torso con anatomía, hombros y brazos. SIN APROBAR.")
    # el agarre de la pistola se vuelve a resolver con la mano FINAL (la de V37 se resolvía antes de la muñeca nueva
    # y el pulgar no llegaba a su contacto: 30 mm, con 4 mm de penetración)
    tmp2 = dst + ".agarre.glb"
    log.append({"operacion": "agarre pistola (mano final)", **v37_agarre(tmp, tmp2)})
    compactar(tmp2, dst)
    for f in (t38, te, tmp, tmp2):
        os.remove(f)
    return log


def v37_agarre(glb, salida):
    import receta_adan_v37 as v37
    return v37.agarre_pistola(glb, salida)


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-4:]:
        print(x)
