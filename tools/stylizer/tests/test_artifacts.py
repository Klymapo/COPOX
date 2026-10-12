import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from artifacts import artifact_paths, package_run


class ArtifactTests(unittest.TestCase):
    def test_package_is_complete_and_excludes_partial_and_private_files(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for filename in ["manifest.json", "prompt.json", "image.png", "model.glb", "model.partial.glb", ".env"]:
                (directory / filename).write_text("test")
            run = {"id": "run", "directory": temp, "image": str(directory / "image.png"), "model": str(directory / "model.glb")}
            package_run(run)
            archive = package_run(run)
            with ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()), {"manifest.json", "prompt.json", "image.png", "model.glb"})
            self.assertEqual(len(artifact_paths(run)), 4)

    def test_failed_run_still_has_downloadable_image(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "manifest.json").write_text("{}")
            (directory / "image.png").write_bytes(b"saved input")
            # A leftover failed download must not be offered as a model.
            (directory / "model.glb").write_text("invalid")
            run = {"id": "failed", "directory": temp, "image": str(directory / "image.png"), "model": None}
            with ZipFile(package_run(run)) as bundle:
                self.assertEqual(set(bundle.namelist()), {"manifest.json", "image.png"})


if __name__ == "__main__":
    unittest.main()
