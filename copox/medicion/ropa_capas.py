"""SENKU · ropa por capas (19 oct 2026). Admin: "La ropa, trátala como es. Por capas. No pintes una camisa como si
tuviera chaleco y corbata. Haz cada pieza. Debe de holgar un poco la ropa. Solo un poco. Debe de tener la textura que
le corresponde." Brief: docs/investigacion/ropa_capas.md.

Diferencia con ropa_ajustada (cuerpo inflado y recortado → se veía pintado):
- la tela CUELGA: el sólido del cuerpo (o de la capa de abajo) se CIERRA (dilatar → erosionar, radio `cierre`) antes
  de inflarlo: puentea las concavidades (bajo el pecho, entre glúteos, la ingle) en vez de pegarse a cada una;
- cada capa se apoya en la de abajo: chaleco sobre la camisa, corbata entre camisa y chaleco;
- piezas propias: cuello y puños de la camisa, botones del chaleco, nudo y hoja de la corbata, pretina y vuelta del
  pantalón; cada prenda en su nodo (KHR_node_visibility) con sus pesos de la piel visible;
- textura de tela (texturas_tela) con UV de caja.
Trabaja en vóxeles (NumPy/SciPy, gratis): ocupación del cuerpo → cierre → distancia con signo → marching cubes.
"""
from __future__ import annotations

import numpy as np

from .malla_rapida import paso as _paso


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class Rejilla:
    def __init__(self, lo, hi, paso):
        self.paso = _paso(paso)
        self.lo = np.asarray(lo, float)
        self.n = np.ceil((np.asarray(hi, float) - self.lo) / self.paso).astype(int) + 1
        ejes = [self.lo[i] + self.paso * np.arange(self.n[i]) for i in range(3)]
        self.P = np.stack(np.meshgrid(*ejes, indexing="ij"), -1).reshape(-1, 3)

    def campo(self, f, lote=400_000):
        out = np.empty(len(self.P), np.float32)
        for k in range(0, len(self.P), lote):
            out[k:k + lote] = f(self.P[k:k + lote])
        return out.reshape(self.n)

    def ocupacion(self, piezas, extra=None):
        """Sólido del cuerpo (unión de piezas; el interior profundo se rellena: el campo por muestras dice 'afuera')."""
        from scipy.ndimage import binary_fill_holes

        def f(Q):
            d = np.full(len(Q), 1.0)
            for p in piezas:
                d = np.minimum(d, p.sdf(Q))
            if extra is not None:
                d = np.minimum(d, extra(Q))
            return d
        occ = self.campo(f) < 0
        return binary_fill_holes(occ)

    def cerrar(self, occ, radio):
        from scipy.ndimage import distance_transform_edt as edt
        r = radio / self.paso
        dil = edt(~occ) <= r
        return edt(dil) > r

    def distancia(self, occ):
        """Distancia con signo (negativa adentro) en unidades del modelo."""
        from scipy.ndimage import distance_transform_edt as edt
        return ((edt(~occ) - edt(occ)) * self.paso).astype(np.float32)

    def malla(self, F, suave=0.8):
        from scipy.ndimage import gaussian_filter
        from skimage.measure import marching_cubes
        from .mano_geo import taubin
        if suave:
            F = gaussian_filter(F, suave)
        if F.min() >= 0 or F.max() <= 0:
            return np.zeros((0, 3)), np.zeros((0, 3), int)
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(self.paso,) * 3)
        V = V + self.lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        return taubin(V, T, 4), T

    def muestrear(self, G, Q):
        """Interpola un campo de la rejilla en puntos Q."""
        from scipy.ndimage import map_coordinates
        c = ((Q - self.lo) / self.paso).T
        return map_coordinates(G, c, order=1, mode="nearest")


def normales_campo(rej, F, V):
    g = np.stack(np.gradient(F, rej.paso), -1)
    N = np.stack([rej.muestrear(g[..., i], V) for i in range(3)], 1)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def orientar(V, T, N):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0
    T = T.copy(); T[malo] = T[malo][:, ::-1]
    return T


# ── piezas explícitas (botones, nudo, hoja de corbata, puntas de cuello) ────────────────────────────────────────────
def disco(c, n, r, h, lados=8):
    n = n / np.linalg.norm(n)
    a = np.cross(n, [0, 1, 0]); a = a / max(np.linalg.norm(a), 1e-9) if np.linalg.norm(a) > 1e-6 else np.array([1, 0, 0])
    b = np.cross(n, a)
    ang = np.linspace(0, 2 * np.pi, lados, endpoint=False)
    anillo = np.cos(ang)[:, None] * a + np.sin(ang)[:, None] * b
    V = np.vstack([c + r * anillo, c + r * 0.85 * anillo + h * n, [c], [c + h * n]])
    T = []
    for i in range(lados):
        j = (i + 1) % lados
        T += [(i, j, lados + j), (i, lados + j, lados + i), (2 * lados + 1, lados + i, lados + j), (2 * lados, j, i)]
    return V, np.array(T)


def caja_redondeada(c, ejes, semi, n_ang=6):
    """Elipsoide facetado (nudo de corbata): ejes = 3 vectores unitarios, semi = semiejes."""
    u = np.linspace(0, np.pi, n_ang + 1)[1:-1]; v = np.linspace(0, 2 * np.pi, 2 * n_ang, endpoint=False)
    pts = [[0, 0, 1]] + [[np.sin(a) * np.cos(b), np.sin(a) * np.sin(b), np.cos(a)] for a in u for b in v] + [[0, 0, -1]]
    pts = np.array(pts)
    V = c + (pts * semi) @ np.asarray(ejes)
    from scipy.spatial import ConvexHull
    T = ConvexHull(V).simplices
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, V[T].mean(1) - c) < 0
    T[malo] = T[malo][:, ::-1]
    return V, T


def placa(perfil_izq, perfil_der, grosor, normal_fn):
    """Lámina con grosor entre dos poli-líneas (izquierda/derecha, mismos puntos): hoja de corbata, punta de cuello."""
    L, R = np.asarray(perfil_izq, float), np.asarray(perfil_der, float)
    n = len(L)
    Nf = np.array([normal_fn(p) for p in (L + R) / 2])
    Lf, Rf = L + Nf * grosor, R + Nf * grosor
    V = np.vstack([L, R, Lf, Rf])
    T = []
    for i in range(n - 1):
        a, b = i, i + 1
        T += [(2 * n + a, 3 * n + a, 3 * n + b), (2 * n + a, 3 * n + b, 2 * n + b)]       # cara de afuera
        T += [(a, b, n + b), (a, n + b, n + a)]                                           # cara de adentro
        T += [(a, 2 * n + a, 2 * n + b), (a, 2 * n + b, b)]                               # canto izquierdo
        T += [(n + a, n + b, 3 * n + b), (n + a, 3 * n + b, 3 * n + a)]                   # canto derecho
    T += [(0, n, 3 * n), (0, 3 * n, 2 * n), (n - 1, 3 * n - 1, 4 * n - 1), (n - 1, 4 * n - 1, 2 * n - 1)]
    T = np.array(T)
    c = V.mean(0)                                   # lámina delgada y casi plana: afuera = lejos del centro
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    malo = np.einsum("ij,ij->i", fn, V[T].mean(1) - c) < 0
    T[malo] = T[malo][:, ::-1]
    return V, T


def expandir(V, T, N):
    """Un vértice por esquina (para UV de caja sin estirar)."""
    return V[T].reshape(-1, 3), np.arange(len(T) * 3).reshape(-1, 3), N[T].reshape(-1, 3)
