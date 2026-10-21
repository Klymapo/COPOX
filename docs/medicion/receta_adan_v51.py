"""Adán V51 (sobre ADAN_BASE_CONGELADA = V50_1): cabeza de caja BLANDA, como la de las referencias.

Admin (21 oct 2026), viendo las cabezas de Theo V4_2 y Alastor V11 contra sus referencias: la cabeza «está demasiado
caja» (frente plano, lados verticales con canto, quijada de esquinas cuadradas: se lee Roblox). En las referencias la
caja es blanda: esquinas suaves, quijada que se curva a la barbilla y cara un poco más ancha en los cachetes que en la
sien. Pidió (Martillo): (1) suavizar las esquinas verticales y la quijada, (2) ensanchar un poco abajo (cachetes),
(3) barbilla redondeada con un poco de curvatura al frente, sin bultos. La cabeza sigue siendo caja.

Método (el de V33, «superelipse por cortes», aprobado; aquí en sentido inverso, sin técnica nueva):
1. Planta: cada corte horizontal pasa de la superelipse de V33 (n₁ = 3.4 frente / 3.0 atrás) a una más redonda
   (n₂ = N_FRENTE / N_ATRAS) con los mismos semiejes. Frente, costados y nuca no se mueven; solo entran las
   diagonales (nunca infla: lección de los cachetes de bolsa). Ahora el campo sí entra a la cara hasta antes de los
   ojos (PHI_CARA) para que el canto cara-costado se vuelva curva.
2. Frente (silueta): ancho por altura. Abajo la quijada se angosta con un cuarto de superelipse (las esquinas se
   vuelven curva hacia la barbilla) y a la altura de los cachetes se ensancha un poco (CACHETE). El cuello no se toca:
   se escala solo lo que está fuera del radio del cuello.
3. Perfil: la barbilla se redondea igual (la parte de abajo-adelante entra un poco).
El mismo campo se aplica a todo lo que va en la cabeza (piel, ojos, párpados, cejas, boca, orejas, pelo), así nada se
separa. Los gestos (morphs) se conservan como desplazamientos. Normales: las del archivo + cambio de las geométricas.
Uso: python receta_adan_v51.py ADAN_BASE_CONGELADA.glb ADAN_V51.glb
     (el mismo campo sirve para derivados con la cabeza de Adán: THEO_VESTIDO_V4_2 → V4_3, ALASTOR_V11 → V12;
      los lentes y las puntas del cuello no se tocan)
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from copox.medicion import rostro_edicion as re  # noqa: E402
from copox.medicion.gltf import accesor  # noqa: E402
from copox.medicion.compactar import compactar  # noqa: E402
import receta_adan_v32 as v32  # noqa: E402

# --- parámetros (intento 3; 1: ancho mal medido por excluir |x|>0.131; 2: sin escalón bajo la quijada) ---------------------------------------------------------------------------------
N1_FRENTE, N1_ATRAS = 3.4, 3.0        # lo que dejó V33
N_FRENTE, N_ATRAS = 2.3, 2.3          # caja blanda
PHI_CARA = (45.0, 62.0)               # grados desde el costado: el campo de planta se apaga antes de las cuencas
Y_BASE = (0.495, 0.52)                # bajo Y_BASE[0] (cuello) no se mueve nada
CUELLO = dict(zc=0.005, r=0.085, banda=0.015)   # tubo del cuello (medido en y 0.49)
R_CUELLO = 0.055                      # |x| menor que esto (cuello) no se escala en x
QUIJADA = dict(y_ini=0.585, y_fin=0.495, angosta=0.16, n=2.4)   # cuarto de superelipse en la silueta de frente
CACHETE = dict(y=0.575, ancho=0.035, k=0.03)                   # +3 % de ancho a la altura de los cachetes
BARBILLA = dict(y_ini=0.56, y_fin=0.495, z0=0.06, entra=0.10, n=2.4)  # perfil: abajo-adelante entra
PIEZAS_PIEL = ("Cabeza_PIEL_EXPUESTA_v04", "CueroCabelludo_PIEL")
# piezas rígidas o que no son de la cabeza aunque estén arriba del cuello (lentes, puntas del cuello de la camisa)
EXCLUIR = ("ALASTOR_GAFAS", "THEO_CUELLO_PUNTAS")


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _se(phi, a, b, n):
    return (np.abs(np.cos(phi) / a) ** n + np.abs(np.sin(phi) / b) ** n) ** (-1.0 / n)


def _cuarto(t, n):
    """Cuarto de superelipse: t∈[0,1] (0 arriba, 1 al fondo) → fracción que se conserva (1 → 1-...)."""
    t = np.clip(t, 0, 1)
    return (1 - t ** n) ** (1.0 / n)


def cortes(P):
    """Por corte horizontal: medio ancho a, centro zc, semiejes bF (frente) y bB (atrás). Sin orejas ni nariz."""
    ys = np.arange(0.49, 0.79 + 1e-9, 0.01)
    filas = []
    for y in ys:
        q = P[np.abs(P[:, 1] - y) < 0.004]
        if len(q) < 20:
            continue
        a = np.abs(q[:, 0]).max()
        zc = q[np.abs(q[:, 0]) > a - 0.004, 2].mean()
        bF = max(q[:, 2].max() - zc, 0.02)
        bB = max(zc - q[:, 2].min(), 0.02)
        filas.append([y, a, zc, bF, bB])
    C = np.array(filas)
    K = np.array([1, 2, 3, 2, 1], float); K /= K.sum()
    for c in range(1, C.shape[1]):
        C[:, c] = np.convolve(np.pad(C[:, c], 2, mode="edge"), K, mode="valid")
    return C


def envolvente(E):
    """Piel de la cabeza + cuero cabelludo (las orejas y la nariz son primitivas aparte)."""
    j = E.j
    pts = []
    for m in j["meshes"]:
        for p in m["primitives"]:
            if p.get("extras", {}).get("pieza") in PIEZAS_PIEL:
                V = accesor(j, E.b, p["attributes"]["POSITION"]).astype(float)
                pts.append(V)          # orejas y nariz son primitivas aparte
    return np.vstack(pts)


def campo(C, V, P=None):
    P = P or {}
    nF, nB = P.get("N_FRENTE", N_FRENTE), P.get("N_ATRAS", N_ATRAS)
    phi_cara = P.get("PHI_CARA", PHI_CARA)
    qj, ch, bb = {**QUIJADA, **P.get("QUIJADA", {})}, {**CACHETE, **P.get("CACHETE", {})}, {**BARBILLA, **P.get("BARBILLA", {})}
    y = np.clip(V[:, 1], C[0, 0], C[-1, 0])
    it = lambda k: np.interp(y, C[:, 0], C[:, k])
    a, zc, bF, bB = it(1), it(2), it(3), it(4)
    dz = V[:, 2] - zc
    frente = dz >= 0
    # 1) planta: diagonales hacia adentro
    phi = np.arctan2(np.abs(dz), np.abs(V[:, 0]))
    b = np.where(frente, bF, bB)
    n1 = np.where(frente, N1_FRENTE, N1_ATRAS); n2 = np.where(frente, nF, nB)
    g = np.minimum(_se(phi, a, b, n2) / _se(phi, a, b, n1), 1.0)
    u = _ss((np.degrees(phi) - phi_cara[0]) / (phi_cara[1] - phi_cara[0]))
    g = np.where(frente, 1 + (g - 1) * (1 - u), g)
    # 2) silueta de frente: quijada curva + cachete
    t = (qj["y_ini"] - V[:, 1]) / (qj["y_ini"] - qj["y_fin"])
    sx = 1 - qj["angosta"] * (1 - _cuarto(t, qj["n"])) * (V[:, 1] < qj["y_ini"])
    sx = sx * (1 + ch["k"] * np.exp(-((V[:, 1] - ch["y"]) / ch["ancho"]) ** 2))
    # 3) perfil: barbilla (sólo adelante)
    tb = (bb["y_ini"] - V[:, 1]) / (bb["y_ini"] - bb["y_fin"])
    sz = 1 - bb["entra"] * (1 - _cuarto(tb, bb["n"])) * (V[:, 1] < bb["y_ini"]) * _ss((dz - bb["z0"]) / 0.05)
    # se apaga en el cuello: por altura, pero lo que queda fuera del tubo del cuello (bajo la quijada) sí se mueve,
    # para que la parte de abajo de la quijada no deje un escalón
    rho = np.hypot(V[:, 0], V[:, 2] - CUELLO["zc"])
    w = np.maximum(_ss((V[:, 1] - Y_BASE[0]) / (Y_BASE[1] - Y_BASE[0])),
                   _ss((rho - CUELLO["r"]) / CUELLO["banda"]) * _ss((V[:, 1] - 0.47) / 0.012))
    gx = 1 + w * (g * sx - 1)
    gz = 1 + w * (g * np.where(frente, sz, 1.0) - 1)
    V2 = V.copy()
    # x: el cuello (|x| < R_CUELLO) no se escala; rampa suave hacia afuera (sin quiebre en la cara)
    rampa = _ss((np.abs(V[:, 0]) - R_CUELLO * 0.6) / (R_CUELLO * 0.9))
    V2[:, 0] = V[:, 0] * (1 + (gx - 1) * rampa)
    V2[:, 2] = zc + dz * gz
    return V2


def ablandar(E, P=None):
    j = E.j
    C = cortes(envolvente(E))
    hechos, dmax, vistos = 0, 0.0, set()
    for nd in j["nodes"]:
        if "mesh" not in nd:
            continue
        for p in j["meshes"][nd["mesh"]]["primitives"]:
            at = p["attributes"]
            if at["POSITION"] in vistos:
                continue
            V = accesor(j, E.b, at["POSITION"]).astype(float)
            if V[:, 1].min() < 0.44 or p.get("extras", {}).get("pieza") in EXCLUIR:   # sólo la cabeza
                continue
            vistos.add(at["POSITION"])
            V2 = campo(C, V, P)
            if np.abs(V2 - V).max() < 1e-7:
                continue
            E.escribir(p, V2, [])
            if "NORMAL" in at and "indices" in p:
                F = accesor(j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
                N0 = accesor(j, E.b, at["NORMAL"]).astype(float)
                N1 = N0 + v32._normales(V2, F) - v32._normales(V, F)
                N1 /= np.maximum(np.linalg.norm(N1, axis=1, keepdims=True), 1e-12)
                at["NORMAL"] = E._add(N1, "VEC3", 34962)
            hechos += 1
            dmax = max(dmax, float(np.abs(V2 - V).max()))
    E.b = bytes(E.out)
    E.log.append({"operacion": "cabeza de caja blanda (planta más redonda, quijada curva, cachete, barbilla)",
                  "piezas": hechos, "desplazamiento_max": round(dmax, 4),
                  "n_meta": [N_FRENTE, N_ATRAS], "quijada": QUIJADA, "cachete": CACHETE, "barbilla": BARBILLA})


def main(src, dst, P=None, nota="Adán V51: cabeza de caja blanda. SIN APROBAR."):
    E = re.Editor(src)
    ablandar(E, P)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota=nota)
    compactar(tmp, dst)
    os.remove(tmp)
    return E.log


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2]))
