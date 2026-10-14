import unittest
from copox.geometry.provenance_gate import evaluate_manifest,ProvenanceError


class TestProvenance(unittest.TestCase):
    def test_gamma_ancestry_blocks_clean_claim(self):
        doc={"target":"r3","nodes":[
            {"id":"gamma","origin":"third_party"},
            {"id":"beta","origin":"original","rights_evidence":"ownership-record"},
            {"id":"delta","origin":"derived","parents":["gamma","beta"]},
            {"id":"r3","origin":"derived","parents":["delta"]}
        ]}
        r=evaluate_manifest(doc)
        self.assertEqual(r["status"],"PROVENANCE_BLOCKED")
        self.assertFalse(r["independent_verified"])
        self.assertTrue(any(b["id"]=="gamma" for b in r["blockers"]))

    def test_new_original_assembly_only_ready_for_review(self):
        doc={"target":"new","nodes":[
            {"id":"new","origin":"derived","parents":["own-rig","own-mesh"]},
            {"id":"own-rig","origin":"original","rights_evidence":"rig-creation-log"},
            {"id":"own-mesh","origin":"original","rights_evidence":"geometry-sources-log"}
        ]}
        r=evaluate_manifest(doc)
        self.assertEqual(r["status"],"ORIGIN_REVIEW_READY")
        self.assertFalse(r["independent_verified"])
        self.assertFalse(r["release_approved"])

    def test_unverified_input_blocks(self):
        doc={"target":"mesh","nodes":[{"id":"mesh","origin":"original"}]}
        self.assertEqual(evaluate_manifest(doc)["status"],"PROVENANCE_BLOCKED")

    def test_cycle_rejected(self):
        doc={"target":"a","nodes":[
            {"id":"a","origin":"derived","parents":["b"]},
            {"id":"b","origin":"derived","parents":["a"]}
        ]}
        with self.assertRaises(ProvenanceError):evaluate_manifest(doc)


if __name__=="__main__":unittest.main()
