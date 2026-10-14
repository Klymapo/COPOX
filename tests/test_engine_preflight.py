"""Preflight opcional debe impedir trabajos profundos SIN romper cassettes existentes."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from copox import engine


class FakeCassette:
    id = "synthetic-preflight"
    kind = "framework_test"
    path = Path("synthetic.json")
    max_candidates = 1
    tournament_size = 1
    maturity = None

    def __init__(self, with_gate=True):
        self.data = {
            "target": "dummy",
            "baseline": "synthetic",
            "variables": {},
            "reporting": {"required_evidence": ["capture.png"]},
            "commands": {"mutate": ["mutate"], "execute": ["execute"], "capture": ["capture"]}
        }
        if with_gate:
            self.data["commands"]["preflight"] = ["preflight"]


class PreflightEngineTests(unittest.TestCase):
    def campaign(self, status, with_gate=True, write_report=True):
        calls = []
        cassette = FakeCassette(with_gate)
        with tempfile.TemporaryDirectory() as d:
            def run(command, ctx, cwd, env):
                phase = command[0]
                calls.append(phase)
                if phase == "preflight" and write_report:
                    Path(ctx["candidate_dir"], "preflight.json").write_text(
                        json.dumps({"status": status, "can_promote": False}))
                if phase == "capture":
                    Path(ctx["evidence_dir"], "capture.png").write_bytes(b"test")
            with patch.object(engine, "load_cassette", return_value=cassette), \
                 patch.object(engine, "_run_command", side_effect=run), \
                 patch.object(engine, "_audit_candidate", return_value=(True, 1.0, [])):
                code = engine.run_campaign("synthetic.json", output_root=d)
            manifests = list(Path(d).glob("*/*/manifest.json"))
            self.assertEqual(len(manifests), 1)
            manifest = json.loads(manifests[0].read_text())
            return code, calls, manifest

    def test_reject_early_skips_capture(self):
        code,calls,report=self.campaign("REJECTED_EARLY")
        self.assertEqual(code,2)
        self.assertEqual(calls,["mutate","execute","preflight"])
        self.assertEqual(report["status"],"PLATEAU")
        self.assertEqual(report["candidates"][0]["reason"],"preflight_gate")

    def test_accept_reaches_capture(self):
        code,calls,report=self.campaign("DEEP_ELIGIBLE")
        self.assertEqual(code,0)
        self.assertIn("capture",calls)
        self.assertEqual(report["candidates"][0]["status"],"ELIGIBLE")

    def test_missing_report_fails_closed(self):
        code,calls,report=self.campaign("DEEP_ELIGIBLE",write_report=False)
        self.assertEqual(code,2)
        self.assertNotIn("capture",calls)
        self.assertEqual(report["candidates"][0]["status"],"ERROR")

    def test_invalid_status_does_not_pass(self):
        code,calls,report=self.campaign("PASS")
        self.assertEqual(code,2)
        self.assertNotIn("capture",calls)

    def test_legacy_without_preflight_still_captures(self):
        code,calls,report=self.campaign(None,with_gate=False)
        self.assertEqual(code,0)
        self.assertEqual(calls,["mutate","execute","capture"])
        self.assertEqual(report["status"],"PROMOTED")


if __name__ == "__main__":
    unittest.main()
