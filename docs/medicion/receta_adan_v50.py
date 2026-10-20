"""Adán V50 = Adán V49 (con el pelo de Theo aprobado) + pelvis anatómica + pie con zapato (reemplaza los tenis).

Admin (19 oct 2026): "Trabajemos la cadera/pelvis. Investiga modelos anatómicos y haz una pieza similar que sea
orgánica … coherente con el resto del cuerpo" y "toma los zapatos de Theo para mejorar las piezas de los pies"
(los zapatos reemplazan a los tenis). Briefs: docs/investigacion/pelvis.md, docs/investigacion/zapato.md.

Pelvis (Proko, Anatomy of the Pelvis → simplificación ALTH):
- cubeta: corte superelíptico, más ancha que profunda, inclinada hacia adelante (la parte alta va adelante);
- línea inguinal: surco suave de la espina ilíaca anterior (EIAS) al pubis → la "V" de la ingle, solo al frente;
- glúteos: dos masas atrás con su pliegue inferior; separación central suave;
- trocánter: plano lateral donde entra el muslo; la pelvis ENVUELVE la tapa de la pierna (sin aro).
Uso: GODOT_BIN=… python receta_adan_v50.py ADAN_V49_PELO_THEO.glb ADAN_V50.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v41 as v41  # noqa: E402
import receta_adan_v49 as v49  # noqa: E402

PELVIS = dict(
    y_top=0.292, y_troc=0.214, y_pubis=0.196, y_bot=0.184,       # alturas (u del GLB)
    ancho_top=0.086, ancho_troc=0.122, ancho_bot=0.014,           # medio ancho
    fondo_top=0.058, fondo_troc=0.060, fondo_bot=0.030,           # medio fondo
    zc=0.020, inclinacion=12.0, n=2.6,                             # centro z, grados hacia adelante, superelipse
    asis=(0.084, 0.272), surco_prof=0.0042, surco_ancho=0.0085,    # línea inguinal
    gluteo=dict(x=0.040, y=0.218, z=-0.024, r=(0.044, 0.040, 0.022), pliegue_y=0.188, pliegue_prof=0.0018),
    k_cuerpo=0.020, k_gluteo=0.012, arriba=0.318, abajo=0.150, hundir=0.0022, costura=0.172, costura_torso=0.300, k_union=0.010)
MUSLO = dict(x=0.078, z=0.024, rx=0.047, rz=0.048, n=3.0, y0=0.10, y1=0.30)   # medido en la pierna de V49 (y 0.15–0.17)
TRIS = dict(pelvis=3600)


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _lerp3(y, ys, vs):
    return np.interp(y, ys, vs)


class PelvisAnatomica:
    def __init__(self, torso, pl, pr_):
        from copox.medicion import ropa_ajustada as ra
        self.ra, self.piezas = ra, [torso, pl, pr_]

    def cubeta(self, P):
        c = PELVIS
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        ys = [c["y_bot"], c["y_pubis"], c["y_troc"], c["y_top"]]
        w = _lerp3(y, ys, [c["ancho_bot"], c["ancho_troc"] * 0.62, c["ancho_troc"], c["ancho_top"]])
        dz = _lerp3(y, ys, [c["fondo_bot"], c["fondo_troc"] * 0.85, c["fondo_troc"], c["fondo_top"]])
        zc = c["zc"] + (y - c["y_troc"]) * np.tan(np.radians(c["inclinacion"]))   # la parte alta va hacia adelante
        n = c["n"]
        k = ((np.abs(x) / w) ** n + (np.abs(z - zc) / dz) ** n) ** (1 / n)
        d = (k - 1) * np.minimum(w, dz)
        return -self.ra.smin(-d, -((c["y_bot"] - 0.004) - y), 0.010)              # fondo redondo en la entrepierna

    def surco_inguinal(self, P):
        """Profundidad del surco (≥ 0) a lo largo de la recta EIAS → pubis, solo al frente."""
        c = PELVIS
        ax, ay = c["asis"]
        x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
        a = np.array([ax, ay]); b = np.array([0.016, c["y_pubis"] + 0.004])
        ab = b - a
        q = np.stack([x, y], 1) - a
        t = np.clip(q @ ab / (ab @ ab), 0, 1)
        dist = np.linalg.norm(q - t[:, None] * ab, axis=1)
        frente = _ss((z - (c["zc"] + 0.015)) / 0.02)
        extremos = np.sin(np.pi * np.clip(t, 0, 1)) ** 0.5
        return c["surco_prof"] * np.exp(-(dist / c["surco_ancho"]) ** 2) * frente * extremos

    def gluteos(self, P):
        g = PELVIS["gluteo"]
        r = np.array(g["r"])
        d = None
        for s in (1, -1):
            Q = P - np.array([s * g["x"], g["y"], g["z"]])
            k0 = np.linalg.norm(Q / r, axis=1)
            k1 = np.linalg.norm(Q / (r * r), axis=1)
            e = k0 * (k0 - 1) / np.maximum(k1, 1e-12)
            d = e if d is None else self.ra.smin(d, e, 0.006)
        # pliegue inferior: surco horizontal atrás donde el glúteo se junta con el muslo
        atras = _ss((-(P[:, 2]) - 0.0) / 0.02)
        pl = g["pliegue_prof"] * np.exp(-((P[:, 1] - g["pliegue_y"]) / 0.006) ** 2) * atras * _ss((0.075 - np.abs(P[:, 0])) / 0.02)
        return d, pl

    def muslos(self, P):
        m = MUSLO
        d = None
        for s in (1, -1):
            qx = np.abs(P[:, 0] - s * m["x"]) / m["rx"]; qz = np.abs(P[:, 2] - m["z"]) / m["rz"]
            k = (qx ** m["n"] + qz ** m["n"]) ** (1 / m["n"])
            e = (k - 1) * min(m["rx"], m["rz"])
            e = np.maximum(e, np.maximum(P[:, 1] - m["y1"], m["y0"] - P[:, 1]))
            # por fuera el muslo se angosta hacia la cintura (contorno continuo, sin aleta sobre la cadera)
            xo = np.interp(P[:, 1], [0.195, 0.29], [m["x"] + m["rx"], 0.098])
            e = np.maximum(e, s * P[:, 0] - xo)
            d = e if d is None else np.minimum(d, e)
        return d

    def linea_v(self, x):
        """Altura de la línea inguinal por |x| (ref. de Admin, refs/infografias/cadera-ejemplo-admin.jpg): del pubis al
        centro sube en diagonal hasta la espina ilíaca y, por fuera, sigue hasta la cintura (contorno continuo)."""
        c = PELVIS
        ax, ay = c["asis"]
        x = np.abs(x)
        y_in = c["y_pubis"] + (ay - c["y_pubis"]) * np.clip(x / ax, 0, 1)
        return np.where(x <= ax, y_in, ay + (x - ax) * 2.5)

    def sdf(self, P):
        """Torso que baja + muslos que suben, con la frontera en la V inguinal (al frente) y en el pliegue del glúteo
        (atrás). Sin cubeta que abulte: la pelvis es donde se encuentran; la unión suave pequeña deja el surco."""
        c = PELVIS
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        frente = _ss((z - (c["zc"] - 0.005)) / 0.03)                      # 1 al frente, 0 atrás
        lv = self.linea_v(x)
        g = c["gluteo"]
        frontera = frente * lv + (1 - frente) * g["pliegue_y"]
        # torso: su corte se extruye hacia abajo y se cierra bajo la frontera
        Pt = P.copy(); Pt[:, 1] = np.maximum(Pt[:, 1], c["costura_torso"] - 0.004)
        dt = np.maximum(self.piezas[0].sdf(Pt), frontera - 0.002 - y)
        # muslos: prismas que suben hasta la frontera
        dm = np.maximum(self.muslos(P), y - frontera - 0.002)
        d = self.ra.smin(dt, dm, c["k_union"])
        # cubeta solo como relleno interior (no asoma): evita huecos donde el campo del torso no llega
        d = np.minimum(d, self.cubeta(P) + 0.012)
        dg, pliegue = self.gluteos(P)
        d = self.ra.smin(d, dg, c["k_gluteo"])
        sep = 0.0018 * np.exp(-(x / 0.006) ** 2) * _ss((-z - 0.01) / 0.02) * _ss((y - 0.19) / 0.01) * _ss((0.245 - y) / 0.01)
        baja = _ss((c["costura"] - 0.003 - y) / 0.008)
        sube = _ss((y - c["costura_torso"] - 0.003) / 0.006)
        d = d + self.surco_inguinal(P) + pliegue + sep + c["hundir"] * baja + 0.004 * sube
        return np.maximum(d, np.maximum(y - c["arriba"], c["abajo"] - y))

def cortar_piernas(E, S):
    """Quita de piernas y torso los triángulos que la pelvis ya cubre (tapa superior del muslo, tapa inferior del
    torso): la costura queda donde la pelvis se mete bajo la otra pieza, sin tapas asomando ni z-fighting."""
    import receta_adan_v24 as v24
    import receta_adan_v39 as v39
    from copox.medicion.gltf import accesor
    log = {}
    for n, lado in (("PiernaL_PIEL", 1), ("PiernaR_PIEL", 1), ("Torso_PIEL", -1)):
        q = v49._prims(E)[n]
        V = v39._leer(E, q, "POSITION").astype(float)
        T = accesor(E.j, E.b, q["indices"]).reshape(-1, 3)
        c = V[T].mean(1)
        # piernas: sobre la costura; torso: bajo la costura de arriba (su tapa inferior queda dentro de la pelvis)
        fuera = c[:, 1] > PELVIS["costura"] if lado > 0 else c[:, 1] < PELVIS["costura_torso"]
        if fuera.any():
            dentro = S.sdf(c[fuera]) < 0.0015                # solo lo que de verdad queda bajo la piel de la pelvis
            quitar = np.zeros(len(T), bool); quitar[np.nonzero(fuera)[0][dentro]] = True
        else:
            quitar = np.zeros(len(T), bool)
        q["indices"] = v24._add_raw(E, np.ascontiguousarray(T[~quitar].ravel(), np.uint32), 5125, "SCALAR", 34963)
        E.b = bytes(E.out)
        log[n] = int(quitar.sum())
    return log


def pelvis(E, carpeta):
    import receta_adan_v36 as v36
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import short_geo as sg
    nombres, _ = v40.v38_skin(E)
    P = v49._prims(E)
    vieja = P.get("Pelvis_PIEL")
    S = PelvisAnatomica(v49._pieza(E, "Torso_PIEL"), v49._pieza(E, "PiernaL_PIEL"), v49._pieza(E, "PiernaR_PIEL"))
    V, T = sg.malla_sdf(S.sdf, (-0.17, PELVIS["abajo"] - 0.01, -0.10), (0.17, PELVIS["arriba"] + 0.01, 0.14),
                        paso=0.0012, pulido=4)
    V, T = ra.solo_mayor(V, T)
    n0 = len(T)
    V, T = v36.simplificar(V, T, TRIS["pelvis"], carpeta)
    N = v49._normales_sdf(S.sdf, V)
    T = v49._orientar(V, T, N)
    J4, W4 = v41.pesos_short(V, nombres, y_ent=0.205, y_cint=0.27, alto=0.040, centro=0.03, maximo=1.0)
    mat = P["Torso_PIEL"]["material"]
    if vieja is not None:                                        # la pelvis de V49 sale (V50 la reemplaza)
        for m in E.j["meshes"]:
            if vieja in m["primitives"]:
                m["primitives"].remove(vieja)
    v49._al_cuerpo(E, v41._prim_nueva(E, V, T, N, J4, W4, mat, "Pelvis_PIEL"))
    v49._limpiar(carpeta)
    cortes = cortar_piernas(E, S)
    return {"operacion": "pelvis anatómica", "tris_marching": int(n0), "tris": int(len(T)), "piernas_cortadas": cortes}


def main(src, dst, solo=("pelvis",)):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    carpeta = os.path.dirname(os.path.abspath(dst))
    log = []
    if "pelvis" in solo:
        log.append(pelvis(E, carpeta))
    if "zapato" in solo:
        import pie_calzado as pc
        log.append(pc.zapatos(E, carpeta))
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V50: pelvis anatómica y pie con zapato. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    partes = tuple(os.environ.get("ALTH_PARTES", "pelvis").split(","))
    for x in main(sys.argv[1], sys.argv[2], partes):
        print(x)
