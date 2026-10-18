"""Pruebas del renderizador (copox.render) y del compactador de GLB."""
import json
import os
import struct
import tempfile
import unittest

import numpy as np

from copox.medicion import paleta
from copox.medicion.camara import Camara
from copox.medicion.compactar import compactar
from copox.medicion.gltf import Modelo
from copox.medicion.raster import Escena, render as render_viejo
from copox.render import Sesion, leer, GUARDADAS
from copox.render.lamina import lamina_ab
from copox.render.raster import rasterizar
from copox.render.vistas import MODOS
from tests.test_medicion_v2 import _glb_cubo


class TestRaster(unittest.TestCase):
    def test_area_triangulo(self):
        X = np.array([[10.0, 90.0, 10.0]]); Y = np.array([[10.0, 10.0, 90.0]]); Z = np.zeros((1, 3))
        tri, bary, _ = rasterizar(X, Y, Z, (100, 100))
        self.assertAlmostEqual((tri == 0).sum(), 80 * 80 / 2, delta=80)
        b = bary[tri == 0]
        self.assertTrue(np.allclose(b.sum(1), 1, atol=1e-5) and (b >= -1e-5).all())

    def test_gana_el_mas_cercano(self):
        X = np.array([[0.0, 50, 0], [0.0, 50, 0]]); Y = np.array([[0.0, 0, 50], [0.0, 0, 50]])
        Z = np.array([[0.0, 0, 0], [1.0, 1, 1]])
        tri, _, prof = rasterizar(X, Y, Z, (50, 50))
        self.assertTrue((tri[tri >= 0] == 1).all())
        self.assertTrue(np.allclose(prof[tri >= 0], 1))

    def test_triangulo_grande_fuera_de_cuadro(self):
        X = np.array([[-500.0, 1500, -500]]); Y = np.array([[-500.0, -500, 1500]]); Z = np.zeros((1, 3))
        tri, _, _ = rasterizar(X, Y, Z, (64, 64))
        self.assertTrue((tri == 0).all())


class TestVistas(unittest.TestCase):
    def test_codigo_ida_y_vuelta(self):
        for v in GUARDADAS.values():
            w = leer(v.codigo())
            self.assertEqual(w.codigo(), v.codigo())

    def test_cambios_sobre_guardada(self):
        v = leer("cara_34;modo=arcilla;tam=1024;ocultar=A,B")
        self.assertEqual((v.yaw, v.modo, v.tam, v.ocultar, v.region), (35, "arcilla", 1024, ("A", "B"), "cara"))

    def test_errores_claros(self):
        with self.assertRaises(KeyError):
            leer("no_existe")
        with self.assertRaises(ValueError):
            leer("frente;modo=acuarela")


class TestSesion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.glb = os.path.join(cls.dir.name, "cubo.glb")
        _glb_cubo(cls.glb)
        cls.s = Sesion(cls.glb)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_encuadre_fijo(self):
        r = self.s.render("yaw=0;elev=0;enc=2,0,0.5;clip=reposo;modo=clases;tam=200")
        ys, xs = np.nonzero(r.clases)
        self.assertAlmostEqual(xs.max() - xs.min() + 1, 100, delta=2)
        self.assertAlmostEqual(ys.max() - ys.min() + 1, 100, delta=2)
        self.assertTrue((r.clases[r.clases > 0] == paleta.PIEL).all())

    def test_igual_al_render_anterior(self):
        r = self.s.render("yaw=30;elev=20;enc=2,0,0.5;clip=reposo;modo=clases_tri;tam=160")
        C, _ = render_viejo(Escena(Modelo(self.glb)), r.cam, r.escala, r.centro, (160, 160))
        self.assertGreaterEqual((C == r.clases).mean(), 0.99)

    def test_todos_los_modos(self):
        for m in MODOS:
            r = self.s.render(f"yaw=30;elev=20;enc=2,0,0.5;clip=reposo;modo={m};tam=96")
            self.assertEqual(r.imagen.shape, (96, 96, 3), m)
            self.assertGreater(r.con_sello().shape[0], 96)

    def test_perspectiva(self):
        r = self.s.render("yaw=0;elev=0;dist=3;enc=2,0,0.5;clip=reposo;modo=clases;tam=200")
        ys, xs = np.nonzero(r.clases)
        self.assertGreater(xs.max() - xs.min() + 1, 100)  # la cara frontal está más cerca: se ve más grande

    def test_ab_mismo_modelo(self):
        _, info = lamina_ab(self.s, self.s, "yaw=30;elev=20;enc=2,0,0.5;clip=reposo;modo=arcilla;tam=96")
        self.assertAlmostEqual(info["iou"]["silueta"], 1.0)


class TestCompactar(unittest.TestCase):
    def test_quita_huerfanos(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c = (os.path.join(d, n) for n in ("a.glb", "b.glb", "c.glb"))
            _glb_cubo(a)
            # agrega 4 KB huérfanos, como dejan las ediciones
            raw = open(a, "rb").read()
            jl = struct.unpack("<I", raw[12:16])[0]
            j = json.loads(raw[20:20 + jl]); binc = raw[28 + jl:] + b"\0" * 4096
            j["buffers"][0]["byteLength"] = len(binc)
            j["bufferViews"].append({"buffer": 0, "byteOffset": len(binc) - 4096, "byteLength": 4096})
            js = json.dumps(j).encode(); js += b" " * (-len(js) % 4)
            with open(b, "wb") as fh:
                fh.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(binc)))
                fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binc), 0x004E4942) + binc)
            r = compactar(b, c)
            self.assertLess(r["bytes_despues"], r["bytes_antes"] - 4000)
            self.assertTrue(np.array_equal(Modelo(b).posar()[0], Modelo(c).posar()[0]))


class TestOrientar(unittest.TestCase):
    def test_voltea_cubo_invertido(self):
        from copox.medicion.gltf import leer_glb
        from copox.medicion.orientar import diagnostico, orientar
        with tempfile.TemporaryDirectory() as d:
            a, b, c = (os.path.join(d, n) for n in ("a.glb", "b.glb", "c.glb"))
            _glb_cubo(a)
            j, binc = leer_glb(a)
            inv = not diagnostico(j, binc)[0]["invertida"]
            # cubo con el orden de triángulos al revés
            raw = bytearray(open(a, "rb").read())
            jl = struct.unpack("<I", raw[12:16])[0]
            o = 28 + jl + 96
            F = np.frombuffer(bytes(raw[o:o + 72]), np.uint16).reshape(-1, 3)[:, ::-1].copy()
            raw[o:o + 72] = F.tobytes()
            open(b, "wb").write(raw)
            j, binc = leer_glb(b)
            self.assertNotEqual(diagnostico(j, binc)[0]["invertida"], not inv)
            if diagnostico(j, binc)[0]["invertida"]:
                orientar(b, c)
                j, binc = leer_glb(c)
                self.assertFalse(diagnostico(j, binc)[0]["invertida"])


if __name__ == "__main__":
    unittest.main()
