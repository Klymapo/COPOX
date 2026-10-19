"""COPOX · manos de bloques intercambiables (abierta, puño, señalar…) según las hojas de Adán.

Decisión de Admin (18 oct 2026): manos como la referencia (adan-brazo-4-vistas.jpg): dedos en barras rectangulares de
punta cuadrada, palma de losa, pulgar en bloque; "bloques redondeados" con sombreado suave. Cada mano se MODELA ya en
su pose (no se dobla una mano abierta): no hay piel que se encime ni puntas que atraviesen la palma. Se intercambian
en el juego; todas empiezan en la misma boca de muñeca (el último anillo del antebrazo) y se cosen a ella con los
mismos vértices, normales y pesos: no queda línea entre brazo y mano.

Marco local de la mano izquierda (reposo, pose T): origen = articulación de la muñeca; u = hacia los dedos (+x mundo),
h = hacia el dorso (+y mundo; la palma ve a −y), w = hacia el pulgar (+z mundo). La derecha es espejo en x.
Medidas de la referencia (px de adan-brazo-4-vistas.jpg, vista FRONT): palma 235 de largo y 238 de ancho; dedos
medio 205, índice 165, anular 162, meñique 120; ancho de dedo ~55, separación ~5; pulgar ~170 a ~40°. Se escalan con
el largo de la mano del modelo (muñeca → punta del medio), que coincide con la hoja del cuerpo.
"""
from __future__ import annotations

import numpy as np

from .mano_geo import _smin, taubin, normales

REF_PX = {"palma_largo": 235, "palma_ancho": 238, "Middle": 205, "Index": 165, "Ring": 162, "Little": 120,
          "dedo_ancho": 55, "separacion": 5, "pulgar": 170, "mano": 440}
# dedos-bloque (revisión V40): más cortos y gruesos, casi sin ranura entre ellos; el ancho total de los cuatro no cambia
LARGO_DEDO = 0.86
GRUESO_DEDO = 0.92                     # grueso / ancho del dedo (antes 0.74)
SEPARACION_DEDO = 2                    # px de la hoja entre dedos (antes 5); el ancho absorbe la diferencia
# Estilo de la mano. Los valores por defecto son los de V40–V43.1 (se reproducen bit a bit); una receta nueva pasa los
# suyos con ManoBloques(..., estilo={...}).
ESTILO = {"largo_dedo": LARGO_DEDO, "grueso_dedo": GRUESO_DEDO, "separacion": SEPARACION_DEDO,
          "grosor_palma": 0.36,     # grosor de la losa / ancho de la palma
          "cuna": 1.75,             # la palma es esta tanto más gruesa en la muñeca que en los nudillos
          "pulgar_ang": 32.0, "pulgar_baja": 22.0,   # apertura del pulgar hacia afuera y hacia la palma (grados)
          "pulgar_ancho": 1.3, "pulgar_grueso": 1.2}  # ÷ ancho / grueso del dedo
DEDOS = ("Index", "Middle", "Ring", "Little")
REPARTO = (0.45, 0.30, 0.25)          # largo de cada falange (fracción del dedo)


def _u(v):
    return v / np.linalg.norm(v)


