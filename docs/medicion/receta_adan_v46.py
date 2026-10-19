"""Adán V46 (sobre V45): pierna baja y pie como UNA pieza por secciones, siguiendo la hoja de pies.

Pedido de Admin (19 oct 2026), tras la auditoría artística de V45 (peor discrepancia: pie y tobillo): "Detallamos los
pies todavía más". Decisión: solo forma (sin uñas ni arco). Referencia: refs/personajes/adan/adan-pies-4-vistas-captura.jpg.
- Tobillo sin aro: la sección pasa de la de la pierna a la del pie sin unión (copox/medicion/pie_loft.py).
- El tobillo es lo más ancho; el talón sale hacia atrás y se bisela hacia la planta (angosto abajo, como la vista BACK).
- El empeine es una sola diagonal del frente del tobillo a la base de los dedos (vista SIDE).
- Adentro el lado es recto y afuera se abre hacia los dedos; la planta no sobresale (sin aletas).
- Dedos: cuatro, graduados (el gordo más ancho y más alto), puntas en diagonal y un poco caídas.
- La pierna, de la rodilla al tobillo y dentro del short, es la de V42–V45 (aprobada): mismas medidas.
Pesos por altura: muslo sobre la rodilla (rampa 2 cm), pie desde la articulación del tobillo (rampa 1.6 cm), dedos desde la
base de los dedos. Normales de la rejilla (suaves); la planta con las suyas (arista dura).
Uso: python receta_adan_v46.py ADAN_V45.glb ADAN_V46.glb
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

Y_TOBILLO = 0.075                    # pliegue del tobillo: 0.82 × fondo de la pierna (hoja de pies; V45: 0.0589)
PIE = dict(pierna=(0.049, 0.050), tobillo=(0.045, 0.046), p=2.8, talon_z=-0.0216, punta_z=0.150, largo_dedos=0.040,
           alto_dedos=0.022)


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def pesos(V, nombres, lado, H, z_base):
    iU, iL = nombres.index(lado + "UpperLeg"), nombres.index(lado + "LowerLeg")
    iF, iT = nombres.index(lado + "Foot"), nombres.index(lado + "Toes")
    yk, yf = float(H[lado + "LowerLeg"][1]), float(H[lado + "Foot"][1])
    fk = _ss((V[:, 1] - (yk - 0.010)) / 0.020)                      # rodilla: arriba el muslo
    fa = _ss((V[:, 1] - (yf - 0.008)) / 0.016)                      # tobillo: abajo el pie
    ft = _ss((V[:, 2] - (z_base - 0.004)) / 0.008)                  # base de los dedos
    pie = (1 - fk) * (1 - fa)
    W = np.stack([fk * 0.85, fk * 0.15 + (1 - fk) * fa, pie * (1 - ft), pie * ft], 1)
    J = np.tile(np.array([iU, iL, iF, iT], np.uint16), (len(V), 1))
    return J, (W / W.sum(1, keepdims=True)).astype(np.float32)


def _orientar(V, T):
    """Caras hacia afuera: el promedio de normal·(centro de cara − eje de la pieza) debe ser positivo."""
    c = V.mean(0)
    C = V[T].mean(1)
    N = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    d = C - c; d[:, 1] = 0
    return T if np.einsum("ij,ij->i", N, d).sum() >= 0 else T[:, ::-1].copy()


def piernas(E):
    from copox.medicion import mano_geo as mg
    from copox.medicion import pie_loft as pl
    nombres, H = v40.v38_skin(E)
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    y_dob = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
    log = {"operacion": "pierna y pie por secciones"}
    for lado, signo in (("Left", 1), ("Right", -1)):
        p = prims[f"Pierna{lado[0]}_PIEL"]
        xc, zc = float(signo * H[lado + "UpperLeg"][0]), float(H[lado + "UpperLeg"][2])
        y_arriba = float(H[lado + "UpperLeg"][1]) - 0.010
        P = pl.PiernaPieLoft(xc, zc, y_arriba, Y_TOBILLO, y_dob + 0.008, **PIE)
        V, T, planta = P.malla()
        T = _orientar(V, T)
        N = mg.normales(V, T)
        N[planta] = [0, -1, 0]
        Vd, Td = P.dedos_malla()
        partes_d = []
        n0 = 0
        # cada dedo se orienta por separado (son 4 cajas)
        cuantos = len(P.dedos); por = len(Vd) // cuantos
        for i in range(cuantos):
            Vi = Vd[i * por:(i + 1) * por]; Ti = Td[(Td.min(1) >= i * por) & (Td.max(1) < (i + 1) * por)] - i * por
            Ti = _orientar(Vi, Ti)
            partes_d.append((Vi, Ti))
        Vd = np.vstack([v for v, _ in partes_d])
        Td = np.vstack([t + sum(len(v) for v, _ in partes_d[:i]) for i, (_, t) in enumerate(partes_d)])
        Nd = mg.normales(Vd, Td)
        Vt = np.vstack([V, Vd]); Tt = np.vstack([T, Td + len(V)]); Nt = np.vstack([N, Nd])
        J4, W4 = pesos(Vt, nombres, lado, H, P.z_base)
        if signo < 0:
            Vt = Vt * [-1, 1, 1]; Nt = Nt * [-1, 1, 1]; Tt = Tt[:, ::-1].copy()
        nueva = v41._prim_nueva(E, Vt, Tt, Nt, J4, W4, p["material"], f"Pierna{lado[0]}_PIEL")
        if p.get("targets"):
            ceros = E._add(np.zeros((len(Vt), 3), np.float32), "VEC3", None, True)
            nueva["targets"] = [{"POSITION": ceros} for _ in p["targets"]]
        malla = next(m for m in E.j["meshes"] if p in m["primitives"])
        malla["primitives"] = [q if q is not p else nueva for q in malla["primitives"]]
        log[f"tris_{lado[0]}"] = int(len(Tt))
    E.b = bytes(E.out)
    return log


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [piernas(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V46: pierna baja y pie por secciones (hoja de pies). SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
