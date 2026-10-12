"""Cloud entry point, authentication, private storage and a complete HTTP task."""

import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from config import settings, validate_server_config
from prompt_stylizer import stylize


class ServerConfigTests(unittest.TestCase):
    def test_hosting_port_and_explicit_override(self):
        with patch.dict(os.environ, {"PORT": "10000", "STYLIZER_PORT": ""}):
            self.assertEqual(settings().port, 10000)
            os.environ["STYLIZER_PORT"] = "7861"
            self.assertEqual(settings().port, 7861)

    def test_server_rejects_missing_password_and_overlapping_storage(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {
            "STYLIZER_DATA_DIR": temp + "/private", "STYLIZER_OUTPUT_DIR": temp + "/outputs",
            "STYLIZER_USER": "tester", "STYLIZER_PASSWORD": "",
        }):
            with self.assertRaisesRegex(ValueError, "12 caracteres"):
                validate_server_config(settings())
            os.environ["STYLIZER_PASSWORD"] = "server-test-password"
            os.environ["STYLIZER_OUTPUT_DIR"] = temp + "/private/outputs"
            with self.assertRaisesRegex(ValueError, "carpetas separadas"):
                validate_server_config(settings())

    def test_template_prompt_works_without_ollama(self):
        with patch.dict(os.environ, {"STYLIZER_PROMPT_MODE": "template"}), patch("prompt_stylizer.requests.post") as post:
            prompt = stylize("robot jardinero azul")
        self.assertIn("robot jardinero azul", prompt)
        self.assertIn("white background", prompt)
        post.assert_not_called()


class ServerHTTPTests(unittest.TestCase):
    def test_cloud_auth_generation_download_and_private_storage(self):
        import httpx
        import uvicorn
        from gradio_client import Client
        from PIL import Image
        import app
        from server import create_app
        import test_pipeline as helpers

        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {
            "STYLIZER_DATA_DIR": temp + "/private", "STYLIZER_OUTPUT_DIR": temp + "/outputs",
            "STYLIZER_USER": "tester", "STYLIZER_PASSWORD": "server-test-password",
            "STYLIZER_PROMPT_MODE": "template", "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost", "GRADIO_ANALYTICS_ENABLED": "False",
        }), patch.object(app, "_manager", None):
            app._peticiones.clear()
            def generate_image(prompt, output_file):
                Image.new("RGB", (16, 16), "blue").save(output_file)
                return True

            with patch("image_generator_agnes.generate_image_agnes", side_effect=generate_image), patch("mesh_generator.generate_3d_mesh", side_effect=helpers.PipelineTests.generate_mesh), patch("prompt_stylizer.requests.post") as ollama:
                application = create_app()
                listener = socket.socket()
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
                server = uvicorn.Server(uvicorn.Config(application, log_level="error", lifespan="on"))
                worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
                worker.start()
                client = None
                try:
                    deadline = time.monotonic() + 10
                    while not server.started and time.monotonic() < deadline:
                        time.sleep(.05)
                    self.assertTrue(server.started)
                    url = f"http://127.0.0.1:{port}/"
                    with httpx.Client(base_url=url, trust_env=False) as browser:
                        health = browser.get("healthz")
                        self.assertEqual(health.status_code, 200)
                        self.assertEqual(health.json(), {"status": "ok"})
                        self.assertEqual(health.headers["cache-control"], "no-store")
                        self.assertEqual(browser.post("login", data={"username": "tester", "password": "wrong"}).status_code, 400)
                        self.assertEqual(browser.get("gradio_api/info").status_code, 401)
                        self.assertEqual(browser.post("login", data={"username": "tester", "password": "server-test-password"}).status_code, 200)
                        database = str(app.get_manager().database)
                        self.assertEqual(browser.get("gradio_api/file=" + database).status_code, 403)

                    client = Client(url, auth=("tester", "server-test-password"), verbose=False,
                                    httpx_kwargs={"trust_env": False}, download_files=Path(temp) / "downloads")
                    queued = client.predict("text", "robot jardinero azul", None, "trellis", api_name="/generate")
                    identifier = queued[0]["value"]
                    deadline = time.monotonic() + 10
                    while app.get_manager().get(identifier)["status"] in ("queued", "running") and time.monotonic() < deadline:
                        time.sleep(.05)
                    self.assertEqual(app.get_manager().get(identifier)["status"], "completed")
                    client.predict(identifier, api_name="/status")
                    result = client.predict(identifier, api_name="/open")
                    with ZipFile(result[1]) as bundle:
                        self.assertIn("model.glb", bundle.namelist())
                        self.assertIn("prompt.json", bundle.namelist())
                    self.assertIn("robot jardinero azul", result[4])
                    ollama.assert_not_called()
                finally:
                    if client:
                        client.close()
                    server.should_exit = True
                    worker.join(timeout=15)
                    listener.close()
                    self.assertFalse(worker.is_alive())
