"""Adán V43 (sobre V42): cadera coherente con el torso y short más chico (parte inferior, etapa 3).

Pedido de Admin (18 oct 2026): "El ancho de la cadera no es coherente de cintura para abajo con el resto del torso.
El bóxer también se ve muy grande." Decisiones: subir el dobladillo, short "solo más chico" (no ajustado), corregir
el volumen de la ropa de una vez. Piernas y pies aprobados: su forma no cambia.

Medidas contra refs/personajes/adan/adan-cuerpo-4-vistas.jpg (vista FRONT, en múltiplos del medio ancho de la
cintura del torso justo arriba del short, W):
                         referencia   V42     V43
  boca del short (arriba)   1.05      1.33    1.05
  entrepierna               1.24      1.42    1.33
  dobladillo                1.30      1.46    1.36
  centro de la pierna       0.72      0.89    0.79
V42 tenía la pretina 31 % más ancha que la cintura (HOLGURA_CINT de la hoja de piernas) y las piernas muy
separadas: el escalón torso → short era la incoherencia. Las piernas de V42 son más gruesas que las de la hoja
(aprobadas así), por eso no se puede llegar al 1.30 del dobladillo sin que asomen.

Qué cambia:
1. Piernas 1 cm más adentro cada una (hueso UpperLeg y toda su cadena). Forma de pierna y pie idéntica a V42.
2. Short nuevo con el mismo código implícito (copox/medicion/short_geo.py):
   - boca 1.05 W, abrazando al torso (sin escalón);
   - dobladillo 2.8 cm más arriba (alto del short −20 %); entrepierna 1 cm más arriba (sigue la proporción de la hoja);
   - fondo 0.6–0.8 cm menos (menos "pompa" de lado).
3. El tobillo queda exactamente donde estaba en V42 (no depende del nuevo dobladillo).
Uso: GODOT_BIN=… python receta_adan_v43.py ADAN_V22_HABLA.glb ADAN_V43.glb
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

DX_PIERNA = 0.010              # u: cada pierna se acerca al centro (centro x 0.088 → 0.078)
Y_DOB = 0.162                  # u: dobladillo (V42: 0.134); alto del short −20 %
Y_ENT = 0.190                  # u: entrepierna (V42: 0.180); 68 % del alto del short desde arriba, como la hoja
BOCA = 1.05                    # medio ancho de la boca ÷ medio ancho del torso en la cintura (hoja del cuerpo)
CADERA = (0.131, 0.084, 0.022)          # medio ancho, medio fondo y centro z en la entrepierna (V42: 0.140, 0.092)
DOBLADILLO = (0.134, 0.082, 0.023)      # en el dobladillo (V42: 0.144, 0.088); la pierna llega a x 0.127
MUESCA = 0.016                          # medio ancho de la muesca en el dobladillo (la pierna empieza en x 0.0295)
FONDO_CINT = 0.004                      # u: la boca es este tanto más profunda que el torso (V41: 0.010)
PIEZAS_PIERNA = v42.PIEZAS_VIEJAS
SHORT = ("Short_AZUL", "Short_PRETINA", "Short_CORDON")


def _cadena(j, raiz):
    hijos = {i: n.get("children", []) for i, n in enumerate(j["nodes"])}
    out, pila = [], [raiz]
    while pila:
        k = pila.pop(); out.append(k); pila += hijos[k]
    return out


def mover_piernas(E, dx=DX_PIERNA):
    """Acerca cada pierna al centro: traslada el hueso UpperLeg (sin rotaciones en reposo), corrige las matrices
    de enlace de toda la cadena y mueve las piezas de pierna viejas, que son la fuente de pesos de la pierna nueva."""
    from copox.medicion.gltf import accesor
    j = E.j; sk = j["skins"][0]
    nombre = {i: n.get("name") for i, n in enumerate(j["nodes"])}
    ibm = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    pos_joint = {k: i for i, k in enumerate(sk["joints"])}
    piezas = {p.get("extras", {}).get("pieza"): p for m in j["meshes"] for p in m["primitives"]}
    for lado, signo in (("Left", 1), ("Right", -1)):
        d = -signo * dx
        raiz = next(i for i, n in nombre.items() if n == lado + "UpperLeg")
        nodo = j["nodes"][raiz]
        assert not nodo.get("rotation"), "UpperLeg con rotación: el corrimiento en x no sería global"
        nodo["translation"][0] += d
        Tm = np.eye(4); Tm[0, 3] = -d
        for k in _cadena(j, raiz):
            if k in pos_joint:
                ibm[pos_joint[k]] = ibm[pos_joint[k]] @ Tm
        for pz in [p for p in PIEZAS_PIERNA if (p.startswith(("PiernaL", "PieL", "CanaL", "SuelaL")) == (lado == "Left"))]:
            p = piezas[pz]
            V = v39._leer(E, p, "POSITION").astype(float); V[:, 0] += d
            p["attributes"]["POSITION"] = E._add(V.astype(np.float32), "VEC3", 34962, True)
    sk["inverseBindMatrices"] = E._add(ibm.transpose(0, 2, 1).reshape(-1, 16).astype(np.float32), "MAT4")
    E.b = bytes(E.out)
    # ninguna otra pieza (salvo el short, que se rehace) puede depender de los huesos de la pierna
    pierna = {pos_joint[k] for lado in ("Left", "Right")
              for k in _cadena(j, next(i for i, n in nombre.items() if n == lado + "UpperLeg")) if k in pos_joint}
    for m in j["meshes"]:
        for p in m["primitives"]:
            pz = p.get("extras", {}).get("pieza")
            if "JOINTS_0" not in p["attributes"] or pz in PIEZAS_PIERNA or pz in SHORT:
                continue
            J = v39._leer(E, p, "JOINTS_0").astype(int); W = v39._leer(E, p, "WEIGHTS_0").astype(float)
            assert (np.isin(J, list(pierna)) * W).sum(1).max() < 1e-4, f"{pz} usa huesos de la pierna"
    return {"operacion": "piernas hacia el centro", "dx": dx}


def short(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import short_geo as sg
    from copox.medicion import torso_geo as tg
    nombres, _ = v40.v38_skin(E)
    viejas = [p for m in E.j["meshes"] for p in m["primitives"] if p.get("extras", {}).get("pieza") in SHORT]
    malla_short = [m for m in E.j["meshes"] if any(p in viejas for p in m["primitives"])][0]
    pret = next(p for p in viejas if p["extras"]["pieza"] == "Short_PRETINA")   # el short vive en su propia malla
    y_top = float(v39._leer(E, pret, "POSITION")[:, 1].max())
    y_cint = y_top - 0.0025                                       # V41 cortaba la boca en y_cint + 0.0025
    T0 = tg.Torso(v39.PERFIL, v39.EXPONENTE)
    a, b, c = [float(np.ravel(v)[0]) for v in T0.seccion(np.array([y_cint]))]
    S = sg.Short(y_cint + 0.0025, Y_ENT, Y_DOB - 0.0025, (a * BOCA, b + FONDO_CINT, c), CADERA, DOBLADILLO, MUESCA,
                 boca=(a + 0.004, b + 0.004, c), alto_boca=0.005)
    V, T = S.malla()
    n0 = len(T)
    V, T = v36.simplificar(V, T, v41.TRIS_SHORT, carpeta)
    vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
    if vol < 0:
        T = T[:, ::-1].copy()
    V, T = sg.recortar(V, T, Y_DOB - 0.0025, y_cint + 0.0025)
    V, T, arriba = sg.partir_plano(V, T, y_cint - v41.PRETINA)
    N = mg.normales(V, T)
    J4, W4 = v41.pesos_short(V, nombres, Y_ENT, y_cint)
    m_short = v41._material(E, "ADAN_SHORT_AZUL", v41.COLOR_SHORT)
    m_pret = v41._material(E, "ADAN_SHORT_PRETINA", v41.COLOR_PRETINA)
    m_cord = v41._material(E, "ADAN_CORDON", v41.COLOR_CORDON)
    prims = []
    for sel, mat, pz in ((~arriba, m_short, "Short_AZUL"), (arriba, m_pret, "Short_PRETINA")):
        Ts = T[sel]; u = np.unique(Ts); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
        Vs = V[u].copy()
        if pz == "Short_PRETINA":
            f = np.clip((Vs[:, 1] - (y_cint - v41.PRETINA)) / 0.003, 0, 1)
            Vs += N[u] * (v41.RESALTE_PRETINA * f)[:, None]
        Ns = mg.normales(Vs, mp[Ts]) if pz == "Short_PRETINA" else N[u]
        prims.append(v41._prim_nueva(E, Vs, mp[Ts], Ns, J4[u], W4[u], mat, pz))
    yk = y_cint - v41.PRETINA * 0.55
    zs = np.linspace(c, c + 0.2, 4001)
    dz = S.sdf(np.stack([np.zeros_like(zs), np.full_like(zs, yk), zs], 1))
    z_frente = float(zs[np.argmax(dz > 0)])
    f, lo, hi = sg.cordon(yk, z_frente + 0.0012)
    Vc, Tc = sg.malla_sdf(f, lo, hi)
    Vc, Tc = v36.simplificar(Vc, Tc, 700, carpeta)
    Nc = mg.normales(Vc, Tc)
    Jc = np.zeros((len(Vc), 4), np.uint16); Jc[:, 0] = nombres.index("Hips")
    Wc = np.zeros((len(Vc), 4), np.float32); Wc[:, 0] = 1
    prims.append(v41._prim_nueva(E, Vc, Tc, Nc, Jc, Wc, m_cord, "Short_CORDON"))
    ntar = max(len(p.get("targets", [])) for p in viejas)
    malla_short["primitives"] = [p for p in malla_short["primitives"] if p not in viejas] + prims
    if ntar:
        for p in prims:
            nv = E.j["accessors"][p["attributes"]["POSITION"]]["count"]
            ceros = E._add(np.zeros((nv, 3), np.float32), "VEC3", None, True)
            p["targets"] = [{"POSITION": ceros} for _ in range(ntar)]
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return {"operacion": "short más chico", "tris_marching": int(n0), "tris_short": int(len(T)),
            "y_cint": round(y_cint, 4), "y_ent": Y_ENT, "y_dob": Y_DOB, "boca": round(a * BOCA, 4)}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    t41 = dst + ".v41.glb"
    # el paso V41 es largo (toda la cadena desde V22): si ya existe el intermedio de un intento anterior, se reusa
    log = [{"operacion": "V41 reusado", "archivo": t41}] if os.path.exists(t41) else v41.main(src, t41)
    E = re.Editor(t41)
    # el tobillo de V42 dependía del dobladillo de V41: se fija antes de cambiar el short
    y_dob41 = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
    y_tobillo = y_dob41 * v42.TOBILLO_FRAC
    log.append(mover_piernas(E))
    log.append(short(E, os.path.dirname(os.path.abspath(dst))))
    y_dob = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
    frac0 = v42.TOBILLO_FRAC
    v42.TOBILLO_FRAC = y_tobillo / y_dob                          # mismo tobillo que V42
    try:
        log.append(v42.piernas(E, os.path.dirname(os.path.abspath(dst))))
    finally:
        v42.TOBILLO_FRAC = frac0
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V43: cadera coherente y short más chico. SIN APROBAR.")
    compactar(tmp, dst)
    for f in (t41, tmp):
        os.remove(f)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-4:]:
        print(x)
