"""TALLADOR · prendas y mechones por secciones poligonales con bisel (20 oct 2026).

Brief: docs/investigacion/tallador.md. Ruta: docs/RUTA_AAA.md §4.1.

Por qué existe: la ropa y el pelo hechos con SDF → marching cubes → suavizado salen «blandos» y pierden las aristas que
definen el estilo de las referencias (bloques con bisel, paneles, pliegues como geometría). Lo que mejor se parece a la
referencia en el repo (pie/zapato V46 por loft, rizo de Alastor por barrido) no pasa por SDF. Este módulo lo generaliza:

  perfil 2D (rectángulo redondeado / superelipse, con aristas «duras» marcadas)
    → secciones 3D (centro + ejes u, v) a lo largo de una pieza
    → puente de quads entre secciones (low-poly por construcción, sin simplificar)
    → normales ponderadas por área con suavizado por ángulo y costuras duras (look «chunky» limpio)
    → UV por sección (U = perímetro, V = largo) y anillos para pesos.

Todo en numpy, determinista (recetas reproducibles bit a bit) y sin bpy.

API principal
  perfil_rect(a, b, r, seg=2, picos=())      perfil 2D cerrado (rectángulo redondeado), sentido antihorario
  perfil_super(a, b, n=12, p=4.0)            superelipse de n lados
  Seccion(c, u, v, perfil, escala=(1, 1))    una sección en 3D
  secciones_barrido(curva, perfil, escala)   secciones a lo largo de una curva (marcos de transporte paralelo)
  escalon(secciones, i, delta, alto)         dobladillo/pretina: escalón saliente alrededor de la sección i
  tallar(secciones, duros=(), anillos_duros=(), tapas=(False, False), angulo=40, peso=4.0) → Pieza
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# ---------------------------------------------------------------- perfiles 2D

def perfil_rect(a, b, r, seg=2, picos=()):
    """Rectángulo redondeado de semiejes a (u) y b (v) con radio de esquina r (bisel) y `seg` segmentos por esquina.

    `picos`: [(ang_grados, salida)] → agrega un vértice en esa dirección empujado `salida` (raya de pantalón, quilla).
    Devuelve (P[n,2], duros[list]) donde duros son los índices de los picos (aristas longitudinales duras)."""
    r = float(min(r, a * 0.999, b * 0.999))
    P = []
    for cx, cy, a0 in ((a - r, b - r, 0), (-(a - r), b - r, 90), (-(a - r), -(b - r), 180), ((a - r), -(b - r), 270)):
        for k in range(seg + 1):
            t = np.radians(a0 + 90.0 * k / max(seg, 1))
            P.append((cx + r * np.cos(t), cy + r * np.sin(t)))
    P = np.array(P, float)
    if r <= 1e-9:                                                 # sin bisel: quitar duplicados de esquina
        _, idx = np.unique(np.round(P, 9), axis=0, return_index=True)
        P = P[np.sort(idx)]
    duros = []
    for ang, salida in picos:
        d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        # punto del contorno en esa dirección (rayo desde el centro) e inserción ordenada por ángulo
        angs = np.arctan2(P[:, 1], P[:, 0]) % (2 * np.pi)
        t = np.radians(ang) % (2 * np.pi)
        i = int(np.searchsorted(angs, t)) if np.all(np.diff(angs) > 0) else int(np.argmin(np.abs(angs - t)))
        # distancia del contorno en esa dirección: intersección con el segmento i-1 → i
        p0, p1 = P[(i - 1) % len(P)], P[i % len(P)]
        M = np.array([d, p0 - p1]).T
        try:
            s, _ = np.linalg.solve(M, p0)
        except np.linalg.LinAlgError:
            s = float(np.hypot(*p0))
        P = np.insert(P, i % (len(P) + 1), d * (s + salida), axis=0)
        duros = [j + 1 if j >= i else j for j in duros] + [i]
    return P, sorted(duros)


def perfil_super(a, b, n=12, p=4.0, fase=0.0):
    """Superelipse |x/a|^p + |y/b|^p = 1 con n lados (p=2 elipse, p→∞ rectángulo)."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False) + fase
    c, s = np.cos(t), np.sin(t)
    return np.stack([a * np.sign(c) * np.abs(c) ** (2 / p), b * np.sign(s) * np.abs(s) ** (2 / p)], 1), []


