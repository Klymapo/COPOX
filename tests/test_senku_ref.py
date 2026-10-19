"""SENKU senku_ref: la hoja de Theo y el pelo aprobado (ADAN_V49_PELO_THEO) deben seguir midiendo igual.
Requiere los GLB en ../copox-modelos (se salta si no están)."""
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(RAIZ, "..", "copox-modelos", "adan", "ADAN_V49_PELO_THEO.glb")
HOJA = os.path.join(RAIZ, "refs", "personajes", "joven-rubio-4-vistas.jpg")
OCULTAR = ("CAPA_GUIA_CAPILAR", "CAPA_PELO_CORTO", "CAPA_PELO_MECHONES", "PIES_DESCALZOS")


@unittest.skipUnless(os.path.exists(GLB), "falta copox-modelos")
class TestSenkuRef(unittest.TestCase):
    def test_cabeza_theo(self):
        from copox.medicion import senku_ref as sr
        r = sr.auditar(GLB, HOJA, "cabeza", OCULTAR)
        self.assertGreater(r["iou"]["media"], 0.88)
        for v in ("frente", "perfil", "espalda"):
            self.assertGreater(r["iou"][v]["pelo"], 0.88)
        self.assertTrue(any("tres_cuartos" in a for a in r["avisos"]))

    def test_una_vista(self):
        from copox.medicion import senku_ref as sr
        r = sr.auditar(GLB, os.path.join(RAIZ, "refs", "personajes", "detective.jpg"), "objeto", OCULTAR)
        self.assertEqual(r["iou"]["perfil"], "N-A")
        self.assertTrue(any("SUPUESTA" in a for a in r["avisos"]))


if __name__ == "__main__":
    unittest.main()
