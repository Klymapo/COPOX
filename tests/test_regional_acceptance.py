"""COPOX · QA por regiones: defectos de otras piezas no vetan avances locales."""
import unittest
from copox.geometry.regional_acceptance import RegionVerdict,evaluate_regions,REGIONS


class RegionalAcceptanceTests(unittest.TestCase):
    def test_nuca_passes_despite_face_rejected(self):
        result=evaluate_regions({
            "nuca":RegionVerdict("nuca",True,True,True,True,"evidencia local completa"),
            "rostro":RegionVerdict("rostro",False,True,True,True,"facciones pendientes"),
        })
        self.assertEqual(result["regions"]["nuca"]["status"],"PASS_LOCAL_TECHNICAL")
        self.assertEqual(result["regions"]["rostro"]["status"],"REJECTED_LOCAL")
        self.assertEqual(result["technical_pass"],["nuca"])
        self.assertFalse(result["global_approval"])
        self.assertFalse(result["promotion_allowed"])

    def test_local_damage_blocks_only_the_affected_region(self):
        result=evaluate_regions({
            "nuca":RegionVerdict("nuca",True,False,True,True,"cuello afectado"),
            "mano_izquierda":RegionVerdict("mano_izquierda",True,True,True,True),
        })
        self.assertEqual(result["regions"]["nuca"]["status"],"BLOCKED_INTEGRATION")
        self.assertEqual(result["regions"]["mano_izquierda"]["status"],"PASS_LOCAL_TECHNICAL")

    def test_missing_images_means_not_yet_approved(self):
        r=evaluate_regions({"nuca":RegionVerdict("nuca",True,True,True,False)})
        self.assertEqual(r["regions"]["nuca"]["status"],"NEEDS_EVIDENCE")

    def test_reject_unknown_or_mislabeled_regions(self):
        with self.assertRaises(ValueError):
            evaluate_regions({"cola":RegionVerdict("cola",True,True,True,True)})
        with self.assertRaises(ValueError):
            evaluate_regions({"nuca":RegionVerdict("rostro",True,True,True,True)})

    def test_all_regions_accounted_for_even_when_unassessed(self):
        r=evaluate_regions({})
        self.assertEqual(len(r["pending"]),len(REGIONS))
        self.assertFalse(r["global_approval"])
        self.assertEqual(r["locally_accepted"],[])


    def test_artistic_approval_local_does_not_promote(self):
        r=evaluate_regions({
           "nuca":RegionVerdict("nuca",True,True,True,True,
                                artistic_review_completed=True,
                                artistic_review_approved=True,
                                integration_tests_pass=True),
           "rostro":RegionVerdict("rostro",False,True,True,True)
        })
        self.assertEqual(r["locally_accepted"],["nuca"])
        self.assertEqual(r["integration_review_ready"],["nuca"])
        self.assertFalse(r["promotion_allowed"])

    def test_visual_rejection_only_of_one_region(self):
        r=evaluate_regions({
            "nuca":RegionVerdict("nuca",True,True,True,True,
                                 artistic_review_completed=True,
                                 artistic_review_approved=False),
            "mano_derecha":RegionVerdict("mano_derecha",True,True,True,True)
        })
        self.assertEqual(r["regions"]["nuca"]["status"],"REJECTED_VISUAL_LOCAL")
        self.assertIn("mano_derecha",r["technical_pass"])

    def test_requires_completed_artistic_review_before_approval(self):
        with self.assertRaises(ValueError):
            evaluate_regions({"nuca":RegionVerdict("nuca",True,True,True,True,
                                artistic_review_approved=True)})


if __name__=="__main__":
    unittest.main()
