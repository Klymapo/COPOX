"""Queue persistence and failures; never contacts generation providers."""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from jobs import JobManager
from pipeline_core import run_pipeline
import test_pipeline as helpers


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "input.png"
        Image.new("RGB", (8, 8), "blue").save(self.source)

    def manager(self, start=False):
        manager = JobManager(self.root / "data", self.root / "runs", start=start)
        self.addCleanup(manager.close)
        return manager

    def wait_for(self, manager, identifier):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            job = manager.get(identifier)
            if job["status"] not in ("queued", "running"):
                return job
            time.sleep(.02)
        self.fail("Queue did not finish")

    def test_upload_and_queue_survive_restart(self):
        first = self.manager()
        identifier = first.submit_generation(image_path=self.source, provider="trellis")
        self.source.unlink()
        first.close()
        with patch("mesh_generator.generate_3d_mesh", side_effect=helpers.PipelineTests.generate_mesh):
            second = self.manager(start=True)
            result = self.wait_for(second, identifier)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(Path(result["result"]["image"]).exists())

    def test_running_job_is_interrupted_not_resubmitted(self):
        first = self.manager()
        identifier = first.submit_generation(image_path=self.source)
        first._next()  # Simulate shutdown while remote work was running.
        first.close()
        with patch("jobs.run_pipeline") as pipeline:
            second = self.manager(start=True)
            self.assertEqual(second.get(identifier)["status"], "interrupted")
            pipeline.assert_not_called()

    def test_worker_recovers_after_failure_and_redacts_secrets(self):
        first = self.manager()
        failed = first.submit_generation(image_path=self.source, provider="trellis")
        success = first.submit_generation(image_path=self.source, provider="trellis")
        first.close()
        with patch.dict(os.environ, {"HF_TOKEN": "fake-secret-only-for-test"}):
            # A worker-level crash must not prevent the next pipeline from running.
            original = run_pipeline
            calls = 0

            def run(**kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise RuntimeError("worker fake-secret-only-for-test")
                with patch("mesh_generator.generate_3d_mesh", side_effect=helpers.PipelineTests.generate_mesh):
                    return original(**kwargs)

            with patch("jobs.run_pipeline", side_effect=run):
                second = self.manager(start=True)
                self.assertEqual(self.wait_for(second, success)["status"], "completed")
                failure = second.get(failed)
                self.assertEqual(failure["status"], "failed")
                self.assertNotIn("fake-secret-only-for-test", failure["error"])
                self.assertIn("[oculto]", failure["error"])

    def test_one_worker_and_queue_limit(self):
        manager = self.manager()
        with self.assertRaises(RuntimeError):
            JobManager(self.root / "data", self.root / "runs", start=False)
        for number in range(20):
            manager.submit_generation(idea=f"model {number}")
        with self.assertRaises(ValueError):
            manager.submit_generation(image_path=self.source)
        self.assertEqual(len(manager.recent()), 20)
        self.assertEqual(list((self.root / "data" / "inputs").iterdir()), [])

    def test_godot_options_reject_fractional_and_nonfinite_values(self):
        manager = self.manager()
        for values in ({"height": 0}, {"yaw": float("nan")}, {"triangle_limit": 1.5}, {"triangle_limit": float("inf")}):
            with self.assertRaises(ValueError):
                manager.submit_godot(source="unused.glb", **values)
        self.assertEqual(manager.recent(), [])

    def test_previous_generations_import_and_retry_without_text_services(self):
        with patch("mesh_generator.generate_3d_mesh", side_effect=helpers.PipelineTests.generate_mesh):
            run = run_pipeline(image_path=self.source, provider="trellis", output_root=self.root / "runs")
        manager = self.manager()
        self.assertEqual(manager.get(run["id"])["status"], "completed")
        retried = manager.retry(run["id"])
        self.assertIsNone(manager.get(retried)["request"]["idea"])
        self.assertTrue(Path(manager.get(retried)["request"]["image_path"]).exists())
