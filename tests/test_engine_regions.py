"""COPOX Engine: aceptar trabajo por pieza, nunca promover GLB completo."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from copox import engine


class RegionCassette:
    id="regional-nuca-test"
    kind="geometry"
    path=Path("regional-cassette.json")
    max_candidates=1
    tournament_size=1
    maturity=None
    @property
    def auditors(self):
        return [
          {"id":"nuca-geometry","region":"nuca","critical":True,"command":["audit","nuca-geometry"]},
          {"id":"face-likeness","region":"rostro","critical":True,"command":["audit","face-likeness"]},
          {"id":"shared-rig","scope":"global_safety","critical":True,"command":["audit","shared-rig"]},
        ]
    def __init__(self):
        self.data={
          "target":"maniqui-r3",
          "baseline":"r3",
          "variables":{},
          "evaluation":{"scope":"region","region":"nuca"},
          "reporting":{"required_evidence":["fourviews.png"]},
          "commands":{
             "mutate":["mutate"],"execute":["execute"],"preflight":["preflight"],
             "capture":["capture"],"promote":["promote"],"report":["report"]
          }
        }


class RegionEngineTests(unittest.TestCase):
    def run_it(self,*,nuca_pass=True,safety_pass=True,disable_safety=False):
        cass=RegionCassette()
        if disable_safety:
            class NoSafetyCassette(RegionCassette):
                @property
                def auditors(self):
                    items=super().auditors
                    for item in items:
                        if item.get("scope")=="global_safety":
                            item["applicable"]=False
                    return items
            cass=NoSafetyCassette()
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            def simulate(command, ctx, cwd, env):
                calls.append(tuple(command))
                phase=command[0]
                if phase=="capture":
                    Path(ctx["evidence_dir"],"fourviews.png").write_bytes(b"fixture")
                elif phase=="preflight":
                    Path(ctx["candidate_dir"],"preflight.json").write_text(json.dumps({"status":"DEEP_ELIGIBLE"}))
                elif phase=="audit":
                    name=command[1]
                    result={"status":"PASS"}
                    if name=="nuca-geometry" and not nuca_pass:result["status"]="FAIL"
                    if name=="shared-rig" and not safety_pass:result["status"]="FAIL"
                    if name=="face-likeness":result["status"]="FAIL" # must NEVER execute
                    Path(ctx["audit_result"]).write_text(json.dumps(result))
            with patch.object(engine,"load_cassette",return_value=cass),patch.object(engine,"_run_command",side_effect=simulate):
                code=engine.run_campaign("region.json",output_root=d)
            [manifest_file]=list(Path(d).glob("*/*/manifest.json"))
            return code,calls,json.loads(manifest_file.read_text())

    def test_face_rejected_does_not_block_successful_nape(self):
        code,calls,manifest=self.run_it()
        self.assertEqual(code,0)
        self.assertEqual(manifest["status"],"LOCAL_QA_READY_FOR_REVIEW")
        self.assertFalse(manifest["promotion_allowed"])
        self.assertEqual(manifest["candidates"][0]["status"],"LOCAL_ELIGIBLE")
        self.assertNotIn(("audit","face-likeness"),calls)
        self.assertNotIn(("promote",),calls)
        audit=manifest["candidates"][0]["audit"]
        self.assertTrue(any(x["id"]=="face-likeness" and x["status"]=="N-A" for x in audit))
        self.assertIn(("audit","shared-rig"),calls)

    def test_nape_fails_even_if_face_skipped(self):
        code,calls,manifest=self.run_it(nuca_pass=False)
        self.assertEqual(code,2)
        self.assertEqual(manifest["status"],"PLATEAU")
        self.assertNotIn(("promote",),calls)

    def test_disabled_shared_safety_cannot_count_as_passed(self):
        code,calls,manifest=self.run_it(disable_safety=True)
        self.assertEqual(code,2)
        self.assertEqual(manifest["status"],"PLATEAU")
        self.assertNotIn(("promote",),calls)

    def test_shared_safety_failure_blocks_nape(self):
        code,calls,manifest=self.run_it(safety_pass=False)
        self.assertEqual(code,2)
        self.assertEqual(manifest["status"],"PLATEAU")
        self.assertIn(("audit","shared-rig"),calls)
        self.assertNotIn(("promote",),calls)


if __name__=="__main__": unittest.main()
