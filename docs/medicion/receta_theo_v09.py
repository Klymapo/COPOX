"""Theo V09 (sobre V08) / Adán V16 (--solo-estilo): pulido de imperfecciones detectadas con CHXP.

- Picos de malla (astillas en la parte alta de la nariz, sienes, barbilla): los vértices cuyo
  laplaciano supera 0.6 aristas se suavizan con su vecindad; se protegen los bordes abiertos de la
  máscara y la abertura de la boca.
- Ceja dentada en gestos (p. ej. G25_3_Amenazante): los deltas de los morphs de la ceja se suavizan
  sobre la placa (el gesto se conserva, desaparecen los escalones).
- Línea del pelo: el borde del gorro era dentado; se suaviza a lo largo del contorno. El borde
  superior de la máscara de la cara también era dentado (asomaba el relleno del pelo): se lleva bajo
  la tira de contorno.
- Gorro de pelo: normales recalculadas tras los cambios de cráneo. El relleno asomaba por la piel
  bajo la línea del pelo (dientes): entra 1.5 mm; el contorno sale 0.8 mm y marca la línea limpia.
- Huecos: la cabeza es una cáscara abierta; por las uniones de pelo, orejas, quijada y comisuras se
  veía el fondo. La piel pasa a ser de dos caras (se ve piel por dentro) y el fondo de la boca es más
  ancho. (Se probó un relleno interior con elipsoide: tapaba menos y asomaba; se descartó.)
Uso: python receta_theo_v09.py ENTRADA SALIDA [--solo-estilo]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
import receta_theo_v05 as v5  # noqa: E402

ED, YC, S = v5.ED, v5.YC, re._suave
PIEL, BOCA = v5.PIEL, v5.BOCA
es_cabeza = v5.es_cabeza
PELO = ("GUIA_CAPILAR_RUBIO_THEO_RELLENO", "GUIA_CAPILAR_RUBIO_THEO_CONTORNO")
CEJAS = ("C7V2_brow_BAKE_L", "C7V2_brow_BAKE_R")


def _vecinos(F, n):
    E2 = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    return np.concatenate([E2, E2[:, ::-1]])


def _soldar(V):
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True)
    return w.ravel()


def quitar_picos(E, umbral=0.6, iteraciones=4):
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        w = _soldar(V); nw = w.max() + 1; Fw = w[F]
        Pw = np.zeros((nw, 3)); np.add.at(Pw, w, V); Pw /= np.bincount(w, minlength=nw)[:, None]
        E2 = _vecinos(Fw, nw)
        # bordes abiertos
        k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
        u, cnt = np.unique(k, axis=0, return_counts=True)
        borde = np.zeros(nw, bool); borde[u[cnt == 1].ravel()] = True
        cnt_v = np.bincount(E2[:, 0], minlength=nw)

        def lap(P):
            s = np.zeros((nw, 3)); np.add.at(s, E2[:, 0], P[E2[:, 1]])
            return s / np.maximum(cnt_v, 1)[:, None] - P
        le = np.linalg.norm(Pw[E2[:, 0]] - Pw[E2[:, 1]], axis=1)
        lm = np.bincount(E2[:, 0], weights=le, minlength=nw) / np.maximum(cnt_v, 1)
        pico = np.linalg.norm(lap(Pw), axis=1) / np.maximum(lm, 1e-9) > umbral
        v = (YC - Pw[:, 1]) / ED
        boca = (np.abs(v - 0.59) < 0.07) & (np.abs(Pw[:, 0]) < 0.5 * ED) & (Pw[:, 2] > 0.09)
        # pico + 1 anillo
        zona = pico.copy(); zona[E2[pico[E2[:, 0]], 1]] = True
        zona &= ~borde & ~boca
        P = Pw.copy()
        for _ in range(iteraciones):
            P[zona] += 0.6 * lap(P)[zona]
        d = P - Pw
        V1 = V + d[w]
        E.escribir(p, V1, T)
        E.log.append({"operacion": "picos de malla suavizados", "material": PIEL, "picos": int(pico.sum()), "vertices_movidos": int(zona.sum())})


def suavizar_morph_cejas(E, iteraciones=12):
    for mat in CEJAS:
        for p in E.prims(mat):
            V, T = E.leer(p)
            F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
            E2 = _vecinos(F, len(V)); cnt = np.bincount(E2[:, 0], minlength=len(V))
            T1, n = [], 0
            for D in T:
                if np.abs(D).max() == 0:
                    T1.append(D); continue
                D1 = D.copy()
                for _ in range(iteraciones):
                    s = np.zeros_like(D1); np.add.at(s, E2[:, 0], D1[E2[:, 1]])
                    D1 = 0.5 * D1 + 0.5 * s / np.maximum(cnt, 1)[:, None]
                T1.append(D1); n += 1
            # escribir solo los deltas (posiciones iguales)
            for t, D in zip(p.get("targets", []), T1):
                if np.abs(D).max() > 0:
                    t["POSITION"] = E._add(D, "VEC3", None, True)
            E.b = bytes(E.out)
            E.log.append({"operacion": f"{mat}: deltas de gestos suavizados (sin escalones)", "material": mat, "morphs": n})


def separar_pelo(E, seps={"GUIA_CAPILAR_RUBIO_THEO_RELLENO": -0.0015, "GUIA_CAPILAR_RUBIO_THEO_CONTORNO": 0.0008}):
    """El relleno del gorro asomaba por la piel bajo la línea del pelo (dientes): se mete 1.5 mm
    (queda bajo la piel donde se traslapan); el contorno sale 0.8 mm y sigue marcando la línea."""
    for mat in PELO:
        sep = seps[mat]
        E.recalcular_normales(mat, None, f"normales recalculadas: {mat}")
        for p in E.prims(mat):
            V, T = E.leer(p)
            N = accesor(E.j, E.b, p["attributes"]["NORMAL"]).astype(float)
            E.escribir(p, V + N * sep, T)
        E.log.append({"operacion": f"{mat}: desplazado {sep * 1000:+.1f} mm sobre su normal", "material": mat})


def suavizar_linea_pelo(E, iteraciones=12):
    """La línea del pelo (borde del gorro) era dentada: se suaviza el borde a lo largo del contorno."""
    for mat in PELO:
        for p in E.prims(mat):
            V, T = E.leer(p)
            F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
            w = _soldar(V); nw = w.max() + 1; Fw = w[F]
            Pw = np.zeros((nw, 3)); np.add.at(Pw, w, V); Pw /= np.bincount(w, minlength=nw)[:, None]
            k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
            u, cnt = np.unique(k, axis=0, return_counts=True)
            B = u[cnt == 1]
            if len(B) == 0:
                continue
            Bd = np.concatenate([B, B[:, ::-1]])
            nb = np.bincount(Bd[:, 0], minlength=nw)
            en_borde = nb > 0
            P = Pw.copy()
            for _ in range(iteraciones):
                s_ = np.zeros((nw, 3)); np.add.at(s_, Bd[:, 0], P[Bd[:, 1]])
                m = en_borde & (nb == 2)
                P[m] = 0.5 * P[m] + 0.5 * s_[m] / 2
            # relaja el primer anillo hacia el borde nuevo para no dejar pliegues
            E2 = _vecinos(Fw, nw); cnt_v = np.bincount(E2[:, 0], minlength=nw)
            anillo = np.zeros(nw, bool); anillo[E2[en_borde[E2[:, 0]], 1]] = True; anillo &= ~en_borde
            for _ in range(3):
                s_ = np.zeros((nw, 3)); np.add.at(s_, E2[:, 0], P[E2[:, 1]])
                P[anillo] = 0.5 * P[anillo] + 0.5 * s_[anillo] / np.maximum(cnt_v[anillo], 1)[:, None]
            E.escribir(p, V + (P - Pw)[w], T)
            E.log.append({"operacion": f"{mat}: línea del pelo suavizada", "material": mat, "vertices_borde": int(en_borde.sum())})


def piel_bajo_contorno(E, alcance=0.007, debajo=0.0012):
    """El borde superior de la máscara de la cara era dentado y por los huecos asomaba el relleno del
    pelo. Cada vértice de ese borde (y su primer anillo, a medias) se lleva bajo la tira de contorno."""
    C = np.concatenate([E.leer(p)[0] for p in E.prims("GUIA_CAPILAR_RUBIO_THEO_CONTORNO")])
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        N = accesor(E.j, E.b, p["attributes"]["NORMAL"]).astype(float)
        w = _soldar(V); nw = w.max() + 1; Fw = w[F]
        Pw = np.zeros((nw, 3)); np.add.at(Pw, w, V); Pw /= np.bincount(w, minlength=nw)[:, None]
        Nw = np.zeros((nw, 3)); np.add.at(Nw, w, N); Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-9)
        k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
        u, cnt = np.unique(k, axis=0, return_counts=True)
        borde = np.zeros(nw, bool); borde[u[cnt == 1].ravel()] = True
        idx = np.nonzero(borde)[0]
        d2 = ((Pw[idx, None] - C[None]) ** 2).sum(-1)
        j = d2.argmin(1); d = np.sqrt(d2[np.arange(len(idx)), j])
        cerca = d < alcance
        P = Pw.copy()
        destino = C[j] - Nw[idx] * debajo
        P[idx[cerca]] = destino[cerca]
        # primer anillo acompaña a medias
        E2 = _vecinos(Fw, nw)
        mov = np.zeros(nw, bool); mov[idx[cerca]] = True
        delta = P - Pw
        s_ = np.zeros((nw, 3)); c_ = np.zeros(nw)
        np.add.at(s_, E2[:, 1], np.where(mov[E2[:, 0]][:, None], delta[E2[:, 0]], 0)); np.add.at(c_, E2[:, 1], mov[E2[:, 0]])
        anillo = (c_ > 0) & ~mov & ~borde
        P[anillo] += 0.5 * s_[anillo] / c_[anillo][:, None]
        E.escribir(p, V + (P - Pw)[w], T)
        E.log.append({"operacion": "borde superior de la cara llevado bajo la línea del pelo", "material": PIEL, "vertices_borde": int(cerca.sum())})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    quitar_picos(E)
    suavizar_morph_cejas(E)
    suavizar_linea_pelo(E)
    separar_pelo(E)
    piel_bajo_contorno(E)
    # la cabeza es una cáscara abierta: con la piel de dos caras, por las uniones se ve piel y no el fondo
    next(m for m in E.j["materials"] if m["name"] == PIEL)["doubleSided"] = True
    E.log.append({"operacion": "piel: doubleSided (por uniones y comisuras se ve piel, no el fondo)", "material": PIEL})
    re.agregar_caja(E, "ADAN_CUERPO", BOCA, (0, 0.548, 0.100), (0.092, 0.017, 0.012), "Head")
    E.log.append({"operacion": "fondo de boca más ancho (comisuras vistas de lado)", "material": BOCA})
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V09" if identidad else "Adán V16") + ": pulido de imperfecciones (CHXP). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
