import unittest
import numpy as np
from copox.geometry.kernel import GeometryError
from copox.geometry.partial_nape import rear_nape_patch
from copox.geometry.regional_review import RegionVerdict,aggregate_regional_review


def cap(n=128):
    t=np.arange(n)*2*np.pi/n
    rim=np.column_stack([.2*np.cos(t),np.full(n,.672),-.01+.19*np.sin(t)])
    return np.vstack([rim,[[0,.90,-.01]]]),np.array([[n,k,(k+1)%n] for k in range(n)])


class LocalPatchTests(unittest.TestCase):
    def test_nape_changes_only_rear_and_preserves_mesh_prefix(self):
        v,f=cap()
        orig=v.copy();before=f.copy()
        r=rear_nape_patch(v,f)
        self.assertGreater(r.report["source_arc_edges"],8)
        self.assertLess(r.report["source_arc_edges"],75)
        self.assertEqual(r.report["added_triangles"],2*r.report["source_arc_edges"])
        self.assertTrue(np.all(r.positions[len(v):,2]<-.075))
        np.testing.assert_array_equal(r.positions[:len(v)],orig)
        np.testing.assert_array_equal(r.faces[:len(f)],before)
        self.assertGreater(r.report["remaining_open_edges"],0)
        self.assertFalse(r.report["global_watertight"])
        np.testing.assert_array_equal(v,orig);np.testing.assert_array_equal(f,before)

    def test_strictly_reject_front_cut_and_invalid_parameters(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            rear_nape_patch(v,f,rear_z_max=-.3)
        with self.assertRaises(GeometryError):
            rear_nape_patch(v,f,drop_m=-.1)

    def test_eased_profile_preserves_original_and_softens_band_ends(self):
        v,f=cap()
        flat=rear_nape_patch(v,f)
        eased=rear_nape_patch(v,f,profile="eased")
        n=len(eased.source_edges)+1
        self.assertEqual(eased.report["profile"],"eased")
        self.assertEqual(eased.report["patch_rows"],2)
        self.assertEqual(eased.report["added_triangles"],flat.report["added_triangles"]*2)
        self.assertEqual(len(eased.positions),len(v)+2*n)
        np.testing.assert_array_equal(eased.positions[:len(v)],v)
        np.testing.assert_array_equal(eased.faces[:len(f)],f)
        self.assertEqual(eased.report["remaining_open_edges"],flat.report["remaining_open_edges"])
        original_y=v[eased.ancestry[-n:],1]
        drops=original_y-eased.positions[-n:,1]
        self.assertGreater(float(drops[n//2]),float(drops[0]))
        self.assertGreater(float(drops[n//2]),float(drops[-1]))
        self.assertTrue(np.all(drops>0))
        self.assertTrue(np.all(eased.positions[len(v):,2]<-.075))
        self.assertFalse(eased.report["global_watertight"])

    def test_profile_invalid_is_fail_closed(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            rear_nape_patch(v,f,profile="unchecked")

    def test_region_failure_does_not_reject_independent_nape(self):
        regions={
          "nuca":RegionVerdict("nuca","PASS","IMPROVED",True,True),
          "cara":RegionVerdict("cara","FAIL","REGRESSION",True,True),
          "manos":RegionVerdict("manos","UNTESTED","REVIEW_REQUIRED",True,True)
        }
        result=aggregate_regional_review(regions,target_region="nuca")
        self.assertEqual(result["local_result"],"REGION_IMPROVED_PENDING_HUMAN_APPROVAL")
        self.assertFalse(result["global_model_approved"])
        self.assertFalse(result["auto_merge"])
        self.assertEqual(result["regions"]["cara"]["technical"],"FAIL")

    def test_scope_violation_overrides_local_improvement(self):
        regions={"nuca":RegionVerdict("nuca","PASS","IMPROVED",False,True),
                 "cara":RegionVerdict("cara","FAIL","REGRESSION",True,True)}
        self.assertEqual(aggregate_regional_review(regions,target_region="nuca")["local_result"],
                         "REJECTED_OUT_OF_SCOPE_OR_CORE_INVARIANTS")

    def test_unverified_visual_result_is_not_promotion(self):
        regions={"nuca":RegionVerdict("nuca","PASS","REVIEW_REQUIRED",True,True)}
        result=aggregate_regional_review(regions,target_region="nuca")
        self.assertEqual(result["local_result"],"REGION_READY_FOR_VISUAL_REVIEW")
        self.assertFalse(result["global_model_approved"])

if __name__=="__main__":unittest.main()
