"""Cobertura de TODAS las referencias, sin tolerar vistas que desaparecen."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from copox.visual.critic import audit,mask_metrics


class AllReferencesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.views=["front","three_quarter","side","back"]
        self.images=[]
        for i in range(9):
            name=f"image_{i}.png"
            arr=np.full((20,20,3),255,dtype=np.uint8)
            arr[4+i%3:16,3:16]=[90,105+i,123]
            Image.fromarray(arr).save(self.root/name)
            self.images.append(name)
        for i in range(4):
            m=np.zeros((20,20),np.uint8);m[4:16,4:16]=255
            if i==1:m[4:8,4:8]=0
            Image.fromarray(m).save(self.root/f"mask_{i}.png")
        self.references=[
            {"id":"frontal-main","view":"front","image":self.images[0],"mask":"mask_0.png","camera_alignment":"exact"},
            {"id":"frontal-secondary","view":"front","image":self.images[1],"camera_alignment":"approximate"},
            {"id":"three-quarter","view":"three_quarter","image":self.images[2],"camera_alignment":"unknown"},
            {"id":"side","view":"side","image":self.images[3],"camera_alignment":"exact"},
            {"id":"back","view":"back","image":self.images[4],"camera_alignment":"exact"}
        ]
        self.candidate={"id":"test", "views":[
           {"view":v,"pose":"rest","image":self.images[5+i],
            **({"mask":"mask_1.png"} if i==0 else {})}
           for i,v in enumerate(self.views)]}
        self.manifest={"asset_id":"synthetic","required_views":list(self.views),
                       "provided_reference_files":[x["image"] for x in self.references],
                       "references":self.references,"candidate":self.candidate}

    def run_audit(self, with_sheets=False):
        return audit(self.manifest,root=self.root,
                     output=self.root/"result",make_sheets=with_sheets)

    def test_each_reference_individually_compared_including_second_front(self):
        report=self.run_audit(with_sheets=True)
        self.assertEqual(report["status"],"REVIEW_REQUIRED")
        self.assertEqual(report["references_supplied"],5)
        self.assertEqual(report["references_compared"],5)
        self.assertTrue(report["all_references_accounted_for"])
        self.assertEqual({x["reference_id"] for x in report["comparisons"]},
                         {x["id"] for x in self.references})
        self.assertEqual(len(list((self.root/"result").glob("comparison_*.png"))),5)
        self.assertLess(report["worst_mask_iou"],1)
        self.assertIsNone(report["comparisons"][1]["metrics"])
        self.assertFalse(report["automatically_approved"])

    def test_inventory_detects_omitted_reference_even_if_other_views_pass(self):
        self.manifest["provided_reference_files"].append("image_8.png")
        report=self.run_audit()
        self.assertEqual(report["status"],"INCOMPLETE")
        self.assertIn("image_8.png"," ".join(report["issues"]))

    def test_missing_required_view_blocks(self):
        self.candidate["views"]=[x for x in self.candidate["views"] if x["view"]!="side"]
        report=self.run_audit()
        self.assertEqual(report["status"],"INCOMPLETE")
        self.assertIn("side", " ".join(report["issues"]))
        self.assertEqual(report["references_compared"],4)

    def test_missing_file_in_unreferenced_view_blocks(self):
        self.candidate["views"].append({"view":"top","image":"not_found.png"})
        report=self.run_audit()
        self.assertEqual(report["status"],"INCOMPLETE")

    def test_extra_view_not_auto_approved(self):
        self.candidate["views"].append({"view":"top","image":self.images[5]})
        for r in self.references:
            r["manual_review"]={"verdict":"PASS","observations":["Revisado por humano en prueba sintética"],"reviewer":"test-suite"}
        report=self.run_audit()
        self.assertEqual(report["status"],"REVIEW_REQUIRED")
        self.assertEqual(report["unreferenced_candidate_views"],[{"view":"top","pose":"rest"}])

    def test_all_manual_reviews_ready_only_for_admin(self):
        for r in self.references:
            r["manual_review"]={"verdict":"PASS","observations":["Comparación controlada"],"reviewer":"test-suite"}
        report=self.run_audit()
        self.assertEqual(report["status"],"READY_FOR_ADMIN")
        self.assertFalse(report["automatically_approved"])

    def test_one_reference_issue_overrides_other_passing_references(self):
        for r in self.references:
            r["manual_review"]={"verdict":"PASS","observations":["Sin anomalías"],"reviewer":"test-suite"}
        self.references[3]["manual_review"]={"verdict":"ISSUE","observations":["Bulto en perfil"],"reviewer":"test-suite"}
        self.manifest["anomalies"]=[{"id":"bulge-1","region":"forehead",
            "description":"Bulto observado en el perfil","per_reference":{
                r["id"]:{"assessment":"supports" if r["id"]=="side" else "not_visible",
                          "note":"Se observa en perfil" if r["id"]=="side" else "No concluyente en esta vista"}
                for r in self.references}}]
        report=self.run_audit()
        self.assertEqual(report["status"],"ISSUES_FOUND")
        self.assertEqual(report["problematic_references"],["side"])
        self.assertEqual(len(report["anomaly_cross_view_matrix"]),1)
        self.assertEqual(report["anomaly_cross_view_matrix"][0]["cross_reference_evidence"]["supports"],["side"])

    def test_defect_rejected_when_other_reference_is_not_considered(self):
        for r in self.references:
            r["manual_review"]={"verdict":"PASS","observations":["Evaluada"],"reviewer":"test-suite"}
        self.references[3]["manual_review"]["verdict"]="ISSUE"
        self.manifest["anomalies"]=[{"id":"bulge-1","region":"forehead",
            "description":"Bulto en perfil","per_reference":{
                "side":{"assessment":"supports","note":"Saliente"}
            }}]
        report=self.run_audit()
        self.assertEqual(report["status"],"INCOMPLETE")
        self.assertTrue(any("matriz incompleta" in x for x in report["issues"]))

    def test_camera_approximate_never_used_for_mask_iou(self):
        self.references[1]["mask"]="mask_0.png"
        self.candidate["views"][0]["mask"]="mask_1.png"
        report=self.run_audit()
        self.assertIsNone(report["comparisons"][1]["metrics"])
        self.assertIn("Cámara aproximada",report["comparisons"][1]["metric_note"])

    def test_mask_mismatch_must_not_autoscale(self):
        Image.fromarray(np.full((10,10),255,np.uint8)).save(self.root/"tiny.png")
        with self.assertRaises(ValueError):
            mask_metrics(self.root/"mask_0.png",self.root/"tiny.png")

    def test_reject_reference_outside_root(self):
        self.references[0]["image"]="../outside.png"
        self.manifest["provided_reference_files"][0]="../outside.png"
        self.assertEqual(self.run_audit()["status"],"INCOMPLETE")

    def test_multiple_pose_references_require_matching_frame(self):
        self.references.append({"id":"walk-left","view":"side","pose":"walk_contact",
                                "image":self.images[8],"camera_alignment":"approximate"})
        self.manifest["provided_reference_files"].append(self.images[8])
        self.assertEqual(self.run_audit()["status"],"INCOMPLETE")
        self.candidate["views"].append({"view":"side","pose":"walk_contact","image":self.images[7]})
        r=self.run_audit()
        self.assertEqual(r["references_compared"],6)
        self.assertEqual(r["status"],"REVIEW_REQUIRED")


if __name__=="__main__":unittest.main()
