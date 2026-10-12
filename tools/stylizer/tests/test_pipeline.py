import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pipeline_core import run_pipeline


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        Image.new("RGBA", (8, 8), (255, 0, 0, 120)).save(self.source)

    @staticmethod
    def generate_mesh(image_path, output_file):
        data = json.dumps({"asset": {"version": "2.0"}, "scene": 0, "scenes": [{}]}).encode()
        data += b" " * (-len(data) % 4)
        Path(output_file).write_bytes(struct.pack("<4sIIII", b"glTF", 2, 20 + len(data), len(data), 0x4E4F534A) + data)
        return True

    def test_image_mode_skips_text_services_and_preserves_alpha(self):
        with patch("prompt_stylizer.stylize") as stylize, patch("image_generator_agnes.generate_image_agnes") as agnes, patch("mesh_generator.generate_3d_mesh", side_effect=self.generate_mesh):
            run = run_pipeline(image_path=self.source, provider="trellis", output_root=self.root / "runs")
        self.assertEqual(run["status"], "completed")
        stylize.assert_not_called()
        agnes.assert_not_called()
        with Image.open(run["image"]) as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 120))
        self.assertEqual(json.loads((Path(run["directory"]) / "manifest.json").read_text())["source"], "image")

    def test_text_flow_still_generates_prompt_image_and_model(self):
        def generate_image(prompt, output_file):
            Image.new("RGB", (8, 8), "red").save(output_file)
            return True
        with patch("prompt_stylizer.stylize", return_value="A red toy"), patch("image_generator_agnes.generate_image_agnes", side_effect=generate_image), patch("mesh_generator.generate_3d_mesh", side_effect=self.generate_mesh):
            run = run_pipeline(idea="Un juguete rojo", provider="trellis", output_root=self.root / "runs")
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["prompt"], "A red toy")
        self.assertTrue((Path(run["directory"]) / "prompt.json").is_file())

    def test_missing_key_returns_error_instead_of_exiting_app(self):
        with patch.dict("os.environ", {}, clear=True), patch("prompt_stylizer.stylize", return_value="A red toy"):
            run = run_pipeline(idea="juguete", output_root=self.root / "runs")
        self.assertEqual(run["status"], "failed")
        self.assertIn("AGNES_API_KEY", run["error"])

    def test_failed_reconstruction_keeps_image(self):
        with patch("mesh_generator.generate_3d_mesh", return_value=False):
            run = run_pipeline(image_path=self.source, provider="trellis", output_root=self.root / "runs")
        self.assertEqual(run["status"], "failed")
        self.assertTrue(Path(run["image"]).is_file())
        self.assertIsNone(run["model"])

    def test_invalid_image_does_not_call_provider(self):
        invalid = self.root / "invalid.png"
        invalid.write_text("not an image")
        with patch("mesh_generator.generate_3d_mesh") as mesh:
            run = run_pipeline(image_path=invalid, output_root=self.root / "runs")
        self.assertEqual(run["status"], "failed")
        mesh.assert_not_called()

    def test_input_is_exclusive(self):
        for kwargs in ({}, {"idea": "toy", "image_path": self.source}):
            with self.assertRaises(ValueError):
                run_pipeline(**kwargs, output_root=self.root / "runs")


if __name__ == "__main__":
    unittest.main()
