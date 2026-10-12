"""No-network bridge tests; Blender and API providers are not required."""
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from alth_bridge import APPROVED_ASSETS, SPEC_PATH, create_candidate, describe_glb


def minimal_glb(path, *, rigged=False):
    gltf = {"asset": {"version": "2.0"}, "meshes": [{"primitives": [{}]}]}
    if rigged:
        gltf["skins"] = [{"joints": [0]}]
        gltf["nodes"] = [{}]
    payload = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    payload += b" " * ((-len(payload)) % 4)
    size = 12 + 8 + len(payload)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, size) +
                     struct.pack("<II", len(payload), 0x4E4F534A) + payload)
    return path


class ALTHBridgeTests(unittest.TestCase):
    def test_spec_uses_frozen_v2(self):
        self.assertEqual(json.loads(SPEC_PATH.read_text(encoding="utf-8"))["version"], "2.0")

    def test_creates_unreviewed_manifest_without_changing_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = minimal_glb(base / "model.glb")
            before = hashlib.sha256(src.read_bytes()).hexdigest()
            report = create_candidate(src, base / "manifest", "theo-proposal-1")
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["source"]["sha256"], before)
            self.assertEqual(data["alth_spec_version"], "2.0")
            self.assertEqual(data["approval_state"], "UNREVIEWED")
            self.assertEqual(data["audits"]["scale"], "PENDING")
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(), before)
            with self.assertRaises(FileExistsError):
                create_candidate(src, base / "manifest", "theo-proposal-1")

    def test_detects_rig_and_does_not_process_it_as_static(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = minimal_glb(Path(tmp) / "rig.glb", rigged=True)
            self.assertEqual(describe_glb(src)["mesh_type"], "rigged_or_animated")
            data = json.loads(create_candidate(src, Path(tmp) / "out", "rigged").read_text())
            self.assertEqual(data["audits"]["rig_integrity"], "PENDING")

    def test_refuses_approved_assets_and_unsafe_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = minimal_glb(Path(tmp) / "model.glb")
            with self.assertRaises(ValueError):
                create_candidate(src, APPROVED_ASSETS / "joven_rubio", "proposal")
            with self.assertRaises(ValueError):
                create_candidate(src, Path(tmp) / "other", "../bad")


if __name__ == "__main__":
    unittest.main()
