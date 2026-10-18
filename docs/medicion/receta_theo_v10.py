"""Theo V10 (sobre V09) / Adán V17 (--solo-estilo): zonas lisas en boca, ojos, nariz y orejas.

Suavizado Taubin (conserva volumen) con malla soldada por posición, pesado por zona:
- boca: elipse |u| < 0.8, v 0.34–0.94 (labios y comisuras), sin tocar la base de la nariz;
- ojos: anillo de piel de 0 a 0.5 ED alrededor de cada placa (incluye ojeras);
- nariz: bloque y su base (|u| < 0.4, v −0.1–0.55), suavizado moderado que conserva el bloque
  (se probó rehacerla como bloque ideal —nariz_limpia— y deformaba el puente: descartado);
- orejas: piel de la cabeza a menos de 0.4 ED de cada oreja (pliegues de la sien y la nuca);
- cara: pasada suave de todo el frente (v −0.3…1.0) para unir las zonas sin escalones.
Protegidos: bordes abiertos de la máscara (incluida la abertura de la boca) y todo lo demás.
La rugosidad (laplaciano / arista media) se mide por zona antes y después.
Uso: python receta_theo_v10.py ENTRADA SALIDA [--solo-estilo]
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
OJOS = ("C7V2_eye_BAKE_L", "C7V2_eye_BAKE_R")


def _soldar(V):
    q = np.round(V / 1e-6).astype(np.int64)
    _, w = np.unique(q, axis=0, return_inverse=True)
    return w.ravel()


def zonas(E, P):
    """Pesos 0–1 por zona sobre los vértices soldados P de la cabeza."""
    v = (YC - P[:, 1]) / ED
    u = P[:, 0] / ED
    frente = S((P[:, 2] - 0.07) / 0.03)
    z = {}
    nariz_caja = S((0.3 - np.abs(u)) / 0.08) * S((0.5 - v) / 0.06)
    z["boca"] = S(1 - np.sqrt((u / 0.8) ** 2 + ((v - 0.64) / 0.3) ** 2)) * frente * (1 - nariz_caja)
    ojos = np.zeros(len(P))
    for mat in OJOS:
        Q = np.concatenate([E.leer(p)[0] for p in E.prims(mat)])
        x0, x1, y0, y1 = Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max()
        dx = np.maximum(np.maximum(x0 - P[:, 0], P[:, 0] - x1), 0)
        dy = np.maximum(np.maximum(y0 - P[:, 1], P[:, 1] - y1), 0)
        d = np.hypot(dx, dy) / ED
        ojos = np.maximum(ojos, S((0.5 - d) / 0.15))
    z["ojos"] = ojos * frente
    z["cara"] = S((v + 0.3) / 0.15) * S((1.0 - v) / 0.1) * S((1.2 - np.abs(u)) / 0.15) * frente
    z["nariz"] = S((0.4 - np.abs(u)) / 0.1) * S((v + 0.1) / 0.1) * S((0.55 - v) / 0.1) * frente
    orejas = []
    for p in E.prims(PIEL):
        V, _ = E.leer(p)
        if len(V) == 84 and V[:, 1].min() > 0.5 and np.abs(V[:, 0]).min() > 0.12:
            orejas.append(V)
    d = np.min([np.sqrt(((P[:, None] - O[None]) ** 2).sum(-1)).min(1) for O in orejas], axis=0) / ED
    z["orejas"] = S((0.4 - d) / 0.15)
    return z


def rugosidad(P, E2, cnt):
    s = np.zeros_like(P); np.add.at(s, E2[:, 0], P[E2[:, 1]])
    lap = np.linalg.norm(s / np.maximum(cnt, 1)[:, None] - P, axis=1)
    le = np.linalg.norm(P[E2[:, 0]] - P[E2[:, 1]], axis=1)
    lm = np.bincount(E2[:, 0], weights=le, minlength=len(P)) / np.maximum(cnt, 1)
    return lap / np.maximum(lm, 1e-9)


def alisar(E, iteraciones={"boca": 30, "ojos": 25, "nariz": 12, "orejas": 30}, lam=0.5, mu=-0.53):
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        F = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        w = _soldar(V); nw = w.max() + 1; Fw = w[F]
        P0 = np.zeros((nw, 3)); np.add.at(P0, w, V); P0 /= np.bincount(w, minlength=nw)[:, None]
        E2 = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]); E2 = np.unique(np.concatenate([E2, E2[:, ::-1]]), axis=0)
        cnt = np.bincount(E2[:, 0], minlength=nw)
        k = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1)
        u_, c_ = np.unique(k, axis=0, return_counts=True)
        borde = np.zeros(nw, bool); borde[u_[c_ == 1].ravel()] = True
        Z = zonas(E, P0)
        r0 = rugosidad(P0, E2, cnt)
        P = P0.copy()
        for nombre, it in iteraciones.items():
            wz = np.where(borde, 0.0, Z[nombre])[:, None]
            for _ in range(it):
                for f in (lam, mu):
                    s = np.zeros_like(P); np.add.at(s, E2[:, 0], P[E2[:, 1]])
                    P += f * wz * (s / np.maximum(cnt, 1)[:, None] - P)
        r1 = rugosidad(P, E2, cnt)
        informe = {n: [round(float(np.median(r0[Z[n] > 0.5])), 3), round(float(np.median(r1[Z[n] > 0.5])), 3)] for n in Z}
        E.escribir(p, V + (P - P0)[w], T)
        E.log.append({"operacion": "zonas lisas: boca, ojos, nariz y orejas (Taubin, bordes protegidos)",
                      "material": PIEL, "rugosidad_mediana_antes_despues": informe,
                      "desplazamiento_max_mm": round(float(np.abs(P - P0).max() * 1000), 2)})
        return informe


def nariz_limpia(E, radio=0.0035):
    """Nariz de bloque limpia: frente plano y biseles suaves. z = base de la cara + altura × meseta(x, y)."""
    for p in E.prims(PIEL):
        V, T = E.leer(p)
        if not es_cabeza(V):
            continue
        v = (YC - V[:, 1]) / ED
        anillo = (np.abs(V[:, 0]) > 0.045) & (np.abs(V[:, 0]) < 0.075) & (v > -0.05) & (v < 0.65) & (V[:, 2] > 0.12)
        A = lambda X, Y: np.c_[np.ones(len(X)), X * X, Y, Y * Y]  # noqa: E731
        c, *_ = np.linalg.lstsq(A(V[anillo, 0], V[anillo, 1]), V[anillo, 2], rcond=None)
        base = A(V[:, 0], V[:, 1]) @ c
        alto = V[:, 2] - base
        zona = (np.abs(V[:, 0]) < 0.045) & (v > -0.05) & (v < 0.62)
        n = zona & (alto > 0.006)
        x0, x1 = V[n, 0].min(), V[n, 0].max(); y0, y1 = V[n, 1].min(), V[n, 1].max()
        cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        H = float(np.percentile(alto[n], 90))
        dx, dy = np.abs(V[:, 0] - cx) - hx, np.abs(V[:, 1] - cy) - hy
        d = np.maximum(dx, dy)                                   # distancia (≈) al borde del rectángulo
        meseta = S((radio - d) / (2 * radio))                    # 1 dentro, bisel suave en el borde
        objetivo = base + H * meseta
        objetivo = np.where(d > 0, np.maximum(objetivo, V[:, 2]), objetivo)   # fuera del bloque nunca se cava
        w = zona * S((2 * radio - d) / radio) * (alto > -0.002)   # solo bloque y bisel: no cava alrededor
        V1 = V.copy(); V1[:, 2] = V[:, 2] + (objetivo - V[:, 2]) * w
        E.escribir(p, V1, T)
        E.log.append({"operacion": "nariz: bloque limpio (frente plano, bisel suave)", "material": PIEL,
                      "caja_ED": [round(hx * 2 / ED, 2), round(hy * 2 / ED, 2)], "altura_ED": round(H / ED, 3),
                      "vertices_movidos": int((w > 0.01).sum())})


def main(src, dst, identidad=True):
    E = re.Editor(src)
    alisar(E, iteraciones={"boca": 60, "ojos": 50, "nariz": 20, "orejas": 40, "cara": 15})
    E.recalcular_normales(PIEL, es_cabeza, "normales recalculadas: cabeza")
    tmp = dst + ".tmp"
    E.guardar(tmp, nota=("Theo V10" if identidad else "Adán V17") + ": zonas lisas (boca, ojos, nariz, orejas). SIN APROBAR.")
    compactar(tmp, dst); os.remove(tmp)
    return E.log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2], identidad="--solo-estilo" not in sys.argv):
        print(x)
