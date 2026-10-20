"""PESOS ROBUSTOS · transferencia de pesos cuerpo → prenda con relleno (inpainting) (20 oct 2026).

Brief: docs/investigacion/pesos_robustos.md. Método: Abdrashitov, Raichstat, Monsen, Hill, «Robust Skin Weights
Transfer via Weight Inpainting», SIGGRAPH Asia 2023 Technical Communications (código de referencia MIT:
github.com/rin-23/RobustSkinWeightsTransferCode). Implementación propia en numpy/scipy (sin libigl).

Problema que resuelve: hoy cada vértice de la prenda copia los pesos de la piel MÁS CERCANA. En zonas holgadas o entre
piernas eso salta de un hueso a otro (picos del abrigo V04–V06, capas que se atraviesan en poses, PLATEAU de Theo).

Pasos:
  1. Correspondencia: punto más cercano sobre la SUPERFICIE del cuerpo (triángulo exacto, no vértice) y pesos
     interpolados con baricéntricas.
  2. Confiable si distancia ≤ d_max y el ángulo entre la normal de la prenda y la del cuerpo ≤ ang_max.
  3. Relleno: los vértices no confiables se resuelven minimizando la energía  tr(Wᵀ Q W),  Q = −L + L M⁻¹ L
     (L cotangente, M masa por área) con los confiables fijos → transición suave, sin saltos.
  4. Limpieza: ≥ 0, se quedan los 4 mayores, suman 1.

Uso:
  J4, W4, info = transferir(Vb, Tb, Jb, Wb, Vp, Tp, Np=None, d_max=0.03, ang_max=35)
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.spatial import cKDTree


# ---------------------------------------------------------------- geometría

def normales_vertice(V, T):
    f = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], f)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)


def _punto_triangulo(P, A, B, C):
    """Punto más cercano de cada P al triángulo ABC (vectorizado, Ericson). Devuelve punto y baricéntricas."""
    ab, ac, ap = B - A, C - A, P - A
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = P - B
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = P - C
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    vc = d1 * d4 - d3 * d2
    vb = d5 * d2 - d1 * d6
    va = d3 * d6 - d5 * d4
    n = len(P)
    bar = np.zeros((n, 3))
    hecho = np.zeros(n, bool)

    def pon(m, b):
        m = m & ~hecho
        bar[m] = b[m] if b.ndim == 2 else b
        hecho[m] = True
    pon((d1 <= 0) & (d2 <= 0), np.array([1.0, 0, 0]))
    pon((d3 >= 0) & (d4 <= d3), np.array([0, 1.0, 0]))
    pon((d6 >= 0) & (d5 <= d6), np.array([0, 0, 1.0]))
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        pon((vc <= 0) & (d1 >= 0) & (d3 <= 0), np.stack([1 - v, v, 0 * v], 1))
        w = d2 / (d2 - d6)
        pon((vb <= 0) & (d2 >= 0) & (d6 <= 0), np.stack([1 - w, 0 * w, w], 1))
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        pon((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), np.stack([0 * w2, 1 - w2, w2], 1))
        den = 1.0 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        pon(np.ones(n, bool), np.stack([1 - vv - ww, vv, ww], 1))
    bar = np.nan_to_num(bar)
    Q = bar[:, :1] * A + bar[:, 1:2] * B + bar[:, 2:] * C
    return Q, bar


def mas_cercano(Vb, Tb, P, k=24):
    """Para cada punto P: triángulo del cuerpo más cercano, punto y baricéntricas (candidatos por centroides)."""
    cen = Vb[Tb].mean(1)
    arbol = cKDTree(cen)
    k = min(k, len(Tb))
    _, cand = arbol.query(P, k=k)
    cand = np.atleast_2d(cand).reshape(len(P), k)
    mejor_d = np.full(len(P), np.inf)
    mejor_t = np.zeros(len(P), int)
    mejor_q = np.zeros_like(P)
    mejor_b = np.zeros((len(P), 3))
    for c in range(k):
        t = cand[:, c]
        A, B, C = Vb[Tb[t, 0]], Vb[Tb[t, 1]], Vb[Tb[t, 2]]
        Q, bar = _punto_triangulo(P, A, B, C)
        d = np.linalg.norm(P - Q, axis=1)
        m = d < mejor_d
        mejor_d[m], mejor_t[m], mejor_q[m], mejor_b[m] = d[m], t[m], Q[m], bar[m]
    return mejor_t, mejor_q, mejor_b, mejor_d


# ---------------------------------------------------------------- operadores

def cotangente(V, T):
    """Laplaciano cotangente L (semidefinido negativo) y masa lumped M (área/3)."""
    n = len(V)
    i0, i1, i2 = T[:, 0], T[:, 1], T[:, 2]
    e0, e1, e2 = V[i2] - V[i1], V[i0] - V[i2], V[i1] - V[i0]
    area2 = np.linalg.norm(np.cross(e1, e2), axis=1)
    area2 = np.maximum(area2, 1e-18)

    def cot(a, b):
        return np.einsum("ij,ij->i", a, b) / area2
    c0, c1, c2 = cot(-e1, e2), cot(-e2, e0), cot(-e0, e1)           # ángulo en 0, 1, 2
    I = np.concatenate([i1, i2, i2, i0, i0, i1])
    J = np.concatenate([i2, i1, i0, i2, i1, i0])
    W = 0.5 * np.concatenate([c0, c0, c1, c1, c2, c2])
    L = sp.coo_matrix((W, (I, J)), shape=(n, n)).tocsr()
    L = L - sp.diags(np.asarray(L.sum(1)).ravel())
    m = np.zeros(n)
    for k in range(3):
        np.add.at(m, T[:, k], area2 / 6)
    return L, sp.diags(np.maximum(m, 1e-15))


def _soldar(V, T, dec=6):
    _, gid, inv = np.unique(np.round(V, dec), axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    return V[gid], inv[T], inv


# ---------------------------------------------------------------- transferencia

def densos(J4, W4, n_huesos):
    D = np.zeros((len(J4), n_huesos))
    np.add.at(D, (np.repeat(np.arange(len(J4)), J4.shape[1]), J4.ravel().astype(int)), W4.ravel())
    return D


def a_cuatro(D, k=4):
    D = np.clip(D, 0, None)
    if D.shape[1] < k:                                               # menos huesos que influencias: rellenar
        D = np.hstack([D, np.zeros((len(D), k - D.shape[1]))])
    J = np.argsort(-D, 1, kind="stable")[:, :k]
    W = np.take_along_axis(D, J, 1)
    s = W.sum(1, keepdims=True)
    W = np.where(s > 1e-12, W / np.maximum(s, 1e-12), np.eye(1, k)[[0] * len(W)])
    J = np.where(W > 0, J, 0)                                        # ranuras vacías → hueso 0 con peso 0 (glTF válido)
    return J.astype(np.uint16), W.astype(np.float32)


def transferir(Vb, Tb, Jb, Wb, Vp, Tp, Np=None, d_max=None, ang_max=35.0, n_huesos=None, permitir_invertida=False):
    """Pesos de la prenda (Vp, Tp) desde el cuerpo (Vb, Tb, Jb/Wb por vértice). Devuelve J4, W4 por vértice de Vp.

    d_max: por defecto 5 % de la diagonal del cuerpo (como el artículo). permitir_invertida: True para prendas
    gruesas cerradas (la cara interior mira hacia el cuerpo). El cuerpo debe incluir TODA la piel bajo la prenda
    (también la oculta: Pelvis, Torso…), no sólo la visible."""
    Vb, Vp = np.asarray(Vb, float), np.asarray(Vp, float)
    Tb, Tp = np.asarray(Tb, int), np.asarray(Tp, int)
    n_huesos = int(n_huesos or (int(np.max(Jb)) + 1))
    if d_max is None:
        d_max = 0.05 * float(np.linalg.norm(Vb.max(0) - Vb.min(0)))
    Db = densos(np.asarray(Jb), np.asarray(Wb, float), n_huesos)
    usados = np.nonzero(Db.any(0))[0]
    Db = Db[:, usados]
    # 1. correspondencia sobre la prenda soldada (las costuras de normales/UV duplican vértices)
    Vs, Ts, inv = _soldar(Vp, Tp)
    Ns = normales_vertice(Vs, Ts) if Np is None else normales_vertice(Vs, Ts)
    t, Q, bar, d = mas_cercano(Vb, Tb, Vs)
    Nb = normales_vertice(Vb, Tb)
    nq = (bar[:, :, None] * Nb[Tb[t]]).sum(1)
    nq /= np.maximum(np.linalg.norm(nq, axis=1, keepdims=True), 1e-15)
    cosang = np.einsum("ij,ij->i", Ns, nq)
    if permitir_invertida:
        cosang = np.abs(cosang)
    Wc = (bar[:, :, None] * Db[Tb[t]]).sum(1)
    conf = (d <= d_max) & (cosang >= np.cos(np.radians(ang_max)))
    info = {"vertices": int(len(Vs)), "confiables": int(conf.sum()), "rellenados": int((~conf).sum()),
            "d_max": d_max, "ang_max": ang_max}
    W = Wc.copy()
    # 2. relleno por componente conexa (una componente sin confiables cae al más cercano)
    if (~conf).any():
        L, M = cotangente(Vs, Ts)
        Minv = sp.diags(1.0 / M.diagonal())
        Qm = (-L + L @ Minv @ L).tocsr()
        n = len(Vs)
        A = sp.coo_matrix((np.ones(len(Ts) * 3), (np.repeat(Ts[:, 0], 3), Ts.ravel())), shape=(n, n))
        ncomp, comp = sp.csgraph.connected_components(A + A.T, directed=False)
        info["componentes"] = int(ncomp)
        for c in range(ncomp):
            en = comp == c
            u = np.nonzero(en & ~conf)[0]
            k = np.nonzero(en & conf)[0]
            if len(u) == 0:
                continue
            if len(k) == 0:
                info.setdefault("sin_confiables", 0)
                info["sin_confiables"] += int(len(u))
                continue                                         # se quedan los pesos del más cercano
            Quu = Qm[u][:, u] + sp.identity(len(u)) * 1e-10
            rhs = -(Qm[u][:, k] @ W[k])
            sol = spla.splu(Quu.tocsc())
            W[u] = sol.solve(rhs)
    Dfull = np.zeros((len(Vs), n_huesos))
    Dfull[:, usados] = W
    J4s, W4s = a_cuatro(Dfull)
    info["confiable_frac"] = round(float(conf.mean()), 4)
    return J4s[inv], W4s[inv], info
