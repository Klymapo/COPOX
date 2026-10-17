"""Pruebas del motor de medición v2 (solo NumPy/Pillow, datos sintéticos)."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from copox.medicion import paleta, piezas
from copox.medicion.camara import Camara
from copox.medicion.gltf import Modelo
from copox.medicion.raster import Escena, render


def _glb_cubo(path, color=(0.95, 0.56, 0.34, 1.0)):
    """Cubo unitario (lado 1, base en y=0) con un material de color plano."""
    v = np.array([[x, y, z] for x in (-.5, .5) for y in (0, 1) for z in (-.5, .5)], np.float32)
    f = np.array([[0, 2, 3], [0, 3, 1], [4, 5, 7], [4, 7, 6], [0, 1, 5], [0, 5, 4], [2, 6, 7], [2, 7, 3], [0, 4, 6], [0, 6, 2], [1, 3, 7], [1, 7, 5]], np.uint16)
    binb = v.tobytes() + f.tobytes()
    j = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "cubo"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
         "materials": [{"pbrMetallicRoughness": {"baseColorFactor": list(color)}}],
         "buffers": [{"byteLength": len(binb)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": v.nbytes}, {"buffer": 0, "byteOffset": v.nbytes, "byteLength": f.nbytes}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-.5, 0, -.5], "max": [.5, 1, .5]},
                       {"bufferView": 1, "componentType": 5123, "count": 36, "type": "SCALAR"}]}
    js = json.dumps(j).encode()
    js += b" " * (-len(js) % 4)
    binb += b"\0" * (-len(binb) % 4)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(binb)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(binb), 0x004E4942) + binb)


class TestCamara(unittest.TestCase):
    def test_frente_ortografica(self):
        x, y, _ = Camara(yaw=0, objetivo=(0, 0, 0)).proyectar(np.array([[1.0, 2.0, 0.0]]))
        self.assertAlmostEqual(float(x[0]), 1.0)
        self.assertAlmostEqual(float(y[0]), 2.0)

    def test_perfil_ve_profundidad(self):
        x, _, _ = Camara(yaw=90, objetivo=(0, 0, 0)).proyectar(np.array([[0.0, 0.0, 1.0]]))
        self.assertAlmostEqual(abs(float(x[0])), 1.0, places=6)

    def test_perspectiva_agranda_lo_cercano(self):
        cam = Camara(yaw=0, distancia=2.0, objetivo=(0, 0, 0))
        xc, _, _ = cam.proyectar(np.array([[1.0, 0.0, 0.5]]))
        xl, _, _ = cam.proyectar(np.array([[1.0, 0.0, -0.5]]))
        self.assertGreater(float(xc[0]), float(xl[0]))


class TestPaleta(unittest.TestCase):
    def test_colores_alth(self):
        rgb = np.array([[[251, 195, 156], [239, 201, 137], [40, 40, 40], [74, 87, 112], [250, 245, 238]]])
        self.assertEqual(paleta.clasificar(rgb)[0].tolist(), [paleta.PIEL, paleta.PELO, paleta.OSCURO, paleta.AZUL, paleta.CLARO])

    def test_fondo_y_hueco_encerrado(self):
        img = np.full((60, 60, 3), 230, np.uint8)
        img[10:50, 10:50] = (74, 87, 112)
        img[20:40, 20:40] = 230  # hueco gris encerrado
        C = paleta.segmentar_referencia(img, hueco_min=0.01)
        self.assertEqual(C[0, 0], paleta.FONDO)
        self.assertEqual(C[30, 30], paleta.FONDO)
        self.assertEqual(C[15, 15], paleta.AZUL)


class TestPiezas(unittest.TestCase):
    def test_ojos_y_perfil(self):
        C = np.zeros((200, 200), np.uint8)
        C[20:190, 50:150] = paleta.PIEL
        C[60:75, 70:82] = paleta.OSCURO
        C[60:75, 118:130] = paleta.OSCURO
        C[40:44, 70:84] = paleta.OSCURO  # ceja (fina) no debe confundirse
        o = piezas.ojos(C)
        self.assertEqual(len(o), 2)
        ed = o[1]["cx"] - o[0]["cx"]
        self.assertAlmostEqual(ed, 48.0, delta=1)
        filas = piezas.perfil_anchos(C, 67, ed, 100, np.array([0.0, 1.0]))
        self.assertAlmostEqual(filas[0][2], 100 / ed, delta=0.05)


class TestModelo(unittest.TestCase):
    def test_render_cubo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cubo.glb"
            _glb_cubo(p)
            esc = Escena(Modelo(str(p)))
            self.assertEqual(len(esc.T), 12)
            self.assertTrue((esc.clase == paleta.PIEL).all())
            C, _ = render(esc, Camara(yaw=0, objetivo=(0, 0.5, 0)), 100, (100, 100), (200, 200))
            ys, xs = np.nonzero(C)
            self.assertAlmostEqual(xs.max() - xs.min() + 1, 100, delta=2)
            self.assertAlmostEqual(ys.max() - ys.min() + 1, 100, delta=2)


if __name__ == "__main__":
    unittest.main()
