"""Adán V45 (sobre V44): "liso y plano" — nuca sin hueco ni bulto, brazos de una pieza, manos recosidas, pies.

Pedido de Admin (18 oct 2026): "Suavizado general. Queremos que no haya bultos… todo liso y plano. Tampoco queremos
huecos. Veo un bulto en la nuca y hoyos en los brazos. Corrige lo necesario de brazos y manos… dale una pasada a los
pies. Prioriza likeness con las referencias de Adán renderizado." Pies: forma de la hoja de pies, tamaño de la del cuerpo.
Mano de empuñar: después.

1. Nuca (copox/medicion/pelo_nuca.py): la franja baja del pelo baja hasta 2.4 cm en el centro de la nuca y se acuesta
   sobre la piel: se cierra la rendija por la que se veía el interior de la boca (Godot: línea rojiza) y se tapa la
   bola de piel bajo el pelo (en la hoja el pelo llega casi al cuello). Cara y gestos sin tocar.
2. Brazos (copox/medicion/brazo_geo.py): superficie continua de sección caja redondeada, mismo tamaño que V44 pero
   sin el relieve viejo (bulto de bíceps y de antebrazo) y con el codo limitado a un estrechamiento leve.
3. Manos: las de V44 (mismo estilo y poses), recosidas al anillo nuevo de la muñeca.
4. Pies: ver PIES abajo.
Uso: GODOT_BIN=… python receta_adan_v45.py ADAN_V44.glb ADAN_V45.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v41 as v41  # noqa: E402
import receta_adan_v42 as v42  # noqa: E402
import receta_adan_v44 as v44  # noqa: E402

NUCA = dict(delta=0.024, banda=0.020, ancho_th=75.0, holgura=0.0006)
BRAZO = dict(sigma=0.012, codo_max=0.03, p=2.6)
TRIS_BRAZO = 3500             # el barrido sigue 1 cm más allá de cada boca: parte del presupuesto se corta
HUECO_ANILLO = 0.0007          # u: ningún vértice a menos de esto del plano de la muñeca (el anillo queda limpio)


def _prims(E):
    return {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}


def _malla(E, p):
    from copox.medicion.gltf import accesor
    return v39._leer(E, p, "POSITION").astype(float), accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)


def nuca(E):
    from copox.medicion import mano_geo as mg
    from copox.medicion import pelo_nuca as pn
    P = _prims(E)
    piel = _malla(E, P["Cabeza_PIEL_EXPUESTA_v04"])
    Vr, Tr = _malla(E, P["GUIA_CAPILAR_RELLENO_RUBIO_v04"])
    _, inv = np.unique(np.round(Vr, 5), axis=0, return_inverse=True); inv = inv.ravel(); Tw = inv[Tr]
    e = np.sort(np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    borde_y = pn.borde_por_angulo(Vr[np.isin(inv, np.unique(u[c == 1]))])
    log = {"operacion": "nuca"}
    for pz in ("GUIA_CAPILAR_RELLENO_RUBIO_v04", "GUIA_CAPILAR_CONTORNO_RUBIO_v04"):
        p = P[pz]
        V, T = _malla(E, p)
        off = None
        if "CONTORNO" in pz:
            Q, _ = pn.mas_cercano(V, Vr, Tr)
            off = np.linalg.norm(V - Q, axis=1)
        V2, mov = pn.mover(V, (Vr, Tr), piel, borde_y, off=off, **NUCA)
        N = v39._leer(E, p, "NORMAL").astype(float)
        N[mov] = mg.normales(V2, T)[mov]
        p["attributes"]["POSITION"] = E._add(V2.astype(np.float32), "VEC3", 34962, True)
        p["attributes"]["NORMAL"] = E._add(N.astype(np.float32), "VEC3", 34962)
        log[pz[:20]] = int(mov.sum())
    E.b = bytes(E.out)
    return log


def _normales_sdf(B, V, h=0.0004):
    """Normales del gradiente del campo del brazo, lejos de las tapas (en las bocas el campo es el del barrido)."""
    P = V.copy()
    P[:, 0] = np.clip(P[:, 0], B.x0 + 0.003, B.x1 - 0.003)
    g = np.zeros_like(P)
    for i in range(3):
        d = np.zeros(3); d[i] = h
        g[:, i] = B.sdf(P + d) - B.sdf(P - d)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


def brazos(E, carpeta):
    import receta_adan_v24 as v24
    import receta_adan_v36 as v36
    from copox.medicion import brazo_geo as bg
    from copox.medicion import mano_bloques as mb
    from copox.medicion import mano_geo as mg
    from copox.medicion import torso_geo as tg
    nombres, H = v40.v38_skin(E)
    P = _prims(E)
    log = {"operacion": "brazos de una pieza"}
    for lado in ("Left", "Right"):
        s = 1.0 if lado == "Left" else -1.0
        p = P["Brazo" + lado[0]]
        V, T = _malla(E, p)
        J = v39._leer(E, p, "JOINTS_0").astype(int); W = v39._leer(E, p, "WEIGHTS_0").astype(float)
        Vl = V * [s, 1, 1]
        x0, x1 = float(Vl[:, 0].min()), float(Vl[:, 0].max())
        B = bg.Brazo(Vl, T, x0, x1, codo_x=float(s * H[lado + "LowerArm"][0]), **BRAZO)
        Vn, Tn = B.malla()
        Vn, Tn = v36.simplificar(Vn, Tn, TRIS_BRAZO, carpeta)
        vol = float(np.einsum("ij,ij->i", Vn[Tn[:, 0]], np.cross(Vn[Tn[:, 1]], Vn[Tn[:, 2]])).sum())
        if vol < 0:
            Tn = Tn[:, ::-1].copy()
        Vn, Tn = mb.cortar(Vn, Tn, x0 + 0.0005)                                  # boca del hombro (dentro del torso)
        Vf, Tn = mb.cortar(Vn * [-1, 1, 1], Tn, -x1)                             # boca de la muñeca: plano exacto
        Vn = Vf * [-1, 1, 1]
        cerca = (Vn[:, 0] < x1 - 1e-7) & (Vn[:, 0] > x1 - HUECO_ANILLO)
        Vn[cerca, 0] = x1 - HUECO_ANILLO
        Vn[np.abs(Vn[:, 0] - x1) < 1e-7, 0] = x1
        N = _normales_sdf(B, Vn)          # del gradiente: lisas y sin sesgo en el anillo (la mano copia estas)
        J4, W4 = tg.transferir_pesos(Vn, Tn, [(Vl, J, W)], len(nombres), suavizado=6)
        if lado == "Right":
            Vn = Vn * [-1, 1, 1]; N = N * [-1, 1, 1]; Tn = Tn[:, ::-1].copy()
        p["attributes"] = {"POSITION": E._add(Vn.astype(np.float32), "VEC3", 34962, True),
                           "NORMAL": E._add(N.astype(np.float32), "VEC3", 34962),
                           "JOINTS_0": v24._add_raw(E, np.ascontiguousarray(J4, np.uint16), 5123, "VEC4", 34962),
                           "WEIGHTS_0": v24._add_raw(E, np.ascontiguousarray(W4, np.float32), 5126, "VEC4", 34962)}
        p["indices"] = v24._add_raw(E, np.ascontiguousarray(Tn.ravel(), np.uint32), 5125, "SCALAR", 34963)
        if p.get("targets"):
            ceros = E._add(np.zeros((len(Vn), 3), np.float32), "VEC3", None, True)
            p["targets"] = [{"POSITION": ceros} for _ in p["targets"]]
        log[f"tris_{lado[0]}"] = int(len(Tn))
        log[f"perfil_{lado[0]}"] = B.perfil()
    E.b = bytes(E.out)
    return log


def manos(E, carpeta):
    """Las manos de V44 (mismo estilo y poses) cosidas al anillo nuevo de la muñeca."""
    j = E.j
    nombres, _ = v40.v38_skin(E)
    poses = v44._poses()
    log = []
    for variante in v40.MANOS:
        for lado in ("Left", "Right"):
            malla = next(m for m in j["meshes"] if m.get("name") == f"MANO_{variante.upper()}_{lado[0]}")
            viejo = malla["primitives"][0]
            prim, info = v44.mano(E, variante, lado, nombres, carpeta, poses)
            prim["material"] = viejo["material"]
            if "extras" in viejo:
                prim["extras"] = viejo["extras"]
            malla["primitives"] = [prim]
            log.append(info)
    E.b = bytes(E.out)
    return {"operacion": "manos recosidas", "tris": [x["tris"] for x in log]}


# Pies: la pierna queda como V42–V44 (aprobada por Admin; una pierna más cónica dejaba rayas al sombrear y al
# moverse). Sólo cambia el pie, hacia la hoja de pies: talón que se abre más (campana), pie un poco más abierto afuera,
# dedos más delgados y separados, con las puntas en diagonal hacia afuera y la punta un poco caída. Tamaño de la hoja
# del cuerpo (largo de pie y tobillo de V42–V44, que ya coincidían).
PIES = {**v42.PARAMS, "alto_dedos": 0.022, "largo_dedos": 0.040, "hueco": 0.0032, "abre": 0.009, "abre_talon": 0.009,
        "escalon": 0.007, "caida": 0.3}
# Probado tras la revisión (aro en el tobillo): empeine a la altura del pliegue con unión 0.0015 → el aro se marca más;
# unión 0.014 → rayas en la pierna. Se queda la unión de V42 (0.005); el tobillo pide otra técnica (pendiente).


def pies(E, carpeta):
    """Igual que receta_adan_v42.piernas (pesos, simplificado, tobillo de V43), con el pie nuevo."""
    p0 = dict(v42.PARAMS)
    v42.PARAMS.clear(); v42.PARAMS.update(PIES)
    try:
        y_dob = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
        frac0 = v42.TOBILLO_FRAC
        v42.TOBILLO_FRAC = 0.0589 / y_dob                       # mismo tobillo que V43–V44
        P = _prims(E)
        viejas = [P[f"Pierna{l}_PIEL"] for l in "LR"]
        log = _piernas_desde(E, carpeta, viejas)
    finally:
        v42.PARAMS.clear(); v42.PARAMS.update(p0)
        v42.TOBILLO_FRAC = frac0
    return log


def _piernas_desde(E, carpeta, viejas):
    """v42.piernas, pero tomando como fuente de pesos las piernas actuales (las piezas viejas ya no existen)."""
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import pie_geo as pg
    from copox.medicion import torso_geo as tg
    nombres, H = v40.v38_skin(E)
    malla = next(m for m in E.j["meshes"] if any(p in viejas for p in m["primitives"]))
    y_dob = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
    y_arriba = float(H["LeftUpperLeg"][1]) - 0.010
    x, z = float(H["LeftUpperLeg"][0]), float(H["LeftUpperLeg"][2])
    PP = pg.PiernaPie(x, z, y_arriba, y_tobillo=y_dob * v42.TOBILLO_FRAC, y_oculta=y_dob + 0.008, **v42.PARAMS)
    V, T = PP.malla()
    fuentes = [(v39._leer(E, q, "POSITION").astype(float), v39._leer(E, q, "JOINTS_0").astype(int),
                v39._leer(E, q, "WEIGHTS_0").astype(float)) for q in viejas]
    mat = viejas[0]["material"]
    ntar = len(viejas[0].get("targets", []))
    prims, log = [], {"operacion": "pies"}
    for lado, signo in (("L", 1), ("R", -1)):
        cara = (V[T].mean(1)[:, 0] * signo) > 0
        Ts = T[cara]; u = np.unique(Ts); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
        Vs, Ts = V[u].copy(), mp[Ts]
        Vs, Ts = v36.simplificar(Vs, Ts, v42.TRIS_PIERNA, carpeta)
        vol = float(np.einsum("ij,ij->i", Vs[Ts[:, 0]], np.cross(Vs[Ts[:, 1]], Vs[Ts[:, 2]])).sum())
        if vol < 0:
            Ts = Ts[:, ::-1].copy()
        Vs[Vs[:, 1] < 0.0015, 1] = 0.0
        N = mg.normales(Vs, Ts)
        J4, W4 = tg.transferir_pesos(Vs, Ts, fuentes, len(nombres), suavizado=6)
        J4, W4 = v42._muslo(Vs, J4, W4, nombres, lado, float(H["LeftLowerLeg"][1]))
        p = v41._prim_nueva(E, Vs, Ts, N, J4, W4, mat, f"Pierna{lado}_PIEL")
        if ntar:
            ceros = E._add(np.zeros((len(Vs), 3), np.float32), "VEC3", None, True)
            p["targets"] = [{"POSITION": ceros} for _ in range(ntar)]
        prims.append(p)
        log[f"tris_{lado}"] = int(len(Ts))
    malla["primitives"] = [p for p in malla["primitives"] if p not in viejas] + prims
    E.b = bytes(E.out)
    return log


PASOS = ("nuca", "brazos", "manos", "pies")


def main(src, dst, pasos=PASOS):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    carpeta = os.path.dirname(os.path.abspath(dst))
    log = []
    for paso in pasos:
        f = globals()[paso]
        log.append(f(E, carpeta) if paso != "nuca" else f(E))
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V45: liso y plano (nuca, brazos, manos, pies). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print({k: v for k, v in x.items() if not k.startswith("perfil")})
