import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
from fidelity import ASPECTS, save_review


class FidelityTests(unittest.TestCase):
    def test_review_keeps_versions_and_packages_reference_snapshots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "image.png"
            Image.new("RGB", (8, 8), "red").save(image)
            (root / "model.glb").write_bytes(b"test-model")
            (root / "manifest.json").write_text("{}")
            run = {"id": "test", "directory": temp, "image": str(image), "model": str(root / "model.glb")}
            ratings = {aspect: "Sin evaluar" for aspect in ASPECTS}
            ratings[ASPECTS[0]] = "Coincide"
            ratings[ASPECTS[1]] = "Corregir"
            path, plan, archive = save_review(run, {"front": image}, ratings, "Acortar cabello.")
            first = json.loads(Path(path).read_text())
            self.assertIn("Conservar: Silueta y proporciones", plan)
            self.assertEqual(len(first["model_sha256"]), 64)
            copied = root / first["references"]["front"]["path"]
            original = copied.read_bytes()
            Image.new("RGB", (8, 8), "blue").save(image)
            second, _, archive = save_review(run, {"front": image}, ratings, "Segunda revisión.")
            self.assertNotEqual(path, second)
            self.assertEqual(copied.read_bytes(), original)
            with ZipFile(archive) as bundle:
                self.assertIn(Path(path).name, bundle.namelist())
                self.assertIn(Path(second).name, bundle.namelist())
                self.assertIn(first["references"]["front"]["path"], bundle.namelist())

    def test_review_requires_a_model(self):
        with self.assertRaisesRegex(ValueError, "generación 3D"):
            save_review(None, {}, {aspect: "Sin evaluar" for aspect in ASPECTS})
