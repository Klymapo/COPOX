"""SENKU · pelo por mechones (prueba, 19 oct 2026): skill alth-meta-vestuario-cabello, paso 6: "Theo mechones gruesos
de raíz ancha y punta suave; evitar pelo realista de hebras".

Cada mechón es una cadena de elipsoides (unión suave) que corre sobre la cáscara del pelo de V48.3 desde una raíz cerca
de la coronilla hasta una punta: ancho y grueso bajan hacia la punta; a media altura se levanta un poco. El pelo es la
unión suave de la cáscara base (un poco hundida) y los mechones. Direcciones en grados: azimut 0 = frente, +90 = lado
izquierdo del personaje (+x); elevación desde el ecuador de la cabeza.
"""
from __future__ import annotations

import numpy as np

from .ropa_ajustada import smin

# (az_raíz, el_raíz, az_punta, el_punta, ancho_mm, grueso_mm): disposición tipo hoja de Theo (copete al frente que
# barre hacia su izquierda, mechones que bajan a los lados y atrás, tres en la coronilla).
MECHONES = [
    (-45, 70, -20, 24, 30, 9), (-18, 74, 8, 21, 32, 10), (8, 74, 34, 23, 30, 9), (32, 70, 55, 27, 28, 8),
    (70, 58, 96, 8, 30, 8), (102, 52, 112, 2, 28, 8), (-70, 58, -96, 8, 30, 8), (-102, 52, -112, 2, 28, 8),
    (150, 62, 160, -22, 32, 9), (180, 62, 180, -28, 34, 9), (-150, 62, -160, -22, 32, 9),
    (125, 52, 136, -12, 28, 8), (-125, 52, -136, -12, 28, 8),
    (0, 86, 120, 62, 30, 10), (90, 80, 168, 56, 28, 9), (-90, 80, -168, 56, 28, 9),
]


def _dir(az, el):
    a, e = np.radians(az), np.radians(el)
    return np.stack([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)], -1)


def _elipsoide(Q, r):
    k0 = np.linalg.norm(Q / r, axis=1); k1 = np.linalg.norm(Q / (r * r), axis=1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-12)


