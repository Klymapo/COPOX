"""Pruebas de las herramientas de animación (sin GLB de personajes: lógica pura + BVH sintético)."""
import os
import unittest

import numpy as np

from copox.movimiento import bvh, cara_arkit as ca, labios

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "mini_tpose.bvh")
MORPHS = ["boca_abrir", "mandibula", "vis_A", "vis_E", "vis_I", "vis_O", "vis_U", "vis_MBP", "vis_FV", "boca_dientes",
          "parpado_L", "parpado_R", "ceja_ceno_L", "ceja_ceno_R", "comisura_arriba_L", "comisura_arriba_R", "boca_sonrisa"]


class TestBVH(unittest.TestCase):
    def test_parse_y_fk(self):
        B = bvh.BVH(open(FIX).read())
        self.assertEqual(B.cuadros.shape, (3, 48))
        R, P = B.fk()
        j = B.nombres.index("LeftHand")
        self.assertTrue(np.allclose(P[0, j], [25, 50, 0]))
        self.assertLess(P[1, j, 1], P[0, j, 1])                      # el brazo baja con Z −60°

    def test_cuaterniones_continuos(self):
        M = np.stack([bvh._rot_eje(1, a) for a in np.linspace(0, 2 * np.pi, 9)])
        q = bvh._m2q(M)
        self.assertTrue(np.all(np.einsum("ij,ij->i", q[1:], q[:-1]) >= 0))

    def test_rodrigues_unitario(self):
        R = bvh._rodrigues(np.array([0, 0, 1.0]), np.pi / 2)
        self.assertTrue(np.allclose(R @ [1, 0, 0], [0, 1, 0]))


class TestCara(unittest.TestCase):
    def test_mapa_solo_morphs_reales(self):
        reales = {'boca_soplar', 'boca_abrir', 'boca_sonrisa', 'boca_triste', 'boca_o', 'boca_tensa', 'boca_lado_L',
                  'boca_lado_R', 'ceja_arriba_L', 'ceja_arriba_R', 'ceja_ceno_L', 'ceja_ceno_R', 'ceja_triste_L',
                  'ceja_triste_R', 'parpado_L', 'parpado_R', 'mandibula', 'vis_A', 'vis_E', 'vis_I', 'vis_O', 'vis_U',
                  'vis_MBP', 'vis_FV', 'parpado_inf_L', 'parpado_inf_R', 'cachete_inflar_L', 'cachete_inflar_R',
                  'cachete_subir_L', 'cachete_subir_R', 'comisura_arriba_L', 'comisura_arriba_R', 'comisura_abajo_L',
                  'comisura_abajo_R', 'boca_ancha', 'boca_estrecha', 'boca_dientes'}
        for k, v in ca.MAPA_ARKIT.items():
            self.assertIn(k, ca.ARKIT)
            for m, g in v:
                self.assertIn(m, reales, f"{k} → {m}")
        self.assertEqual(len(ca.ARKIT), 52)

    def test_neutral_y_rango(self):
        n = 60
        curvas = {k: np.full(n, 0.2) for k in ca.ARKIT}
        curvas["jawOpen"] = np.r_[np.full(30, 0.2), np.full(30, 0.9)]
        P, mir, info = ca.curvas_a_morphs(curvas, MORPHS, fps=30, neutral_s=1.0)
        i = MORPHS.index("mandibula")
        self.assertLess(P[:25, i].max(), 0.05)                       # la cara neutra no deja la boca abierta
        self.assertGreater(P[-1, i], 0.7)
        self.assertTrue(np.all((P >= 0) & (P <= 1)))

    def test_espejo_intercambia_lados(self):
        n = 40
        curvas = {k: np.zeros(n) for k in ca.ARKIT}
        curvas["eyeBlinkLeft"] = np.r_[np.zeros(30), np.ones(10)]
        P, _, _ = ca.curvas_a_morphs(curvas, MORPHS, fps=30, neutral_s=0.5, espejo=True, suavizar=False)
        self.assertGreater(P[-1, MORPHS.index("parpado_R")], 0.9)
        self.assertEqual(P[-1, MORPHS.index("parpado_L")], 0)


class TestLabios(unittest.TestCase):
    def test_cues_a_pesos(self):
        cues = [{"start": 0.0, "end": 0.2, "value": "X"}, {"start": 0.2, "end": 0.5, "value": "D"},
                {"start": 0.5, "end": 0.7, "value": "A"}, {"start": 0.7, "end": 1.0, "value": "X"}]
        t, P = labios.cues_a_pesos(cues, MORPHS, fps=30)
        f = int(0.35 * 30)
        self.assertGreater(P[f, MORPHS.index("vis_A")], 0.9)
        g = int(0.6 * 30)
        self.assertGreater(P[g, MORPHS.index("vis_MBP")], 0.9)
        self.assertLess(P[-1].max(), 0.01)
        self.assertTrue(np.all((P >= 0) & (P <= 1)))


if __name__ == "__main__":
    unittest.main()
