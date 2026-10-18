"""Adán V38 (sobre V37): antebrazo y muñeca según la referencia del brazo de Adán (refs/personajes/adan/).

Pedido de Admin (18 oct 2026): "Podemos ir empezando a trabajar el antebrazo para editar las muñecas y mantener
coherencia en las uniones". Referencias: adan-brazo-4-vistas.jpg (brazo de frente/lado) y adan-cuerpo-4-vistas.jpg.
Decisiones de Admin: forma "como la Hoja" y codo "seguir la referencia nueva" (sube ~1.5 cm; muñeca y mano fijas).

Qué hace:
  1. V37 con la palma más gruesa en la muñeca (mano_geo grosor_muneca): de frente la mano no cambia.
  2. Codo 1.5 cm hacia el hombro (proporciones `mover_articulacion`): brazo más corto, antebrazo más largo; la muñeca
     y la mano no se mueven (la mano sigue llegando a la entrepierna).
  3. Perfil del antebrazo medido en la referencia (ancho de frente y grueso de lado, de la muñeca al codo), en
     unidades del modelo por la escala largo-de-mano (referencia 440 px = muñeca → punta del medio). Los anillos del
     antebrazo se escalan radialmente con ese perfil, mezclado por el peso de LowerArm (el codo no salta).
  4. Muñeca nueva: se quita la pieza "Antebrazo" (cono que estrangulaba la muñeca) y la mano se regenera con la
     muñeca en la MISMA superficie implícita (mano_geo.muneca): un cilindro elíptico que sale del último anillo del
     antebrazo (su orilla abierta queda dentro de él) y se funde con la palma. Pesos LowerArm → Hand de mano_geo.
     (Intentos descartados: tubo aparte → escalón tipo manga y labio en el borde abierto de la palma.)
Uso: GODOT_BIN=… python receta_adan_v38.py ADAN_V22_HABLA.glb ADAN_V38.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v37 as v37  # noqa: E402

GROSOR_MUNECA = 1.7         # la palma mide ×1.7 de grueso en la muñeca y se adelgaza hacia los nudillos
CODO = -0.015               # u: el codo sube 1.5 cm (hacia el hombro)
# referencia (adan-brazo-4-vistas.jpg, 2400×1792): de la muñeca (x=545) al codo (x=865, u=1) y 200 px más del
# brazo (u=1.625), cada 40 px
REF_ANCHO = [179, 187, 195, 202, 211, 218, 226, 214, 198, 207, 217, 226, 236, 245]     # de frente (palma)
REF_GRUESO = [161, 168, 177, 185, 192, 200, 208, 199, 184, 192, 203, 212, 222, 231]    # de lado
U_MAX = 1.625               # hasta dónde llega la referencia; de ahí al hombro el factor se desvanece
U_FIN = 1.9
REF_MANO_PX = 440                                             # muñeca → punta del dedo medio (sólo informativo)
# Escala absoluta: las dos referencias no coinciden (con la escala del largo de mano, el brazo de la hoja del brazo sale
# ~25 % más delgado que en la hoja del cuerpo). Manda la hoja del CUERPO (mismo encuadre que Adán completo): grosor del
# antebrazo de frente 44 px con envergadura 538 px (adan-cuerpo-4-vistas.jpg, vista FRONT). La hoja del brazo da la FORMA.
REF_CUERPO_ANTEBRAZO_PX, REF_CUERPO_ENVERGADURA_PX = 44, 538
METE_EN_ANTEBRAZO = 0.006   # u: la muñeca empieza dentro del antebrazo (su orilla abierta no se ve)
RADIO_DENTRO = 1.0         # radios de la muñeca = último anillo del antebrazo (0.985 dejaba un escalón visible);
                            # dentro del antebrazo no asoma porque el antebrazo es más grueso hacia el codo
PALMA_DESDE = 0.012         # u: la muñeca llega a la sección de la palma 1.2 cm después de su borde
PUNO_V38 = {"Proximal": 82.0, "Intermediate": 88.0, "Distal": 45.0}   # = V36. Probado 82/80/30 y 78/72/25: los picos del puño NO
# cambian; no son las puntas sino la piel del lado de la palma que se dobla sobre sí misma en los nudillos (pendiente)
MUNECA_RAMPA = 0.006        # u: los pesos llegan a los de la mano 6 mm después de la articulación de la muñeca
TRIS_MANO = 3000            # por mano (V36: 2600; ahora incluye la muñeca)
ANGOSTA_MUNECA = 0.72       # la palma se angosta más hacia la muñeca (referencia: muñeca 53 mm, palma 62)


def _skin(E):
    from copox.medicion.gltf import accesor
    j = E.j; sk = j["skins"][0]
    ibm = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    nombres = [j["nodes"][k]["name"] for k in sk["joints"]]
    H = {n: np.linalg.inv(ibm[i])[:3, 3] for i, n in enumerate(nombres)}
    return nombres, H


def _prim(E, pieza):
    return next(p for p in E.j["meshes"][0]["primitives"] if p.get("extras", {}).get("pieza") == pieza)


def _leer(E, p, attr):
    from copox.medicion.gltf import accesor
    return accesor(E.j, E.b, p["attributes"][attr])


def _perfil(u, tabla):
    return np.interp(np.clip(u, 0, U_MAX), np.linspace(0, U_MAX, len(tabla)), tabla)


def _normales(V, T):
    Nf = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, T[:, i], Nf)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def antebrazo(E, lado):
    """Pasos 3 y 4 para un lado ('Left'/'Right'). Devuelve medidas para el log."""
    from copox.medicion.gltf import accesor
    s = 1.0 if lado == "Left" else -1.0
    L = lado[0]
    nombres, H = _skin(E)
    ie, iw = nombres.index(lado + "LowerArm"), nombres.index(lado + "Hand")
    xe, xw = s * H[lado + "LowerArm"][0], s * H[lado + "Hand"][0]
    yc, zc = H[lado + "LowerArm"][1], H[lado + "LowerArm"][2]
    mano = _leer(E, _prim(E, "Mano" + L), "POSITION").astype(float)
    largo_mano = float((s * mano[:, 0]).max()) - xw
    envergadura = 2 * float((s * mano[:, 0]).max())
    grueso_antebrazo = REF_CUERPO_ANTEBRAZO_PX / REF_CUERPO_ENVERGADURA_PX * envergadura
    k = grueso_antebrazo / _perfil(0.5, REF_GRUESO)    # u por px de la hoja del brazo
    k_mano = largo_mano / REF_MANO_PX
    ancho = lambda u: _perfil(u, REF_ANCHO) * k        # noqa: E731
    grueso = lambda u: _perfil(u, REF_GRUESO) * k      # noqa: E731

    # --- 3. anillos del antebrazo ---------------------------------------------------------------------
    pb = _prim(E, "Brazo" + L)
    V = _leer(E, pb, "POSITION").astype(float)
    J = _leer(E, pb, "JOINTS_0").astype(int); W = _leer(E, pb, "WEIGHTS_0").astype(float)
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
    iu = nombres.index(lado + "UpperArm")
    w_low = (W * ((J == ie) | (J == iw) | (J == iu))).sum(1)
    x = s * V[:, 0]
    anillo = np.round(x / 0.0005).astype(int)
    fy = np.ones(len(V)); fz = np.ones(len(V))
    for a in np.unique(anillo):
        m = anillo == a
        u = (xw - x[m].mean()) / (xw - xe)
        if u > U_FIN:
            continue
        cy = (V[m, 1].max() - V[m, 1].min()) / 2; cz = (V[m, 2].max() - V[m, 2].min()) / 2
        fy[m] = grueso(u) / 2 / cy; fz[m] = ancho(u) / 2 / cz
    uu = (xw - x) / (xw - xe)
    desv = np.clip((U_FIN - uu) / (U_FIN - U_MAX), 0, 1)       # hacia el hombro se desvanece
    fy = 1 + (fy - 1) * w_low * desv; fz = 1 + (fz - 1) * w_low * desv
    V1 = V.copy()
    V1[:, 1] = yc + (V[:, 1] - yc) * fy
    V1[:, 2] = zc + (V[:, 2] - zc) * fz
    Tb = accesor(E.j, E.b, pb["indices"]).reshape(-1, 3).astype(np.int64)
    pb["attributes"]["POSITION"] = E._add(V1.astype(np.float32), "VEC3", 34962, True)
    N1 = _normales(V1, Tb)
    N_orig = _leer(E, pb, "NORMAL").astype(float)       # el orden de las caras de esta pieza puede ir al revés:
    if np.mean(np.einsum("ij,ij->i", N1, N_orig)) < 0:  # las normales nuevas se orientan como las originales
        N1 = -N1
    pb["attributes"]["NORMAL"] = E._add(N1.astype(np.float32), "VEC3", 34962)
    for t in pb.get("targets", []):                     # deltas de morph: misma escala radial
        D = accesor(E.j, E.b, t["POSITION"]).astype(float)
        if np.abs(D).max() > 0:
            D[:, 1] *= fy; D[:, 2] *= fz
            t["POSITION"] = E._add(D.astype(np.float32), "VEC3", None, True)

    # --- 4. último anillo del antebrazo: de ahí sale la muñeca de la mano (mano_geo.muneca) -------------
    ultimo = np.isclose(x, x.max(), atol=0.0006)
    R0 = V1[ultimo]
    x0 = float((s * R0[:, 0]).mean())
    r0y = float(np.abs(R0[:, 1] - yc).max()); r0z = float(np.abs(R0[:, 2] - zc).max())
    return {"lado": lado, "u_por_px": round(float(k), 6), "u_por_px_si_mandara_la_mano": round(float(k_mano), 6),
            "muneca_ref_mm": [round(ancho(0.0) * 1000, 1), round(grueso(0.0) * 1000, 1)],
            "anillo_x": x0, "anillo_c": [float(yc), float(zc)], "anillo_r": [r0y, r0z],
            "antebrazo_fin_mm": [round(r0z * 2000, 1), round(r0y * 2000, 1)]}


def _pesos_muneca(V, J4, W4, nombres, x_anillo, x_muneca):
    """Donde la mano sale del antebrazo los pesos son del antebrazo y pasan a los de la mano en rampa suave hasta
    MUNECA_RAMPA después de la articulación: la orilla escondida no se asoma al girar la mano."""
    ia = nombres.index("LeftLowerArm")
    f = np.clip((V[:, 0] - x_anillo) / (x_muneca + MUNECA_RAMPA - x_anillo), 0, 1)
    f = f * f * (3 - 2 * f)
    n = len(V)
    W = np.zeros((n, len(nombres)))
    np.add.at(W, (np.repeat(np.arange(n), 4), J4.ravel().astype(int)), W4.ravel())
    W *= f[:, None]; W[:, ia] += 1 - f
    top = np.argsort(-W, axis=1)[:, :4]
    Wt = np.take_along_axis(W, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
    return top.astype(np.uint16), Wt.astype(np.float32)


def mano_con_muneca(E, D, nombres, anillo, carpeta):
    """Regenera la mano (izquierda + espejo) con la muñeca en la misma superficie implícita: un cilindro elíptico del
    último anillo del antebrazo (radios ×RADIO_DENTRO, la orilla abierta queda dentro del antebrazo) a la sección de
    la palma. Quita la pieza vieja de la muñeca (cono "Antebrazo")."""
    import receta_adan_v36 as v36
    import receta_adan_v27 as v27
    import receta_adan_v24 as v24
    from copox.medicion import mano_geo as mg
    _, H = _skin(E)
    D.H["LeftLowerArm"] = H["LeftLowerArm"]              # el codo se movió: rampa de pesos antebrazo → mano
    cz = (D.palma_z[0] + D.palma_z[1]) / 2; hz = (D.palma_z[1] - D.palma_z[0]) / 2
    g = D.grosor / 2 * (D.grosor_muneca or 1.0)
    D.muneca = {"x0": anillo["anillo_x"] - METE_EN_ANTEBRAZO, "x1": D.palma_x0 + PALMA_DESDE,
                "c0": anillo["anillo_c"], "r0": [anillo["anillo_r"][0] * RADIO_DENTRO, anillo["anillo_r"][1] * RADIO_DENTRO],
                "c1": [D.palma_y + (g - D.grosor / 2), cz], "r1": [g * 0.92, hz * D.angosta * 0.92]}
    V, T = D.malla()
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS_MANO, carpeta)
    # caras hacia AFUERA (glTF: antihorario visto desde afuera). Desde V36 la mano salía al revés y dependía del
    # material de dos caras (en Godot dejaba un anillo claro en la muñeca). Volumen con signo < 0 → se voltea.
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum()) / 6
    if vol < 0:
        T = T[:, ::-1].copy()
    N = mg.normales(V, T)
    J4, W4 = mg.pesos(V, T, D, nombres, v27.pesos_cadena)
    J4, W4 = _pesos_muneca(V, J4, W4, nombres, anillo["anillo_x"], float(D.H["LeftHand"][0]))
    prims = E.j["meshes"][0]["primitives"]
    vieja = _prim(E, "ManoL")
    mat = vieja["material"]; ntar = len(vieja.get("targets", []))
    nuevas = []
    for lado, (VV, TT, NN, JJ) in (("L", (V, T, N, J4)), ("R", mg.espejo(V, T, N, J4, nombres))):
        ceros = E._add(np.zeros((len(VV), 3), np.float32), "VEC3", None, True)
        nuevas.append({"attributes": {"POSITION": E._add(VV.astype(np.float32), "VEC3", 34962, True),
                                      "NORMAL": E._add(NN.astype(np.float32), "VEC3", 34962),
                                      "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(JJ, np.uint16), 5123, "VEC4", 34962),
                                      "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)},
                       "indices": v24._add_raw(E, np.ascontiguousarray(TT.ravel(), np.uint32), 5125, "SCALAR", 34963),
                       "material": mat, "extras": {"pieza": "Mano" + lado}, "targets": [{"POSITION": ceros} for _ in range(ntar)]})
    quitar = {"ManoL", "ManoR", "AntebrazoL", "AntebrazoR"}
    E.j["meshes"][0]["primitives"] = [p for p in prims if p.get("extras", {}).get("pieza") not in quitar] + nuevas
    E.b = bytes(E.out)
    for f in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f)):
            os.remove(os.path.join(carpeta, f))
    return {"operacion": "mano con muñeca en la misma superficie", "tris_marching": int(n0), "tris_mano": int(len(T)),
            "muneca": {k: (np.round(v, 5).tolist() if not isinstance(v, float) else round(v, 5)) for k, v in D.muneca.items()}}


def costura_normales(E):
    """El último anillo del antebrazo toma la normal de la mano en ese punto: sin línea de luz en la costura."""
    from copox.medicion.gltf import accesor
    from scipy.spatial import cKDTree
    n_tot = 0
    for L in "LR":
        pb, pm = _prim(E, "Brazo" + L), _prim(E, "Mano" + L)
        V = _leer(E, pb, "POSITION").astype(float); N = _leer(E, pb, "NORMAL").astype(float)
        Vm = _leer(E, pm, "POSITION").astype(float); Nm = _leer(E, pm, "NORMAL").astype(float)
        x = np.abs(V[:, 0]); borde = np.isclose(x, x.max(), atol=0.0006)
        # normal de la mano en la orilla visible: vértices de la mano a ≤3 mm por fuera del borde
        xm = np.abs(Vm[:, 0]); cerca = (xm > x.max()) & (xm < x.max() + 0.004)
        kd = cKDTree(Vm[cerca][:, 1:]); _, i = kd.query(V[borde][:, 1:])
        Nn = Nm[cerca][i]
        # por si acaso: la normal se orienta como la del antebrazo (hacia afuera)
        Nn = np.where((np.einsum("ij,ij->i", Nn, N[borde]) < 0)[:, None], -Nn, Nn)
        Nn[:, 0] = N[borde][:, 0]
        N[borde] = Nn / np.linalg.norm(Nn, axis=1, keepdims=True)
        pb["attributes"]["NORMAL"] = E._add(N.astype(np.float32), "VEC3", 34962)
        n_tot += int(borde.sum())
    E.b = bytes(E.out)
    return {"operacion": "costura antebrazo–mano: normales", "vertices": n_tot}


def main(src, dst):
    from copox.medicion import proporciones
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    import receta_adan_v36 as v36
    v37.DISENO_EXTRA_V38 = {"grosor_muneca": GROSOR_MUNECA, "angosta_muneca": ANGOSTA_MUNECA}
    puno0 = dict(v36.PUNO_V36); v36.PUNO_V36.update(PUNO_V38)
    t37 = dst + ".v37.glb"
    guardado = {}
    diseno0 = v36.diseno

    def diseno_y_guardar(E_):
        r_ = diseno0(E_); guardado["D"] = r_
        return r_
    v36.diseno = diseno_y_guardar
    try:
        log = v37.main(src, t37)
    finally:
        v37.DISENO_EXTRA_V38 = {}; v36.diseno = diseno0; v36.PUNO_V36.clear(); v36.PUNO_V36.update(puno0)
    D, nombres = guardado["D"]
    t38 = dst + ".codo.glb"
    r = proporciones.editar(t37, t38, [{"tipo": "mover_articulacion", "hueso": f"{l}LowerArm", "delta": CODO}
                                       for l in ("Left", "Right")], nota="V38: codo hacia el hombro")
    log.append({"operacion": "codo", **{k: v for k, v in r.items() if k != "huesos_movidos"}})
    E = re.Editor(t38)
    anillos = {}
    for lado in ("Left", "Right"):
        anillos[lado] = antebrazo(E, lado)
        log.append({"operacion": "antebrazo", **{k: v for k, v in anillos[lado].items() if not k.startswith("anillo")}})
    log.append(mano_con_muneca(E, D, nombres, anillos["Left"], os.path.dirname(os.path.abspath(dst))))
    log.append(costura_normales(E))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V38: antebrazo y muñeca según la referencia del brazo. SIN APROBAR.")
    compactar(tmp, dst)
    for f in (t37, t38, tmp):
        os.remove(f)
    return log


if __name__ == "__main__":
    if len(sys.argv) > 3:                 # experimentos: PUNO proximal,intermedia,distal
        PUNO_V38.update(zip(("Proximal", "Intermediate", "Distal"), map(float, sys.argv[3].split(","))))
    for x in main(sys.argv[1], sys.argv[2])[-3:]:
        print(x)
