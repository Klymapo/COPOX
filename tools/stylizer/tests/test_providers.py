import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mesh_service import reconstruct
from mesh_generator import predict_bounded
from mesh_generator_threews import generate_3d_mesh_threews, response_json
import test_pipeline as helpers


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "model.glb"

    def test_auto_falls_back_after_exception(self):
        with patch("mesh_generator.generate_3d_mesh", side_effect=RuntimeError("quota")), patch("mesh_generator_threews.generate_3d_mesh_threews", side_effect=helpers.PipelineTests.generate_mesh) as fallback:
            result = reconstruct("source.png", self.output)
        fallback.assert_called_once()
        self.assertEqual(result["provider"], "threews")
        self.assertEqual(len(result["attempts"]), 2)

    def test_success_does_not_use_fallback(self):
        with patch("mesh_generator.generate_3d_mesh", side_effect=helpers.PipelineTests.generate_mesh), patch("mesh_generator_threews.generate_3d_mesh_threews") as fallback:
            result = reconstruct("source.png", self.output)
        fallback.assert_not_called()
        self.assertEqual(result["provider"], "trellis")

    def test_explicit_provider_failure_stays_with_that_provider(self):
        with patch("mesh_generator.generate_3d_mesh", return_value=False), patch("mesh_generator_threews.generate_3d_mesh_threews") as fallback:
            result = reconstruct("source.png", self.output, "trellis")
        fallback.assert_not_called()
        self.assertIsNone(result["model"])

    def test_corrupt_download_is_not_reported_as_success(self):
        def bad_download(image_path, output_file):
            Path(output_file).write_text("<html>Error</html>")
            return True
        with patch("mesh_generator.generate_3d_mesh", side_effect=bad_download):
            result = reconstruct("source.png", self.output, "trellis")
        self.assertIsNone(result["model"])
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_name("model.partial.glb").exists())

    def test_threews_accepts_inline_completion_without_job_id(self):
        with patch("mesh_generator_threews.upload_image_to_threews", return_value="https://example.com/a.png"), patch("mesh_generator_threews.request_job", return_value=(None, {"status": "done", "glbUrl": "https://example.com/a.glb"})), patch("mesh_generator_threews.wait_for_job") as poll, patch("mesh_generator_threews.download_glb", return_value=True) as download:
            self.assertTrue(generate_3d_mesh_threews("image.png"))
        poll.assert_not_called()
        download.assert_called_once()

    def test_payment_required_stops(self):
        with self.assertRaisesRegex(RuntimeError, "solicita pago"):
            response_json(Mock(status_code=402))

    def test_timeout_requests_cancellation(self):
        client = Mock()
        client.submit.return_value.result.side_effect = TimeoutError("wait expired")
        with self.assertRaisesRegex(TimeoutError, "10 minutos"):
            predict_bounded(client, api_name="/image_to_3d")
        client.submit.return_value.cancel.assert_called_once()

    def test_failed_provider_does_not_persist_credentials(self):
        with patch.dict("os.environ", {"HF_TOKEN": "test-only-secret"}), patch("mesh_generator.generate_3d_mesh", side_effect=RuntimeError("token test-only-secret")):
            result = reconstruct("source.png", self.output, "trellis")
        self.assertNotIn("test-only-secret", str(result))
        self.assertIn("[oculto]", result["attempts"][0]["error"])


if __name__ == "__main__":
    unittest.main()
