"""Pruebas sintéticas de la transferencia robusta de pesos."""
import unittest

import numpy as np

from copox.medicion import pesos_robustos as pr
from copox.medicion import tallador as tl


def _cilindro(r, y0, y1, n=16, m=21):
    perf = tl.perfil_super(r, r, n=n, p=2.0)
    secs = [tl.Seccion(np.array([0, y, 0.0]), np.array([1.0, 0, 0]), np.array([0, 0, -1.0]), perf)
            for y in np.linspace(y0, y1, m)]
    p = tl.tallar(secs, angulo=80)
    Vs, Ts, _ = pr._soldar(p.V.astype(float), p.T)
    return Vs, Ts


class TestPesosRobustos(unittest.TestCase):
    def setUp(self):
        # «cuerpo»: cilindro con 2 huesos, peso del hueso 1 sube linealmente con y
        self.Vb, self.Tb = _cilindro(0.05, 0.0, 0.4)
        a = np.clip(self.Vb[:, 1] / 0.4, 0, 1)
        self.Jb = np.zeros((len(self.Vb), 4), np.uint16); self.Jb[:, 1] = 1
        self.Wb = np.zeros((len(self.Vb), 4)); self.Wb[:, 0] = 1 - a; self.Wb[:, 1] = a

    def test_punto_triangulo(self):
        A, B, C = np.array([[0, 0, 0.0]]), np.array([[1, 0, 0.0]]), np.array([[0, 1, 0.0]])
        Q, bar = pr._punto_triangulo(np.array([[0.2, 0.2, 1.0]]), A, B, C)
        self.assertTrue(np.allclose(Q, [[0.2, 0.2, 0]]))
        self.assertTrue(np.allclose(bar.sum(1), 1))

    def test_prenda_ajustada_copia_pesos(self):
        Vp, Tp = _cilindro(0.055, 0.05, 0.35)
        J4, W4, info = pr.transferir(self.Vb, self.Tb, self.Jb, self.Wb, Vp, Tp, d_max=0.02)
        self.assertEqual(info["rellenados"], 0)
        D = pr.densos(J4, W4, 2)
        self.assertTrue(np.allclose(D[:, 1], Vp[:, 1] / 0.4, atol=0.03))
        self.assertTrue(np.allclose(W4.sum(1), 1, atol=1e-5))

    def test_falda_holgada_se_rellena_suave(self):
        # prenda con el tramo de abajo lejos del cuerpo (como un faldón): ahí no hay correspondencia confiable
        Vp, Tp = _cilindro(0.055, 0.05, 0.35)
        lejos = Vp[:, 1] < 0.15
        Vp[lejos, 0] *= 2.2; Vp[lejos, 2] *= 2.2
        J4, W4, info = pr.transferir(self.Vb, self.Tb, self.Jb, self.Wb, Vp, Tp, d_max=0.02)
        self.assertGreater(info["rellenados"], 0)
        D = pr.densos(J4, W4, 2)
        self.assertTrue(np.all(D >= -1e-6) and np.all(D <= 1 + 1e-6))
        # suave: vecinos de la malla no saltan más de 0.15 en el peso
        e = np.vstack([Tp[:, [0, 1]], Tp[:, [1, 2]], Tp[:, [2, 0]]])
        self.assertLess(np.abs(D[e[:, 0], 1] - D[e[:, 1], 1]).max(), 0.15)

    def test_costuras_duplicadas_mismo_peso(self):
        perf = tl.perfil_rect(0.055, 0.055, 0.01, picos=[(90, 0.003)])
        secs = [tl.Seccion(np.array([0, y, 0.0]), np.array([1.0, 0, 0]), np.array([0, 0, -1.0]), perf)
                for y in np.linspace(0.05, 0.35, 8)]
        p = tl.tallar(secs)
        J4, W4, _ = pr.transferir(self.Vb, self.Tb, self.Jb, self.Wb, p.V, p.T, d_max=0.03)
        D = pr.densos(J4, W4, 2)
        _, inv = np.unique(np.round(p.V.astype(float), 6), axis=0, return_inverse=True)
        inv = inv.ravel()
        for g in np.unique(inv):
            self.assertLess(np.ptp(D[inv == g, 1]), 1e-6)


if __name__ == "__main__":
    unittest.main()
