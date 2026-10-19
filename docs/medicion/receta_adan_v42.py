"""Adán V42 (sobre V41): piernas desde la cadera y pies de bloques como la hoja de pies (parte inferior, etapa 2).

Pedido de Admin (18 oct 2026): "Sigue con piernas desde cadera y pies".
Medidas con el dobladillo del short como regla (hoja del cuerpo, vista de frente; el short ya coincide con la hoja):
la pierna mide de ancho 0.35 del short en el dobladillo (igual que V41) y el pliegue del tobillo queda al 44 % de la
altura del dobladillo; en la hoja de pies el pie mide 1.8 veces el fondo de la pierna y lleva cuatro dedos separados.
Uso: GODOT_BIN=… python receta_adan_v42.py ADAN_V22_HABLA.glb ADAN_V42.glb
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

PIEZAS_VIEJAS = ("PiernaL_PIEL", "PiernaR_PIEL", "PieL", "PieR", "CanaL", "CanaR", "SuelaL", "SuelaR")
TOBILLO_FRAC = 0.44           # alto del pliegue del tobillo ÷ alto del dobladillo (hoja del cuerpo, frente)
TRIS_PIERNA = 3200            # por pierna
PARAMS = dict(pierna=(0.049, 0.050), tobillo=(0.045, 0.046), talon_z=-0.032, punta_z=0.150, ancho_pie=0.052,
              alto_talon=0.062, alto_dedos=0.026, largo_dedos=0.036)


def _muslo(V, J4, W4, nombres, lado, y_rodilla, rampa=0.020):
    """Sobre la rodilla la pierna es del muslo (las piezas viejas no llegaban ahí): rampa de `rampa` en la rodilla."""
    lad = "Left" if lado == "L" else "Right"
    ia, ib = nombres.index(lad + "UpperLeg"), nombres.index(lad + "LowerLeg")
    f = np.clip((V[:, 1] - (y_rodilla - rampa / 2)) / rampa, 0, 1); f = f * f * (3 - 2 * f)
    Wd = np.zeros((len(V), len(nombres)))
    np.add.at(Wd, (np.repeat(np.arange(len(V)), 4), J4.ravel().astype(int)), W4.ravel())
    Wd *= (1 - f)[:, None]
    Wd[:, ia] += f * 0.85; Wd[:, ib] += f * 0.15
    top = np.argsort(-Wd, axis=1)[:, :4]
    Wt = np.take_along_axis(Wd, top, 1); Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
    return top.astype(np.uint16), Wt.astype(np.float32)


def piernas(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import pie_geo as pg
    from copox.medicion import torso_geo as tg
    nombres, H = v40.v38_skin(E)
    malla = E.j["meshes"][0]
    viejas = [p for p in malla["primitives"] if p.get("extras", {}).get("pieza") in PIEZAS_VIEJAS]
    y_dob = float(min(v39._leer(E, q, "POSITION")[:, 1].min() for q in v39._prims(E, "Short_AZUL")))
    y_arriba = float(H["LeftUpperLeg"][1]) - 0.010                 # la pierna sube dentro del short hasta la cadera
    x, z = float(H["LeftUpperLeg"][0]), float(H["LeftUpperLeg"][2])
    PP = pg.PiernaPie(x, z, y_arriba, y_tobillo=y_dob * TOBILLO_FRAC, y_oculta=y_dob + 0.008, **PARAMS)
    V, T = PP.malla()
    n0 = len(T)
    fuentes = [(v39._leer(E, q, "POSITION").astype(float), v39._leer(E, q, "JOINTS_0").astype(int),
                v39._leer(E, q, "WEIGHTS_0").astype(float)) for q in viejas]
    mat = v39._prim(E, "PiernaL_PIEL")["material"]
    ntar = len(viejas[0].get("targets", []))
    prims, log = [], {}
    for lado, signo in (("L", 1), ("R", -1)):
        # cada pierna aparte (no se tocan): la del lado y su malla simplificada
        cara = (V[T].mean(1)[:, 0] * signo) > 0
        Ts = T[cara]; u = np.unique(Ts); mp = -np.ones(len(V), int); mp[u] = np.arange(len(u))
        Vs, Ts = V[u].copy(), mp[Ts]
        Vs, Ts = v36.simplificar(Vs, Ts, TRIS_PIERNA, carpeta)
        vol = float(np.einsum("ij,ij->i", Vs[Ts[:, 0]], np.cross(Vs[Ts[:, 1]], Vs[Ts[:, 2]])).sum())
        if vol < 0:
            Ts = Ts[:, ::-1].copy()
        Vs[Vs[:, 1] < 0.0015, 1] = 0.0
        N = mg.normales(Vs, Ts)
        J4, W4 = tg.transferir_pesos(Vs, Ts, fuentes, len(nombres), suavizado=6)
        J4, W4 = _muslo(Vs, J4, W4, nombres, lado, float(H["LeftLowerLeg"][1]))
        p = v41._prim_nueva(E, Vs, Ts, N, J4, W4, mat, f"Pierna{lado}_PIEL")
        if ntar:
            ceros = E._add(np.zeros((len(Vs), 3), np.float32), "VEC3", None, True)
            p["targets"] = [{"POSITION": ceros} for _ in range(ntar)]
        prims.append(p)
        log[f"tris_{lado}"] = int(len(Ts))
    malla["primitives"] = [p for p in malla["primitives"] if p not in viejas] + prims
    E.b = bytes(E.out)
    for f_ in ("V.npy", "T.npy", "malla.json", "lod.json"):
        if os.path.exists(os.path.join(carpeta, f_)):
            os.remove(os.path.join(carpeta, f_))
    return {"operacion": "piernas y pies de bloques", "tris_marching": int(n0), **log,
            "y_tobillo": round(y_dob * TOBILLO_FRAC, 4), "y_arriba": round(y_arriba, 4)}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    t41 = dst + ".v41.glb"
    log = v41.main(src, t41)
    E = re.Editor(t41)
    log.append(piernas(E, os.path.dirname(os.path.abspath(dst))))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V42: piernas y pies de bloques. SIN APROBAR.")
    compactar(tmp, dst)
    for f in (t41, tmp):
        os.remove(f)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2])[-3:]:
        print(x)
