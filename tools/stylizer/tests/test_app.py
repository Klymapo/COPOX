"""Authenticated HTTP round trip across two independent browser sessions."""

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import httpx
from PIL import Image
import test_pipeline as helpers
from jobs import JobManager


class AppTests(unittest.TestCase):
    def test_mobile_session_sees_pc_job_and_downloads_after_disconnect(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost", "GRADIO_ANALYTICS_ENABLED": "False"}):
            import app
            from gradio_client import Client, handle_file

            root = Path(temp)
            source = root / "reference.png"
            Image.new("RGB", (16, 16), "red").save(source)
            started, finish = threading.Event(), threading.Event()

            def generate(image_path, output_file):
                started.set()
                if not finish.wait(15):
                    raise RuntimeError("Test did not release provider")
                return helpers.PipelineTests.generate_mesh(image_path, output_file)

            manager = JobManager(root / "data", root / "runs")
            app._peticiones.clear()
            pc = phone = None
            with patch.object(app, "_manager", manager), patch("mesh_generator.generate_3d_mesh", side_effect=RuntimeError("quota")), patch("mesh_generator_threews.generate_3d_mesh_threews", side_effect=generate):
                try:
                    _, url, _ = app.demo.queue().launch(
                        share=False, server_name="127.0.0.1", server_port=None,
                        prevent_thread_lock=True, quiet=True, allowed_paths=[str(root / "runs")],
                        auth=("tester", "local-test-password"), blocked_paths=[str(root / "data")],
                    )
                    with self.assertRaises(ValueError):
                        Client(url, verbose=False, httpx_kwargs={"trust_env": False})
                    options = {"auth": ("tester", "local-test-password"), "verbose": False,
                               "httpx_kwargs": {"trust_env": False}, "download_files": root / "downloads"}
                    pc, phone = Client(url, **options), Client(url, **options)
                    submitted = pc.predict("image", "", handle_file(str(source)), "auto", api_name="/generate")
                    identifier = submitted[0]["value"]
                    self.assertTrue(started.wait(5))
                    pc.close()
                    pc = None
                    state = phone.predict(None, api_name="/status")
                    self.assertEqual(state[0]["value"], identifier)
                    self.assertIn("En curso", state[1])
                    self.assertIn("threews", state[1])
                    finish.set()
                    deadline = time.monotonic() + 10
                    while manager.get(identifier)["status"] == "running" and time.monotonic() < deadline:
                        time.sleep(.05)
                    self.assertEqual(manager.get(identifier)["status"], "completed")
                    state = phone.predict(identifier, api_name="/status")
                    self.assertIn("Completada", state[1])
                    result = phone.predict(identifier, api_name="/open")
                    with ZipFile(result[1]) as bundle:
                        self.assertIn("model.glb", bundle.namelist())
                        self.assertIn("image.png", bundle.namelist())
                    # Knowing an output URL does not bypass the web password.
                    private_file = manager.get(identifier)["result"]["model"]
                    response = httpx.get(url + "gradio_api/file=" + private_file, trust_env=False)
                    self.assertEqual(response.status_code, 401)
                    review = phone.predict(
                        handle_file(str(source)), None, None,
                        "Coincide", "Corregir", "Sin evaluar", "Sin evaluar", "Sin evaluar",
                        "Acortar cabello.", api_name="/review",
                    )
                    self.assertIn("Acortar cabello", review[0])
                    with ZipFile(review[3]) as bundle:
                        self.assertTrue(any(name.startswith("review_") for name in bundle.namelist()))
                        self.assertTrue(any(name.startswith("references/") for name in bundle.namelist()))
                    retry = phone.predict(identifier, "auto", api_name="/retry")
                    self.assertNotEqual(identifier, retry[0]["value"])
                    self.assertEqual(manager.get(retry[0]["value"])["request"]["idea"], None)
                finally:
                    finish.set()
                    if pc:
                        pc.close()
                    if phone:
                        phone.close()
                    app.demo.close()
                    manager.close()
