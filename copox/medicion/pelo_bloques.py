"""SENKU · pelo por bloques low-poly explícitos (19 oct 2026, técnica 3 del pelo de Theo).

Las técnicas implícitas (cadena de bolitas, cuñas de rombo) + simplificación daban facetas arrugadas donde se cruzan los
mechones. El pelo de Theo en theo_alpha.glb está hecho de piezas sueltas de ~36 triángulos (Fleco_izquierdo,
Capa_posterior_central, …). Aquí igual: cada mechón es una malla explícita y nuestra, no sale de marching cubes:
sección pentagonal (dos bordes, dos caras de arriba con arista desplazada y una quilla enterrada), 3 estaciones que se
afinan y una punta. ~28 triángulos por mechón, caras planas grandes. Los mechones se apoyan sobre una base del cráneo
(la cáscara de V48.3 inflada y muy simplificada). Las piezas se cruzan entre sí: es normal en un modelo low-poly de juego.
Direcciones como pelo_mechones: azimut 0 = frente, +90 = +x; elevación desde el ecuador de la cabeza.
"""
from __future__ import annotations

import numpy as np

from .pelo_mechones import _dir

# sección: (x a lo ancho en unidades de w, y hacia afuera en unidades de g)
SECCION = np.array([[-1.0, 0.0], [-0.40, 1.0], [0.30, 0.85], [1.0, 0.0], [0.05, -0.55]])
ESTACIONES = np.array([0.0, 0.38, 0.72])          # la punta va en s = 1


def radio_base(base, D):
    dist, j = base.arbol.query(D, k=16)
    w = np.exp(-(dist / 0.012) ** 2) + 1e-12
    w /= w.sum(1, keepdims=True)
    return (w * base.Rd[j]).sum(1)


def mechon(base, m, escala=1.0, afilar=0.55, rng=None, punta=0.0, romo=False):
    """m = (az0, el0, az1, el1, ancho_mm, grueso_mm[, despega_m[, giro_grados]]) -> V, T (caras hacia afuera)."""
    az0, el0, az1, el1, ancho, grueso = m[:6]
    despega = m[6] if len(m) > 6 else 0.0
    giro = np.radians(m[7] if len(m) > 7 else 0.0)
    s = np.append(ESTACIONES, 1.0)
    az = az0 + (az1 - az0) * s
    el = el0 + (el1 - el0) * s
    D = _dir(az, el)
    R = radio_base(base, D)
    g = escala * grueso / 1000 * (1 - 0.55 * s)
    w = escala * ancho / 1000 / 2 * np.maximum((1 - s) ** afilar, punta)
    C = base.c + D * (R + despega * s ** 1.4 + 0.15 * g)[:, None]
    Tg = np.gradient(C, axis=0)
    Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
    N = D - Tg * np.einsum("ij,ij->i", D, Tg)[:, None]
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    B = np.cross(N, Tg)
    V = []
    k = len(SECCION)
    for i in range(len(ESTACIONES)):
        ca, sa = np.cos(giro * s[i]), np.sin(giro * s[i])          # el mechón se tuerce un poco hacia la punta
        Bi, Ni = ca * B[i] + sa * N[i], -sa * B[i] + ca * N[i]
        jit = 1.0 if rng is None else 1.0 + rng.uniform(-0.08, 0.08, k)[:, None]
        V.append(C[i] + (SECCION[:, :1] * w[i] * Bi + SECCION[:, 1:] * g[i] * Ni) * jit)
    if romo:                                                          # punta cortada en bisel (como la hoja), no aguja
        V.append(C[-1] + SECCION[:, :1] * w[-1] * B[-1] + SECCION[:, 1:] * 0.35 * g[-1] * N[-1])
        V = np.vstack(V + [C[-1][None]])
        n_est = len(ESTACIONES) + 1
    else:
        V = np.vstack(V + [C[-1][None]])
        n_est = len(ESTACIONES)
    T = []
    for i in range(n_est - 1):
        a, b = i * k, (i + 1) * k
        for e in range(k):
            f = (e + 1) % k
            T += [(a + e, b + e, b + f), (a + e, b + f, a + f)]
    pun, ult = len(V) - 1, (n_est - 1) * k
    T += [(ult + e, pun, ult + (e + 1) % k) for e in range(k)]
    T += [(0, 1 + e + 1, 1 + e) for e in range(k - 2)]                # tapa de la raíz (queda bajo la base)
    T = np.array(T, np.int64)
    # orientar cada cara hacia afuera de la línea central del mechón
    ref = np.vstack([np.repeat(C[:n_est], k, axis=0), C[-1][None]])
    fc = V[T].mean(1)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, fc - ref[T].mean(1)) < 0
    T[malo] = T[malo][:, ::-1]
    Sv = np.append(np.repeat(s[:n_est], k), 1.0)                      # parámetro a lo largo del mechón (raíz 0, punta 1)
    return V, T, Sv, C


def peinado(base, mechones, escala=1.0, afilar=0.55, semilla=7, punta=0.0, romo=False, detalle=False):
    """V, T de todos los mechones. detalle=True devuelve además, por vértice, el mechón y su parámetro s, y la curva
    central de cada mechón (para ponerle huesos: pelo_huesos)."""
    rng = np.random.default_rng(semilla)
    Vs, Ts, Ids, Ss, Cs, n = [], [], [], [], [], 0
    for i, m in enumerate(mechones):
        V, T, Sv, C = mechon(base, m, escala, afilar, rng, punta, romo)
        Vs.append(V); Ts.append(T + n); Ids.append(np.full(len(V), i)); Ss.append(Sv); Cs.append(C); n += len(V)
    V, T = np.vstack(Vs), np.vstack(Ts)
    if detalle:
        return V, T, np.concatenate(Ids), np.concatenate(Ss), Cs
    return V, T
