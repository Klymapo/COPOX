"""Ejemplo reproducible que no utiliza red, pagos ni modelos previos."""
import json
import tempfile
import unittest
from pathlib import Path

from alth_bridge import create_candidate, describe_glb
from examples.build_cube import build_cube


class ExampleCubeTests(unittest.TestCase):
    def test_cube_glb_is_reproducible_and_valid_for_alth_bridge(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first = build_cube(base / "one.glb")
            second = build_cube(base / "two.glb")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            info = describe_glb(first)
            self.assertEqual(info["mesh_type"], "static_or_unidentified")
            self.assertGreater(info["size_bytes"], 1000)
            result = create_candidate(first, base / "reports", "neutral-cube")
            record = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(record["approval_state"], "UNREVIEWED")
            self.assertEqual(record["audits"]["scale"], "PENDING")
            self.assertEqual(record["source"]["sha256"], info["sha256"])


if __name__ == "__main__":
    unittest.main()
