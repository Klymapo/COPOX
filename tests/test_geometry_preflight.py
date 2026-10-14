"""Pruebas gratuitas del gate barato; no requiere GLB ni GPU."""
import unittest
from copox.geometry.preflight_gate import evaluate


CFG = {
    "coordinates": {"up":"Y","front":"+Z","units":"m"},
    "requires_connected_seam": True,
    "requires_boundary_reduction": True,
    "min_target_visible_change_pct": 0.5,
    "min_target_improvement_pp": 0.10,
    "max_frozen_region_loss_pp": 0.20,
}

def sample():
    return {
        "coordinates":{"up":"Y","front":"+Z","units":"m"},
        "rig":{"original_animation_skin_bytes_equal":True,"frozen_primitives_equal":True},
        "protected":{"missing_face_triangles":0,"missing_ear_triangles":0},
        "topology":{"new_nonmanifold_edges":0,"seam_connected":True,
            "target_boundary_edges_before":128,"target_boundary_edges_after":0},
        "visual":{"target_visible_change_pct":1.2,
            "target_improvement_pp":0.25,"worst_frozen_region_loss_pp":0.0},
    }

class GeometryPreflightTest(unittest.TestCase):
    def test_valid_candidate_only_reaches_deep(self):
        x=evaluate(sample(), CFG)
        self.assertEqual(x["status"],"DEEP_ELIGIBLE")
        self.assertTrue(x["must_render_deep"])
        self.assertFalse(x["can_promote"])

    def test_previous_v04_plateau_rejects_before_deep(self):
        x=sample()
        x["topology"]["seam_connected"]=False
        x["topology"]["target_boundary_edges_after"]=128
        x["visual"]["target_visible_change_pct"]=0.1
        x["visual"]["target_improvement_pp"]=0.0
        z=evaluate(x,CFG)
        self.assertEqual(z["status"],"REJECTED_EARLY")
        self.assertTrue({"SeamConnected","TargetBoundaryImproved","VisibleDifference","TargetImprovement"}.issubset(z["failures"]))

    def test_lost_facial_triangles_always_rejected(self):
        x=sample()
        x["protected"]["missing_face_triangles"]=99
        self.assertEqual(evaluate(x,CFG)["status"],"REJECTED_EARLY")

    def test_rig_regression_always_rejected(self):
        x=sample()
        x["rig"]["original_animation_skin_bytes_equal"]=False
        self.assertEqual(evaluate(x,CFG)["status"],"REJECTED_EARLY")

    def test_wrong_coordinates_rejected(self):
        x=sample()
        x["coordinates"]["up"]="Z"
        self.assertEqual(evaluate(x,CFG)["status"],"REJECTED_EARLY")

    def test_missing_metrics_does_not_implicitly_pass(self):
        x=sample()
        del x["topology"]["seam_connected"]
        with self.assertRaises(ValueError):
            evaluate(x,CFG)

if __name__ == "__main__":
    unittest.main()