def _rot(eje, ang):
    eje = np.asarray(eje, float); eje = eje / np.linalg.norm(eje)
    K = np.array([[0, -eje[2], eje[1]], [eje[2], 0, -eje[0]], [-eje[1], eje[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def _caja_orientada(P, a, b, lado, ancho, grueso, r):
    """Caja redondeada del punto a al b; `lado` = dirección del ancho (w); el grueso va en la tercera dirección."""
    d = b - a; L = np.linalg.norm(d); d = d / L
    e1 = lado - d * (lado @ d); e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    c = (a + b) / 2
    Q = P - c
    q = np.stack([Q @ d, Q @ e1, Q @ e2], 1)
    h = np.array([L / 2, ancho / 2, grueso / 2]) - r
    k = np.abs(q) - h
    return np.linalg.norm(np.maximum(k, 0), axis=1) + np.minimum(k.max(1), 0) - r


class ManoBloques:
    def __init__(self, largo_mano, pose, palma_w0=0.0, grosor_palma=None, radio=0.0038, estilo=None):
        self.e = e = {**ESTILO, **(estilo or {})}
        k = largo_mano / REF_PX["mano"]
        self.k = k
        self.palma_largo = REF_PX["palma_largo"] * k
        self.palma_ancho = REF_PX["palma_ancho"] * k
        ancho_px = REF_PX["dedo_ancho"] + (REF_PX["separacion"] - e["separacion"])
        self.dedo_ancho = ancho_px * k
        self.paso = (ancho_px + e["separacion"]) * k
        self.largos = {d: REF_PX[d] * k * e["largo_dedo"] for d in DEDOS}
        self.pulgar_largo = REF_PX["pulgar"] * k
        self.dedo_grueso = self.dedo_ancho * e["grueso_dedo"]
        self.grosor = grosor_palma or self.palma_ancho * e["grosor_palma"]      # losa
        self.r = radio
        self.w0 = palma_w0
        self.pose = pose
        self.muneca = None                                         # dict como mano_geo (anillo del antebrazo)
        self._armar()

    # --- esqueleto local (FK de la pose) ------------------------------------------------------------------
    def _armar(self):
        p = self.pose
        U, Hh, W = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
        self.segs = []                    # (a, b, lado, ancho, grueso)
        self.grupos = []
        self.dedo_pts = {}
        h_dedo = self.grosor / 2 - self.dedo_grueso / 2            # dedos al ras del dorso
        for i, d in enumerate(DEDOS):
            w = self.w0 + (1.5 - i) * self.paso
            abanico = np.radians(p.get("abanico", {}).get(d, 0.0))
            dirc = _rot(Hh, abanico) @ U
            lado = np.cross(Hh, dirc)
            lado = lado / np.linalg.norm(lado) * (1 if lado[2] >= 0 else -1)
            raiz = np.array([self.palma_largo - 0.010, h_dedo, w])
            nud = np.array([self.palma_largo, h_dedo, w])
            angs = p["dedos"].get(d, (0.0, 0.0, 0.0))
            pts = [nud]; R = np.eye(3); cur = nud
            for f, a in zip(REPARTO, angs):
                R = _rot(lado, -np.radians(a)) @ R                  # cerrar = la punta va a la palma (−h)
                cur = cur + R @ dirc * f * self.largos[d]
                pts.append(cur)
            self.dedo_pts[d] = pts
            # la falange proximal empieza dentro de la palma
            n0 = len(self.segs)
            # cada falange se alarga medio grueso hacia ambos lados (salvo la punta): los extremos redondeados de
            # dos falanges se tapan entre sí y no queda un surco en la articulación
            ext = self.dedo_grueso * 0.6
            for j in range(3):
                a_ = raiz if j == 0 else pts[j] - _u(pts[j + 1] - pts[j]) * ext
                b_ = pts[j + 1] + (_u(pts[j + 1] - pts[j]) * ext if j < 2 else 0)
                self.segs.append((a_, b_, lado, self.dedo_ancho, self.dedo_grueso))
            self.grupos.append(self.segs[n0:])
        # pulgar: base en el borde de la palma (lado del pulgar), cerca de la muñeca
        t = p["pulgar"]
        base = _base_pulgar(self)
        pts = [base] + [np.asarray(q, float) for q in t["puntos"](self)]
        lado_p = np.asarray(t.get("lado", [0, 1.0, 0]), float)
        n0 = len(self.segs)
        for j in range(len(pts) - 1):
            a_ = pts[j]
            if j > 0:
                a_ = pts[j] - (pts[j + 1] - pts[j]) / np.linalg.norm(pts[j + 1] - pts[j]) * self.dedo_grueso * 0.4
            self.segs.append((a_, pts[j + 1], lado_p, self.dedo_ancho * self.e["pulgar_ancho"],
                              self.dedo_grueso * self.e["pulgar_grueso"]))
        self.grupos.append(self.segs[n0:])
        self.pulgar_pts = pts

    def sdf(self, P):
        L, A, G = self.palma_largo, self.palma_ancho, self.grosor
        # palma: losa con canto redondeado, se angosta hacia la muñeca
        u = np.clip(P[:, 0] / L, 0, 1); su = u * u * (3 - 2 * u)
        hw = A / 2 * (0.78 + 0.22 * su)
        cu = self.e["cuna"]
        hh = G / 2 * (cu - (cu - 1) * su)                          # cuña: gruesa en la muñeca (hoja del brazo)                             # un poco más gruesa en la muñeca
        ch = G / 2 - hh                                             # el extra va al lado de la palma: dorso recto
        x0 = -0.012 if self.muneca is not None else 0.0              # con muñeca, la losa entra al tubo: sin borde en el dorso
        q = np.stack([np.abs(P[:, 0] - (L + x0) / 2) - ((L - x0) / 2 - self.r * 2),
                      np.abs(P[:, 1] - ch) - (hh - self.r * 2),
                      np.abs(P[:, 2] - self.w0) - (hw - self.r * 2)], 1)
        d = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - self.r * 2
        # cuña tenar: une el pulgar con la palma del lado de la muñeca (como la hoja)
        b0 = self.pulgar_pts[0]; b1 = self.pulgar_pts[1]
        ten = _caja_orientada(P, np.array([0.004, b0[1], b0[2] - self.dedo_ancho * 0.6]), b0 + (b1 - b0) * 0.35,
                              np.array([0, 1.0, 0]), self.dedo_ancho * 1.6, self.grosor * 0.8, self.r * 1.5)
        d = _smin(d, ten, 0.008)
        dedos = None
        for grupo in self.grupos:
            g = None
            for (a, b, lado, an, gr) in grupo:                    # falanges del mismo dedo: unión suave (barra
                f = _caja_orientada(P, a, b, lado, an, gr, self.r)  # continua; los dedos entre sí quedan separados)
                g = f if g is None else np.minimum(g, f)
            dedos = g if dedos is None else np.minimum(dedos, g)
        d = _smin(d, dedos, 0.0025)                                 # unión casi dura: bloques, membrana mínima
        if self.muneca is not None:
            m = self.muneca
            x0, x1 = m["x0"], m["x1"]
            t = np.clip((P[:, 0] - x0) / (x1 - x0), 0, 1); st = t * t * (3 - 2 * t)
            ry = m["r0"][0] + (m["r1"][0] - m["r0"][0]) * st
            rz = m["r0"][1] + (m["r1"][1] - m["r0"][1]) * st
            cy = m["c0"][0] + (m["c1"][0] - m["c0"][0]) * st
            cz = m["c0"][1] + (m["c1"][1] - m["c0"][1]) * st
            e = np.sqrt(((P[:, 1] - cy) / ry) ** 2 + ((P[:, 2] - cz) / rz) ** 2)
            dm = (e - 1) * np.minimum(ry, rz)
            dm = np.maximum(dm, np.maximum(x0 - P[:, 0], P[:, 0] - x1))
            d = _smin(d, dm, 0.018)          # suave: sin línea en el dorso donde la losa de la palma empieza
        return d

    def malla(self, paso=0.0008, pulido=3):
        from skimage.measure import marching_cubes
        pts = np.vstack([np.vstack([s[0], s[1]]) for s in self.segs])
        lo = np.minimum(pts.min(0), [0, -self.grosor, self.w0 - self.palma_ancho / 2]) - 0.015
        hi = np.maximum(pts.max(0), [self.palma_largo, self.grosor, self.w0 + self.palma_ancho / 2]) + 0.015
        if self.muneca is not None:
            m = self.muneca
            lo[0] = m["x0"] - 0.003
            lo[1] = min(lo[1], m["c0"][0] - m["r0"][0] - 0.004); hi[1] = max(hi[1], m["c0"][0] + m["r0"][0] + 0.004)
            lo[2] = min(lo[2], m["c0"][1] - m["r0"][1] - 0.004); hi[2] = max(hi[2], m["c0"][1] + m["r0"][1] + 0.004)
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.empty(n, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            F[ix] = self.sdf(g).reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            V = taubin(V, T, pulido)
        return V, T


# --- costura con la boca de muñeca ---------------------------------------------------------------------------
def ajustar_boca(V, base, anillo, centro, x_c, largo=0.028):
    """Los vértices de la mano cerca del corte toman el perfil del anillo (que no es una elipse): sin escalón.
    En x_c el radio es el del anillo en ese ángulo; a `largo` después, el de la mano."""
    yc, zc = centro
    ar = np.arctan2(anillo[:, 2] - zc, anillo[:, 1] - yc); rr = np.hypot(anillo[:, 1] - yc, anillo[:, 2] - zc)
    o = np.argsort(ar); ar, rr = ar[o], rr[o]
    ar = np.concatenate([ar - 2 * np.pi, ar, ar + 2 * np.pi]); rr = np.tile(rr, 3)
    V = V.copy()
    m = np.arange(len(V)) < base
    t = np.clip((V[:, 0] - x_c) / largo, 0, 1); t = t * t * (3 - 2 * t)
    sel = m & (t < 1)
    dy, dz = V[sel, 1] - yc, V[sel, 2] - zc
    a = np.arctan2(dz, dy); r = np.hypot(dy, dz)
    r2 = np.interp(a, ar, rr) * (1 - t[sel]) + r * t[sel]
    V[sel, 1] = yc + np.cos(a) * r2; V[sel, 2] = zc + np.sin(a) * r2
    return V


def cortar(V, T, x_c):
    """Quita lo que queda en x < x_c; los triángulos que cruzan se recortan exactamente en el plano."""
    lado = V[:, 0] >= x_c
    nuevos = {}
    Vl = [V]

    def corte(i, j):
        key = (min(i, j), max(i, j))
        if key not in nuevos:
            a, b = V[i], V[j]
            t = (x_c - a[0]) / (b[0] - a[0])
            Vl.append((a + t * (b - a))[None]); nuevos[key] = len(V) + len(nuevos)
        return nuevos[key]
    out = []
    for tri in T:
        dentro = [lado[v] for v in tri]
        s = sum(dentro)
        if s == 3:
            out.append(tri)
        elif s == 0:
            continue
        else:
            # rota para que el patrón empiece en un vértice "dentro" seguido de uno "fuera" o similar
            for r in range(3):
                a, b, c = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
                if s == 1 and lado[a]:
                    out.append([a, corte(a, b), corte(a, c)]); break
                if s == 2 and not lado[a]:
                    p1, p2 = corte(b, a), corte(c, a)
                    out += [[b, c, p2], [b, p2, p1]]; break
    V2 = np.vstack(Vl)
    T2 = np.array(out, np.int64)
    usados = np.unique(T2)
    mapa = -np.ones(len(V2), np.int64); mapa[usados] = np.arange(len(usados))
    return V2[usados], mapa[T2]


def borde(T):
    """Vértices del borde abierto en orden (el lazo más largo)."""
    from collections import defaultdict
    E = defaultdict(int)
    for t in T:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            E[(a, b)] += 1
    sig = {}
    for (a, b) in E:
        if (b, a) not in E:
            sig[a] = b
    lazos, vistos = [], set()
    for s in sig:
        if s in vistos:
            continue
        l = [s]; vistos.add(s); c = sig[s]
        while c != s and c not in vistos:
            l.append(c); vistos.add(c); c = sig.get(c, s)
        lazos.append(l)
    return max(lazos, key=len)


def coser(V, T, anillo, centro, x_c):
    """Une el borde abierto de la mano (en x = x_c) con el anillo del antebrazo (vértices exactos), por ángulo."""
    b = borde(T)
    ang = lambda P: np.arctan2(P[:, 1] - centro[0], P[:, 2] - centro[1])   # noqa: E731
    ab = ang(V[b]); orden = np.argsort(ab); b = [b[i] for i in orden]; ab = ab[orden]
    aa = ang(anillo); oa = np.argsort(aa); A = anillo[oa]; aa = aa[oa]
    base = len(V)
    V2 = np.vstack([V, A])
    ia = list(range(base, base + len(A)))
    # cierre por fusión de las dos listas ordenadas por ángulo
    i = j = 0; n, m = len(b), len(ia); tris = []
    while i < n or j < m:
        bi, bj = b[i % n], ia[j % m]
        bn, an_ = b[(i + 1) % n], ia[(j + 1) % m]
        ai = ab[(i + 1) % n] + (2 * np.pi if i + 1 >= n else 0)
        aj = aa[(j + 1) % m] + (2 * np.pi if j + 1 >= m else 0)
        if (j >= m) or (i < n and ai <= aj):
            tris.append([bi, bn, bj]); i += 1
        else:
            tris.append([bi, an_, bj]); j += 1
    S = np.array(tris, np.int64)
    # orientación de la tira igual que la malla (normal hacia afuera del eje)
    c = np.stack([V2[S].mean(1)[:, 0], np.full(len(S), centro[0]), np.full(len(S), centro[1])], 1)
    Nf = np.cross(V2[S[:, 1]] - V2[S[:, 0]], V2[S[:, 2]] - V2[S[:, 0]])
    if np.mean(np.einsum("ij,ij->i", Nf, V2[S].mean(1) - c)) < 0:
        S = S[:, ::-1]
    return V2, np.vstack([T, S]), np.array(oa), base


# --- poses ---------------------------------------------------------------------------------------------------
def _base_pulgar(M):
    """Base del pulgar: dentro de la palma, del lado del pulgar y de la palma, a 22 % del largo de la palma."""
    return np.array([REF_PX["palma_largo"] * 0.22 * M.k, -M.grosor * 0.25, M.w0 + M.palma_ancho / 2 - M.dedo_ancho * 0.75])


def _pulgar_abierto(M, ang=None, baja=None, f1=0.45):
    a = np.radians(M.e["pulgar_ang"] if ang is None else ang)
    b = np.radians(M.e["pulgar_baja"] if baja is None else baja)
    d = np.array([np.cos(a), -np.sin(b), np.sin(a)]); d /= np.linalg.norm(d)
    base = _base_pulgar(M)
    return [base + d * M.pulgar_largo * f1, base + d * M.pulgar_largo * 1.08]


def _pulgar_cerrado(M, sobre="Index"):
    """Pulgar acostado por fuera de las falanges medias (sobre el índice y el medio), como el puño de la hoja."""
    base = _base_pulgar(M)
    pi = M.dedo_pts[sobre]; pm = M.dedo_pts["Middle"]
    # cara de enfrente del puño: la falange media del dedo, desplazada hacia afuera (+u)
    objetivo = (pi[1] + pi[2]) / 2 * 0.5 + (pm[1] + pm[2]) / 2 * 0.5
    objetivo = objetivo + np.array([M.dedo_grueso * 0.75, -M.dedo_grueso * 0.2, 0.0])
    mcp = base + np.array([M.pulgar_largo * 0.35, -M.grosor * 0.45, -M.dedo_ancho * 0.1])
    return [mcp, objetivo]


POSES = {
    "abierta": {"dedos": {d: (0.0, 0.0, 0.0) for d in DEDOS},          # rectos, como la hoja
                "abanico": {"Index": -3.0, "Middle": 0.0, "Ring": 2.0, "Little": 5.0},
                "pulgar": {"puntos": _pulgar_abierto, "lado": [0, 1.0, 0]}},
    "puno": {"dedos": {d: (86, 98, 62) for d in DEDOS},
             "pulgar": {"puntos": _pulgar_cerrado, "lado": [0, 0, 1.0]}},
    "senalar": {"dedos": {"Index": (0, 0, 0), "Middle": (86, 98, 62), "Ring": (86, 98, 62), "Little": (86, 98, 62)},
                "abanico": {"Index": -2.0},
                "pulgar": {"puntos": lambda M: _pulgar_cerrado(M, sobre="Middle"), "lado": [0, 0, 1.0]}},
}