class PeloMechones:
    def __init__(self, base, mechones=MECHONES, hundir=0.0, n_bolas=14, k_mechon=0.008, k_union=0.004,
                 levanta=0.6, escala=1.6):
        """base: PeloOrilla (u otra con .c, ._radio(D) vía Rd/arbol y .sdf)."""
        self.base, self.hundir, self.k_union = base, hundir, k_union
        self.cadenas = []
        for m in mechones:
            az0, el0, az1, el1, ancho, grueso = m[:6]
            despega = m[6] if len(m) > 6 else 0.0          # m: la punta se separa de la cabeza (mechones que cuelgan)
            s = np.linspace(0, 1, n_bolas)
            az = az0 + (az1 - az0) * s; el = el0 + (el1 - el0) * s
            D = _dir(az, el)
            R = self._R(D)
            g = escala * grueso / 1000 * (1 - 0.7 * s)
            w = escala * ancho / 1000 * np.maximum((1 - s) ** 0.7, 0.15)
            lift = levanta * g * np.sin(np.pi * s) - g * 0.15 + despega * s ** 1.5
            C = base.c + D * (R + lift)[:, None]
            Tg = np.gradient(C, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
            B = np.cross(D, Tg); B /= np.linalg.norm(B, axis=1, keepdims=True)
            paso = np.linalg.norm(np.diff(C, axis=0), axis=1).mean()
            self.cadenas.append((C, Tg, D, B, np.stack([np.full(n_bolas, paso * 1.5), g, w / 2], 1)))
        self.k_mechon = k_mechon
        todos = np.vstack([c[0] for c in self.cadenas])
        from scipy.spatial import cKDTree
        self.centros = cKDTree(todos); self.rmax = max(float(c[4].max()) for c in self.cadenas) + 0.01

    def _R(self, D):
        dist, j = self.base.arbol.query(D, k=16)
        w = np.exp(-(dist / 0.012) ** 2) + 1e-12; w /= w.sum(1, keepdims=True)
        return (w * self.base.Rd[j]).sum(1)

    def sdf_mechones(self, P):
        """Cada mechón solo se evalúa en su caja, y cada bolita solo en su esfera (+k): fuera de eso no cambia la
        superficie (la unión suave de valores > k no mueve el cero). Medido: el 78 % del tiempo del pelo era esto."""
        d = np.full(len(P), 1.0)
        for C, Tg, D, B, r in self.cadenas:
            alcance = float(r.max()) + self.k_mechon
            lo = C.min(0) - alcance; hi = C.max(0) + alcance
            sel = np.where(((P >= lo) & (P <= hi)).all(1))[0]
            if not len(sel):
                continue
            Q = P[sel]
            dm = np.full(len(Q), 1.0)
            for i in range(len(C)):
                L = Q - C[i]
                ri = float(r[i].max()) + self.k_mechon
                dentro = np.einsum("ij,ij->i", L, L) < ri * ri
                if not dentro.any():
                    continue
                Mi = np.stack([Tg[i], D[i], B[i]])
                loc = L[dentro] @ Mi.T
                dm[dentro] = smin(dm[dentro], _elipsoide(loc, r[i]), self.k_mechon)
            d[sel] = np.minimum(d[sel], dm)
        return d

    def sdf(self, P):
        return smin(self.base.sdf(P) + self.hundir, self.sdf_mechones(P), self.k_union)

    def malla(self, paso=0.0012, pulido=2):
        from .malla_rapida import malla_banda
        rmax = float(self.base.Rd.max()) + 0.03
        rmin = float(self.base.Rd.min()) - 0.03
        c = self.base.c

        def campo(g):
            r = np.linalg.norm(g - c, axis=1)
            f = np.ones(len(g), np.float32)
            cerca = (r > rmin) & (r < rmax)
            if cerca.any():
                f[cerca] = self.sdf(g[cerca])
            return f
        return malla_banda(campo, c - rmax, c + rmax, paso, pulido=pulido, etiqueta="pelo_mechones")

    def normales(self, V, h=0.0004):
        g = np.zeros_like(V)
        for i in range(3):
            e = np.zeros(3); e[i] = h
            g[:, i] = self.sdf(V + e) - self.sdf(V - e)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


class PeloCunas(PeloMechones):
    """Mechones como cuñas continuas (19 oct 2026, pelo de Theo): la cadena de bolitas se leía como trenzas. Aquí cada
    mechón es una cinta barrida a lo largo de su curva con sección de ROMBO (|b|/w + |n|/g ≤ 1): caras planas y una
    arista al centro, como los mechones low-poly de la hoja. Ancho y grueso bajan hacia la punta; unión casi dura para
    que cada mechón se lea como bloque."""

    def __init__(self, base, mechones, hundir=0.0, n_seg=12, k_mechon=0.002, k_union=0.003, levanta=0.8,
                 escala=1.0, afilar=0.7):
        self.base, self.hundir, self.k_union, self.k_mechon = base, hundir, k_union, k_mechon
        self.cadenas = []
        for m in mechones:
            az0, el0, az1, el1, ancho, grueso = m[:6]
            despega = m[6] if len(m) > 6 else 0.0
            s = np.linspace(0, 1, n_seg + 1)
            az = az0 + (az1 - az0) * s; el = el0 + (el1 - el0) * s
            D = _dir(az, el)
            R = self._R(D)
            g = escala * grueso / 1000 * (1 - 0.65 * s)
            w = escala * ancho / 1000 / 2 * np.maximum((1 - s) ** afilar, 0.22)
            lift = levanta * g * np.sin(np.pi * s) * 0.5 + despega * s ** 1.5
            C = base.c + D * (R + lift)[:, None]
            Tg = np.gradient(C, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
            N = D - Tg * np.einsum("ij,ij->i", D, Tg)[:, None]; N /= np.linalg.norm(N, axis=1, keepdims=True)
            B = np.cross(N, Tg)
            self.cadenas.append((C, N, B, w, g))
        self.rmax = max(float(max(c[3].max(), c[4].max())) for c in self.cadenas) + 0.01

    def sdf_mechones(self, P):
        d = np.full(len(P), 1.0)
        for C, N, B, w, g in self.cadenas:
            alcance = float(max(w.max(), g.max())) + 0.004
            lo = C.min(0) - alcance; hi = C.max(0) + alcance
            sel = np.where(((P >= lo) & (P <= hi)).all(1))[0]
            if not len(sel):
                continue
            Q = P[sel]
            mejor = np.full(len(Q), 1.0)
            for i in range(len(C) - 1):
                a, b = C[i], C[i + 1]
                ab = b - a; L2 = float(ab @ ab)
                t_raw = (Q - a) @ ab / L2
                t = np.clip(t_raw, 0, 1)
                L = Q - (a + t[:, None] * ab)
                n_ = N[i] + (N[i + 1] - N[i]) * t[:, None]
                b_ = B[i] + (B[i + 1] - B[i]) * t[:, None]
                wi = w[i] + (w[i + 1] - w[i]) * t; gi = g[i] + (g[i + 1] - g[i]) * t
                xn = np.abs(np.einsum("ij,ij->i", L, n_)); xb = np.abs(np.einsum("ij,ij->i", L, b_))
                rombo = (xb / wi + xn / gi - 1) / np.sqrt(1 / wi ** 2 + 1 / gi ** 2)
                fuera = np.where(t_raw < 0, -t_raw, np.where(t_raw > 1, t_raw - 1, 0)) * np.sqrt(L2)
                dd = np.where(fuera > 0, np.sqrt(np.maximum(rombo, 0) ** 2 + fuera ** 2), rombo)
                mejor = np.minimum(mejor, dd)
            d[sel] = smin(d[sel], mejor, self.k_mechon)
        return d
