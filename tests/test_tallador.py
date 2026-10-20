"""Pruebas sintéticas del tallador (sin personajes: geometría de control)."""
import unittest

import numpy as np

from copox.medicion import tallador as tl


def _soldar(p):
    _, gid = np.unique(np.round(p.V.astype(float), 6), axis=0, return_inverse=True)
    return gid.ravel()[p.T]


class TestTallador(unittest.TestCase):
    def _tubo(self, **kw):
        perf = tl.perfil_rect(0.05, 0.04, 0.012, seg=2, **kw)
        secs = [tl.Seccion(np.array([0, y, 0.0]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), perf)
                for y in np.linspace(0, 0.3, 6)]
        return perf, secs

    def test_perfil_rect_cerrado_y_ccw(self):
        P, duros = tl.perfil_rect(0.05, 0.04, 0.01, seg=3)
        self.assertEqual(len(P), 16)
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        self.assertGreater(area, 0)
        self.assertEqual(duros, [])

    def test_pico_es_arista_dura(self):
        P, duros = tl.perfil_rect(0.05, 0.04, 0.01, seg=2, picos=[(90, 0.004)])
        self.assertEqual(len(duros), 1)
        self.assertAlmostEqual(float(P[duros[0], 1]), 0.044, places=4)

    def test_tubo_sin_huecos_internos(self):
        _, secs = self._tubo()
        p = tl.tallar(secs)
        abiertas = tl.aristas_abiertas(_soldar(p))
        # sólo los dos bordes (inicio y fin): 2 × lados aristas
        self.assertEqual(len(abiertas), 2 * len(secs[0].perfil[0]))
        self.assertEqual(p.tris, 2 * 12 * 5)

    def test_normales_unitarias_y_hacia_afuera(self):
        _, secs = self._tubo()
        p = tl.tallar(secs)
        self.assertTrue(np.allclose(np.linalg.norm(p.N, axis=1), 1, atol=1e-4))
        radial = p.V[:, [0, 2]]
        self.assertTrue(np.all(np.einsum("ij,ij->i", p.N[:, [0, 2]], radial) > 0))

    def test_paneles_planos_por_peso_de_area(self):
        """En la cara plana grande del rectángulo la normal debe ser exactamente la de la cara (look «chunky»)."""
        _, secs = self._tubo()
        p = tl.tallar(secs, peso=4.0)
        cara_x = np.abs(p.V[:, 0] - 0.05) < 1e-6        # vértices sobre la cara plana +X (comparten bisel)
        self.assertTrue(cara_x.any())
        self.assertTrue(np.all(p.N[cara_x, 0] > 0.97))

    def test_arista_dura_duplica_vertices(self):
        perf, secs = self._tubo(picos=[(90, 0.004)])
        blanda = tl.tallar(secs, duros=[])
        dura = tl.tallar(secs)
        self.assertGreater(len(dura.V), len(blanda.V))

    def test_escalon_dobladillo(self):
        _, secs = self._tubo()
        s2, duros = tl.escalon(secs, 0, 0.003, 0.02)
        p = tl.tallar(s2, anillos_duros=duros)
        self.assertEqual(p.info["secciones"], len(secs) + 3)
        r = np.max(np.abs(p.V[:, 0]))
        self.assertAlmostEqual(r, 0.05 + 0.003, delta=0.002)

    def test_uv_en_rango(self):
        _, secs = self._tubo()
        p = tl.tallar(secs)
        self.assertGreaterEqual(p.UV[:, 0].min(), 0)
        self.assertLessEqual(p.UV[:, 0].max(), 1.0 + 1e-6)
        self.assertGreater(p.UV[:, 1].max(), 0)

    def test_barrido_con_tapas_cerrado(self):
        t = np.linspace(0, np.pi, 10)
        curva = np.stack([0.05 * np.cos(t), 0.05 * np.sin(t), np.zeros_like(t)], 1)
        secs = tl.secciones_barrido(curva, tl.perfil_super(0.01, 0.006, n=8), escala=lambda s: (1 - 0.6 * s, 1 - 0.6 * s))
        p = tl.tallar(secs, tapas=(True, True))
        self.assertEqual(len(tl.aristas_abiertas(_soldar(p))), 0)

    def test_determinista(self):
        _, secs = self._tubo()
        a, b = tl.tallar(secs), tl.tallar(secs)
        self.assertTrue(np.array_equal(a.V, b.V) and np.array_equal(a.T, b.T) and np.array_equal(a.N, b.N))


if __name__ == "__main__":
    unittest.main()