# ---------------------------------------------------------------- secciones 3D

@dataclass
class Seccion:
    c: np.ndarray                      # centro (3)
    u: np.ndarray                      # eje del perfil x (3, unitario)
    v: np.ndarray                      # eje del perfil y (3, unitario)
    perfil: tuple                      # (P[n,2], duros)
    escala: tuple = (1.0, 1.0)

    def puntos(self):
        P = self.perfil[0] * np.asarray(self.escala, float)
        return np.asarray(self.c, float) + P[:, :1] * np.asarray(self.u, float) + P[:, 1:] * np.asarray(self.v, float)


def _unit(x):
    x = np.asarray(x, float)
    return x / max(np.linalg.norm(x), 1e-12)


def marcos(curva, arriba=(0, 1, 0)):
    """Marcos de transporte paralelo (sin giros bruscos) a lo largo de una polilínea: devuelve tangentes, u, v."""
    C = np.asarray(curva, float)
    T = np.gradient(C, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    a = np.asarray(arriba, float)
    if abs(T[0] @ _unit(a)) > 0.95:
        a = np.array([0.0, 0.0, 1.0])
    U = [_unit(np.cross(a, T[0]))]
    for i in range(1, len(C)):
        b = np.cross(T[i - 1], T[i])
        if np.linalg.norm(b) < 1e-9:
            U.append(U[-1]); continue
        b = _unit(b); ang = np.arccos(np.clip(T[i - 1] @ T[i], -1, 1))
        u = U[-1]
        u = u * np.cos(ang) + np.cross(b, u) * np.sin(ang) + b * (b @ u) * (1 - np.cos(ang))   # Rodrigues
        U.append(_unit(u - (u @ T[i]) * T[i]))
    U = np.array(U)
    V = np.cross(T, U)
    return T, U, V


def secciones_barrido(curva, perfil, escala=None, arriba=(0, 1, 0)):
    """Secciones a lo largo de una curva. `escala`: lista/array de (sx, sy) por punto o función t∈[0,1] → (sx, sy)."""
    C = np.asarray(curva, float)
    _, U, V = marcos(C, arriba)
    n = len(C)
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        s = escala(t) if callable(escala) else (escala[i] if escala is not None else (1.0, 1.0))
        out.append(Seccion(C[i], U[i], V[i], perfil, tuple(np.broadcast_to(np.asarray(s, float), (2,)))))
    return out


def escalon(secciones, i, delta, alto, arriba=True):
    """Dobladillo / pretina: inserta alrededor de la sección i un escalón saliente `delta` (m) de `alto` (m).

    Devuelve la lista nueva y los índices de anillos duros (bordes del escalón)."""
    s = secciones[i]
    eje = _unit(np.cross(s.u, s.v))
    if not arriba:
        eje = -eje
    P = s.perfil[0]
    n = np.linalg.norm(P, axis=1, keepdims=True)
    crece = lambda d: (P + P / np.maximum(n, 1e-12) * d, s.perfil[1])                       # noqa: E731
    nuevas = [Seccion(s.c, s.u, s.v, crece(delta), s.escala),
              Seccion(np.asarray(s.c) + eje * alto, s.u, s.v, crece(delta), s.escala),
              Seccion(np.asarray(s.c) + eje * alto, s.u, s.v, s.perfil, s.escala)]
    lista = secciones[:i + 1] + nuevas + secciones[i + 1:]
    return lista, [i, i + 1, i + 2, i + 3]


# ---------------------------------------------------------------- tallado

@dataclass
class Pieza:
    V: np.ndarray                      # vértices (con costuras duplicadas)
    T: np.ndarray                      # triángulos (int)
    N: np.ndarray                      # normales por vértice
    UV: np.ndarray                     # uv por vértice
    anillo: np.ndarray                 # índice de sección de cada vértice (para pesos)
    info: dict = field(default_factory=dict)

    @property
    def tris(self):
        return len(self.T)


def _area_normal(Vp, Tq):
    f = np.cross(Vp[Tq[:, 1]] - Vp[Tq[:, 0]], Vp[Tq[:, 2]] - Vp[Tq[:, 0]])
    a = np.linalg.norm(f, axis=1)
    return f / np.maximum(a[:, None], 1e-15), a / 2


def tallar(secciones, duros=None, anillos_duros=(), tapas=(False, False), angulo=40.0, peso=4.0):
    """Puentea las secciones con quads y calcula normales ponderadas + UV.

    duros: índices de vértices del perfil que son aristas longitudinales duras (por defecto los del propio perfil).
    anillos_duros: índices de sección cuyo anillo es arista dura (bordes de dobladillo, pretina).
    tapas: (inicio, fin) cierra con abanico plano (para mechones sueltos; las prendas van abiertas).
    angulo: suavizado automático (caras con normales a más de `angulo` grados no se promedian).
    peso: exponente del peso por área (normales «weighted»: las caras grandes mandan → paneles planos limpios)."""
    if not secciones:
        raise ValueError("tallar: sin secciones")
    n = len(secciones[0].perfil[0])
    if any(len(s.perfil[0]) != n for s in secciones):
        raise ValueError("tallar: todas las secciones deben tener el mismo número de puntos")
    duros = set(secciones[0].perfil[1] if duros is None else duros)
    anillos_duros = set(anillos_duros)
    m = len(secciones)
    R = np.array([s.puntos() for s in secciones])                # m × n × 3
    Vp = R.reshape(-1, 3)
    idx = lambda i, j: i * n + (j % n)                            # noqa: E731
    caras, fi, fj = [], [], []                                    # anillo y tira (columna del perfil) de cada cara
    for i in range(m - 1):
        for j in range(n):
            q = (idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j))
            caras += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
            fi += [i, i]; fj += [j, j]
    tapas_v = []
    for k, (cerrar, i) in enumerate(zip(tapas, (0, m - 1))):
        if not cerrar:
            continue
        ci = len(Vp) + len(tapas_v)
        tapas_v.append(R[i].mean(0))
        for j in range(n):
            t = (ci, idx(i, j + 1), idx(i, j)) if k == 0 else (ci, idx(i, j), idx(i, j + 1))
            caras.append(t); fi.append(-1 - k); fj.append(-1)
    if tapas_v:
        Vp = np.vstack([Vp, tapas_v])
    T = np.array(caras, int)
    fi = np.array(fi); fj = np.array(fj)
    panel = np.where(fi >= 0, 0, -1)
    # orientación: normales hacia afuera del eje de cada sección
    FN, FA = _area_normal(Vp, T)
    cen = np.array([np.asarray(s.c, float) for s in secciones])
    fc = Vp[T].mean(1)
    ring = np.clip(T[:, 0] // n, 0, m - 1)
    afuera = np.einsum("ij,ij->i", FN, fc - cen[ring])
    if np.sum(afuera[panel >= 0] < 0) > np.sum(afuera[panel >= 0] > 0):
        T = T[:, ::-1]; FN = -FN
    # normales por esquina (vértice, cara): promedio ponderado de caras vecinas del mismo panel/banda y a < angulo
    cosmax = np.cos(np.radians(angulo))
    vecinas = [[] for _ in range(len(Vp))]
    for f, tri in enumerate(T):
        for v in tri:
            vecinas[v].append(f)
    amax = np.zeros(len(Vp))
    for v, fs in enumerate(vecinas):
        if fs:
            amax[v] = FA[fs].max()
    esquinas_v, esquinas_n = [], []
    def _lado(g, v):
        """Lado de la cara g respecto de las costuras duras que pasan por el vértice v (−1 = tapa)."""
        if fi[g] < 0:
            return ("tapa", int(fi[g]))
        if v >= m * n:
            return ("cuerpo",)
        iv, jv = divmod(int(v), n)
        lj = (0 if fj[g] == (jv - 1) % n else 1) if jv in duros else 0
        li = (0 if fi[g] < iv else 1) if iv in anillos_duros else 0
        return (lj, li)
    for f, tri in enumerate(T):
        for v in tri:
            lf = _lado(f, v)
            fs = [g for g in vecinas[v] if _lado(g, v) == lf and FN[g] @ FN[f] >= cosmax]
            w = (FA[fs] / max(amax[v], 1e-15)) ** peso
            nn = (FN[fs] * w[:, None]).sum(0)
            esquinas_v.append(v); esquinas_n.append(nn / max(np.linalg.norm(nn), 1e-15))
    EV = np.array(esquinas_v); EN = np.round(np.array(esquinas_n), 6)
    # UV: U por perímetro acumulado del perfil (con costura en j=0), V por largo acumulado de centros
    P0 = secciones[0].perfil[0]
    per = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([P0, P0[:1]]), axis=0), axis=1))]
    Uj = per / max(per[-1], 1e-12)
    largo = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))]
    Vi = largo / max(per[-1] * np.mean([np.mean(s.escala) for s in secciones]), 1e-12)
    uv_esq = []
    for f, tri in enumerate(T):
        js = [int(v % n) if v < m * n else -1 for v in tri]
        costura = (fi[f] >= 0) and (0 in js) and (n - 1 in js)
        for v, j in zip(tri, js):
            if v >= m * n:
                uv_esq.append((0.5, 0.0)); continue
            u = Uj[n] if (costura and j == 0) else Uj[j]
            uv_esq.append((u, Vi[v // n]))
    UVE = np.round(np.array(uv_esq), 6)
    # vértices únicos por (posición, normal, uv)
    clave = np.hstack([EV[:, None].astype(float), EN, UVE])
    _, unico, inv = np.unique(clave, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    orden = np.argsort(unico)                                   # estable: en orden de aparición
    remap = np.empty_like(orden); remap[orden] = np.arange(len(orden))
    sel = unico[orden]
    V = Vp[EV[sel]]
    N = EN[sel]
    UV = UVE[sel]
    T2 = remap[inv].reshape(-1, 3)
    anillo = np.where(EV[sel] < m * n, EV[sel] // n, np.where(EV[sel] == m * n, 0, m - 1))
    info = {"secciones": m, "lados": n, "tris": int(len(T2)), "vertices": int(len(V)),
            "aristas_duras": sorted(duros), "anillos_duros": sorted(anillos_duros)}
    return Pieza(V.astype(np.float32), T2.astype(np.int64), N.astype(np.float32), UV.astype(np.float32), anillo, info)


def unir(piezas):
    """Junta varias piezas en una (para una prenda con partes)."""
    V, T, N, UV, A, o = [], [], [], [], [], 0
    for p in piezas:
        V.append(p.V); T.append(p.T + o); N.append(p.N); UV.append(p.UV); A.append(p.anillo); o += len(p.V)
    return Pieza(np.vstack(V), np.vstack(T), np.vstack(N), np.vstack(UV), np.concatenate(A),
                 {"partes": len(piezas), "tris": int(sum(len(t) for t in T))})


def aristas_abiertas(T):
    """Aristas con una sola cara (bordes de la prenda). Útil para validar que no haya huecos internos."""
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return u[c == 1]


def a_prim(E, pieza, mat, nombre, J4, W4):
    """Pieza tallada → primitiva glTF con sus propias normales, UV y pesos (J4/W4 por vértice de `pieza.V`).

    Los pesos vienen de `pesos_robustos.transferir` (recomendado) o de `ropa_ajustada.pesos_por_piel_visible`."""
    from copox.medicion import glb_util as gu
    p = gu.prim_nueva(E, pieza.V.astype(np.float32), pieza.T.astype(np.uint32), pieza.N.astype(np.float32),
                      np.asarray(J4), np.asarray(W4, np.float32), mat, nombre)
    p["attributes"]["TEXCOORD_0"] = E._add(pieza.UV.astype(np.float32), "VEC2", 34962)
    p.setdefault("extras", {})["tallador"] = pieza.info
    return p
