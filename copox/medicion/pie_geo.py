"""SENKU · pierna y pie de bloques como superficie implícita (Adán V42).

Hoja de pies de Adán: pierna de prisma recto que sale del short, pie en bloque con el empeine en rampa hacia los dedos,
talón marcado atrás, cuatro dedos-bloque separados (el gordo, hacia adentro, más ancho) y planta plana en el piso.
Marco: Y arriba, frente +Z, X hacia la izquierda del personaje; simétrico en X (las dos piernas en un campo).
"""
from __future__ import annotations

import numpy as np

from .mano_geo import _smin, taubin


def _caja(P, c, h, r):
    q = np.abs(P - c) - (np.asarray(h) - r)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - r


def _superelipse(P, cx, cz, a, b, p):
    u = np.abs(P[:, 0] - cx) / a; v = np.abs(P[:, 2] - cz) / b
    return ((u ** p + v ** p) ** (1 / p) - 1) * min(a, b)


class PiernaPie:
    def __init__(self, x, z, y_arriba, pierna=(0.048, 0.050), tobillo=(0.044, 0.046), y_tobillo=0.060,
                 talon_z=-0.030, punta_z=0.152, ancho_pie=0.052, alto_talon=0.050, alto_dedos=0.022,
                 largo_dedos=0.040, dedos=(1.45, 1.0, 0.95, 0.85), hueco=0.0025, abre=0.006, p=2.8,
                 abre_talon=0.005, k_tobillo=0.005, y_oculta=None):
        self.x, self.z, self.y_arriba = x, z, y_arriba
        self.pierna, self.tobillo, self.y_tobillo = np.asarray(pierna), np.asarray(tobillo), y_tobillo
        self.talon_z, self.punta_z, self.ancho_pie = talon_z, punta_z, ancho_pie
        self.alto_talon, self.alto_dedos, self.largo_dedos = alto_talon, alto_dedos, largo_dedos
        self.dedos, self.hueco, self.abre, self.p = dedos, hueco, abre, p
        self.abre_talon, self.k_tobillo, self.y_oculta = abre_talon, k_tobillo, y_oculta
        self._dedos()

    def _dedos(self):
        """Cajas de los dedos: del lado de adentro (x menor) el gordo; el pie se abre un poco hacia afuera."""
        w_tot = 2 * self.ancho_pie + self.abre - self.hueco * (len(self.dedos) - 1) - 0.004
        anchos = np.array(self.dedos) / sum(self.dedos) * w_tot
        x0 = self.x - self.tobillo[0] + 0.002
        self.cajas = []
        z1 = self.punta_z; z0 = z1 - self.largo_dedos
        for i, w in enumerate(anchos):
            cx = x0 + w / 2
            largo = self.largo_dedos * (1.0 if i == 0 else 0.92 - 0.06 * (i - 1))   # el gordo llega más adelante
            alto = self.alto_dedos * (1.1 if i == 0 else 0.9)
            self.cajas.append((np.array([cx, alto / 2, z1 - largo / 2]), np.array([w / 2, alto / 2, largo / 2])))
            x0 += w + self.hueco
        self.z_dedos = z0

    def sdf(self, Q):
        P = Q.copy(); P[:, 0] = np.abs(P[:, 0])
        y = P[:, 1]
        # pierna: prisma recto que se angosta poco hacia el tobillo
        t = np.clip((self.y_arriba - y) / (self.y_arriba - self.y_tobillo), 0, 1)
        a = self.pierna[0] + (self.tobillo[0] - self.pierna[0]) * t
        b = self.pierna[1] + (self.tobillo[1] - self.pierna[1]) * t
        if self.y_oculta is not None:                                # dentro del short se angosta (no atraviesa la tela)
            o = np.clip((y - self.y_oculta) / 0.012, 0, 1); o = o * o * (3 - 2 * o)
            a = a * (1 - 0.22 * o); b = b * (1 - 0.22 * o)
        u = np.abs(P[:, 0] - self.x) / a; v = np.abs(P[:, 2] - self.z) / b
        d = ((u ** self.p + v ** self.p) ** (1 / self.p) - 1) * np.minimum(a, b)
        d = np.maximum(d, np.maximum(y - self.y_arriba, 0.004 - y))
        # pie: sale de la pierna con planos inclinados (hoja de pies): adentro recto, afuera y atrás se abren hacia el
        # piso; arriba el empeine es plano bajo la pierna y baja en rampa a los dedos
        h = self.alto_talon
        f = np.clip(1 - y / h, 0, 1)                                     # 0 en el tobillo, 1 en el piso
        talon = np.clip((self.z - P[:, 2]) / 0.03, 0, 1)                 # sólo atrás: el talón se abre adentro también
        x_in = self.x - self.tobillo[0] - self.abre_talon * f * talon
        x_out = self.x + self.tobillo[0] + (self.ancho_pie * 2 + self.abre - 2 * self.tobillo[0]) * f
        z_atras = (self.z - self.tobillo[1]) + (self.talon_z - (self.z - self.tobillo[1])) * f
        k_out = (self.ancho_pie * 2 + self.abre - 2 * self.tobillo[0]) / h
        k_atr = ((self.z - self.tobillo[1]) - self.talon_z) / h
        z_rampa = self.z + self.tobillo[1] * 0.55
        s = np.clip((P[:, 2] - z_rampa) / (self.z_dedos - z_rampa), 0, 1)
        techo = h + (self.alto_dedos * 1.15 - h) * s                     # rampa recta, como la hoja
        x_out = x_out + self.abre_talon * f * talon
        planos = np.stack([(x_in - P[:, 0]) / np.sqrt(1 + (self.abre_talon / h) ** 2), (P[:, 0] - x_out) / np.sqrt(1 + k_out ** 2),
                           (z_atras - P[:, 2]) / np.sqrt(1 + k_atr ** 2), P[:, 2] - (self.z_dedos + 0.004),
                           y - techo, -y], 1)
        r = 0.004
        dentro = planos.max(1)
        fuera = np.linalg.norm(np.maximum(planos + r, 0), axis=1) - r
        pie = np.where(dentro < -r, dentro, fuera)
        for c, h in self.cajas:
            pie = np.minimum(pie, _caja(P, c, h, 0.004))            # dedos separados: unión dura
        pie = np.maximum(pie, -y)
        return _smin(d, pie, self.k_tobillo)                         # tobillo: arista suave, sin anillo

    def malla(self, paso=0.0010, pulido=2):
        from skimage.measure import marching_cubes
        xe = self.x + self.ancho_pie + self.abre + 0.02
        lo = np.array([-xe, -0.004, self.talon_z - 0.02]); hi = np.array([xe, self.y_arriba + 0.006, self.punta_z + 0.015])
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
        V[V[:, 1] < 0.0015, 1] = 0.0                                  # planta al piso
        return V, T
