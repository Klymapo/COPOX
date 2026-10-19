"""SENKU · brazo de una pieza como superficie implícita (Adán V45).

Hasta V44 el brazo era la malla original escalada anillo por anillo (V38–V39): conservaba el relieve viejo (bulto de
bíceps, bulto del antebrazo) y un estrechamiento de ~12 % en el codo. Con sombreado suave eso se lee como bultos y
"hoyos" (Admin, 18 oct 2026: "todo liso y plano", "sin huecos").

Aquí el brazo es un barrido de sección superelipse (caja redondeada: caras planas, como la pierna) a lo largo del eje
del brazo en pose T (+x), con centro y semiejes que varían suavemente con x:
- los semiejes salen del brazo anterior (mismo tamaño, que ya seguía la hoja), suavizados (sin bultos) y con el codo
  limitado a un estrechamiento leve;
- del lado del hombro la pieza entra al torso igual que antes (no asoma);
- en la muñeca se corta por un plano exacto: ese anillo es la boca donde se cosen las manos intercambiables.
Marco del brazo izquierdo (el derecho es espejo en x). Unidades del GLB.
"""
from __future__ import annotations

import numpy as np

from .mano_geo import taubin


def corte(V, T, x0):
    """Puntos de la sección de la malla con el plano x = x0."""
    d = V[:, 0] - x0
    P = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ia, ib = T[:, a], T[:, b]
        m = (d[ia] * d[ib]) < 0
        t = d[ia[m]] / (d[ia[m]] - d[ib[m]])
        P.append(V[ia[m]] + (V[ib[m]] - V[ia[m]]) * t[:, None])
    return np.vstack(P) if P else np.zeros((0, 3))


def _suave(x, y, sigma):
    """Suavizado gaussiano de una curva muestreada en x."""
    w = np.exp(-0.5 * ((x[:, None] - x[None, :]) / sigma) ** 2)
    return (w * y[None, :]).sum(1) / w.sum(1)


class Brazo:
    def __init__(self, V, T, x0, x1, codo_x, paso=0.004, sigma=0.012, codo_max=0.03, p=2.6, margen=0.010,
                 lineal=False, muneca=None, hombro=0.035):
        """V, T: brazo anterior (marco izquierdo). x0: inicio (dentro del torso). x1: plano de la muñeca.
        codo_x: x del codo; codo_max: estrechamiento máximo permitido en el codo (fracción)."""
        xs = np.arange(x0, x1 + 1e-9, paso)
        filas = []
        for x in xs:
            c = corte(V, T, min(max(x, x0 + 1e-4), x1 - 1e-4))
            filas.append([(c[:, 1].max() + c[:, 1].min()) / 2, (c[:, 2].max() + c[:, 2].min()) / 2,
                          np.ptp(c[:, 1]) / 2, np.ptp(c[:, 2]) / 2])
        F = np.array(filas)
        self.xs = xs
        self.cy, self.cz = _suave(xs, F[:, 0], sigma), _suave(xs, F[:, 1], sigma)
        ay, az = _suave(xs, F[:, 2], sigma), _suave(xs, F[:, 3], sigma)
        # el codo: nunca más angosto que (1 − codo_max) × la recta entre los máximos de antebrazo y brazo
        for a in (ay, az):
            lado_mano = (xs > codo_x) & (xs < x1 - 0.01)
            lado_hombro = (xs < codo_x) & (xs > x0 + 0.03)
            if lado_mano.any() and lado_hombro.any():
                i1 = np.where(lado_hombro)[0][np.argmax(a[lado_hombro])]
                i2 = np.where(lado_mano)[0][np.argmax(a[lado_mano])]
                lo, hi = sorted((i1, i2))
                recta = np.interp(xs[lo:hi + 1], [xs[lo], xs[hi]], [a[lo], a[hi]])
                a[lo:hi + 1] = np.maximum(a[lo:hi + 1], recta * (1 - codo_max))
        self.ay, self.az = _suave(xs, ay, sigma / 2), _suave(xs, az, sigma / 2)
        # en la muñeca el tamaño exacto del brazo anterior (las manos se cosen ahí)
        n = max(3, int(0.012 / paso))
        for a, f in ((self.ay, F[:, 2]), (self.az, F[:, 3])):
            t = np.linspace(0, 1, n)
            a[-n:] = a[-n:] * (1 - t) + f[-n:] * t
        if lineal:
            # V47 ("brazo recto"): de `hombro` (desde x0) a la muñeca, semiejes en línea recta; el tramo del hombro
            # (dentro del torso) conserva el tamaño del brazo anterior en ese punto. muneca = (semi alto, semi fondo).
            xs = x0 + hombro
            i = int(np.argmin(np.abs(xs_ := self.xs - xs)))
            ays, azs = self.ay[i], self.az[i]
            ayw, azw = muneca if muneca is not None else (self.ay[-1], self.az[-1])
            t = np.clip((self.xs - xs) / (x1 - xs), 0, 1)
            ly, lz = ays + (ayw - ays) * t, azs + (azw - azs) * t
            w = np.clip((self.xs - (xs - 0.015)) / 0.015, 0, 1); w = w * w * (3 - 2 * w)
            self.ay = self.ay * (1 - w) + ly * w
            self.az = self.az * (1 - w) + lz * w
            del xs_
        self.x0, self.x1, self.p = x0, x1, p
        self.margen = margen          # el barrido sigue `margen` más allá de las bocas: el corte no toca las tapas

    def sdf(self, P):
        x = np.clip(P[:, 0], self.x0, self.x1)              # más allá de las bocas, la sección de la boca
        cy, cz = np.interp(x, self.xs, self.cy), np.interp(x, self.xs, self.cz)
        ay, az = np.interp(x, self.xs, self.ay), np.interp(x, self.xs, self.az)
        u = np.abs(P[:, 1] - cy) / ay; v = np.abs(P[:, 2] - cz) / az
        d = ((u ** self.p + v ** self.p) ** (1 / self.p) - 1) * np.minimum(ay, az)
        return np.maximum(d, np.maximum(self.x0 - self.margen - P[:, 0], P[:, 0] - self.x1 - self.margen))

    def malla(self, paso=0.0008, pulido=2):
        from skimage.measure import marching_cubes
        m = max(self.ay.max(), self.az.max()) + 0.01
        lo = np.array([self.x0 - self.margen - 0.004, self.cy.min() - m, self.cz.min() - m])
        hi = np.array([self.x1 + self.margen + 0.004, self.cy.max() + m, self.cz.max() + m])
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

    def perfil(self):
        return {"x": self.xs.round(4).tolist(), "alto_mm": (2000 * self.ay).round(1).tolist(),
                "fondo_mm": (2000 * self.az).round(1).tolist()}
