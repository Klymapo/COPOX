"""Integración Visual Critic -> medición -> Scully/Cut/Stitch sin alterar GLB."""
import unittest
import numpy as np
from copox.visual.geometry_planner import propose
from copox.visual.mesh_diagnostics import analyze_plane_region
from copox.geometry.kernel import GeometryError


REFS=["front","three_quarter","side","back","additional_front"]
SHA="a"*64


def visual(coverage=True,conflicts=False):
    return {
        "status":"REVIEW_REQUIRED" if coverage else "INCOMPLETE",
        "all_references_accounted_for":coverage,
        "references_supplied":5,
        "comparisons":[{"reference_id":x,"manual_review":None,"metrics":None} for x in REFS],
        "anomaly_cross_view_matrix":[{"id":"bulto1","region":"forehead","description":"Protrusión",
            "cross_reference_evidence":{
                "supports":["side","three_quarter"],
                "contradicts":["front"] if conflicts else [],
                "not_visible":["back"],
                "uncertain":["additional_front"] if conflicts else ["front","additional_front"]}}],
    }


def geometry(kind="surface_bulge"):
    return {"anomalies":{"bulto1":{
        "kind":kind,
        "measurement_provenance":{"source_sha256":SHA,
           "measurement_method":"synthetic measured sample","coordinate_system":"Y-up m"},
        "signed_excess_mm":12.5,"region_topology_continuous":True,
        "flatten":{"direction":[0,0,1],"target_projection":.21,
                   "region_center":[0,.08,.2],"region_radii":[.2,.25,.3],
                   "strength":.85,"falloff":.35,"max_displacement":.05}
    }}}


class VisualGeometryPlannerTests(unittest.TestCase):
    def test_bulge_selects_scully_not_modify(self):
        result=propose(visual(),geometry())
        self.assertEqual(result["status"],"PLANS_FOR_SANDBOX")
        rec=result["recommendations"][0]
        self.assertEqual(rec["operator"],"Scully")
        self.assertEqual(rec["state"],"PLAN_READY_FOR_SANDBOX")
        self.assertTrue(rec["independent_visual_review_pending"])
        self.assertFalse(rec["auto_apply"])
        self.assertFalse(result["approved"])
        self.assertEqual(set(sum(rec["reference_coverage"].values(),[])),set(REFS))

    def test_missing_reference_blocks_all_operations(self):
        result=propose(visual(coverage=False),geometry())
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["recommendations"],[])

    def test_contradictory_view_prevents_ready(self):
        result=propose(visual(conflicts=True),geometry())
        self.assertEqual(result["status"],"RESEARCH_REQUIRED")
        self.assertIn("conflicting_reference_views",result["recommendations"][0]["blockers"])

    def test_missing_metric_provenance_prevents_ready(self):
        m=geometry()
        m["anomalies"]["bulto1"].pop("measurement_provenance")
        result=propose(visual(),m)
        self.assertEqual(result["status"],"RESEARCH_REQUIRED")
        self.assertIn("missing_measurement_provenance",result["recommendations"][0]["blockers"])

    def test_missing_reference_in_anomaly_matrix_blocks(self):
        v=visual()
        v["anomaly_cross_view_matrix"][0]["cross_reference_evidence"]["uncertain"].remove("additional_front")
        report=propose(v,geometry())
        self.assertEqual(report["status"],"RESEARCH_REQUIRED")
        self.assertIn("not_all_references_checked",report["issues"][0])

    def test_bulge_requires_continuous_measured_surface(self):
        m=geometry()
        m["anomalies"]["bulto1"]["region_topology_continuous"]=False
        report=propose(visual(),m)
        self.assertEqual(report["status"],"RESEARCH_REQUIRED")
        self.assertIn("topology_not_verified_continuous",report["recommendations"][0]["blockers"])

    def test_fragmented_surface_selects_cut_only_with_protection(self):
        m=geometry("surface_fragments")
        m["anomalies"]["bulto1"].update(disconnected_components=3,floating_triangles=4,
             safe_cut_plane_measured=True,protected_faces_mask_ready=True,
             skin_attributes_supported=True,cut_plane={"normal":[0,1,0],"offset":.77})
        r=propose(visual(),m)["recommendations"][0]
        self.assertEqual(r["operator"],"Anatomic Cut")
        self.assertEqual(r["state"],"PLAN_READY_FOR_SANDBOX")
        m["anomalies"]["bulto1"]["protected_faces_mask_ready"]=False
        r=propose(visual(),m)["recommendations"][0]
        self.assertEqual(r["state"],"RESEARCH_REQUIRED")

    def test_open_seam_selects_stitch_with_compatible_loops(self):
        m=geometry("open_seam")
        m["anomalies"]["bulto1"].update(target_boundary_edges=32,loop_vertex_counts=[16,16],
            loop_winding_valid=True,attributes_compatible=True,morph_targets_present=False,max_gap_m=.05)
        r=propose(visual(),m)["recommendations"][0]
        self.assertEqual(r["operator"],"Surface Stitch")
        self.assertTrue(r["arguments"]["requires_glb_reimport_validation"])
        m["anomalies"]["bulto1"]["loop_vertex_counts"]=[16,17]
        r=propose(visual(),m)["recommendations"][0]
        self.assertIn("incompatible_loop_cardinality",r["blockers"])

    def test_unknown_anomaly_kind_cannot_execute(self):
        m=geometry("unknown")
        r=propose(visual(),m)["recommendations"][0]
        self.assertEqual(r["operator"],"RESEARCH_REQUIRED")
        self.assertFalse(r["auto_apply"])
        self.assertEqual(r["state"],"RESEARCH_REQUIRED")

    def test_anomalies_are_ordered_cut_stitch_scully(self):
        v=visual()
        m=geometry()
        def copy_second(id,kind):
            import copy
            an=copy.deepcopy(v["anomaly_cross_view_matrix"][0]);an["id"]=id
            v["anomaly_cross_view_matrix"].append(an)
            mt=copy.deepcopy(m["anomalies"]["bulto1"]);mt["kind"]=kind
            mt.update(target_boundary_edges=24,loop_vertex_counts=[12,12],
             loop_winding_valid=True,attributes_compatible=True,morph_targets_present=False,max_gap_m=.02,
             disconnected_components=4,floating_triangles=2,safe_cut_plane_measured=True,
             protected_faces_mask_ready=True,skin_attributes_supported=True,
             cut_plane={"normal":[1,0,0],"offset":.3})
            m["anomalies"][id]=mt
        copy_second("cut1","surface_fragments")
        copy_second("stitch1","open_seam")
        rec=propose(v,m)["recommendations"]
        self.assertEqual([r["operator"] for r in rec],["Anatomic Cut","Surface Stitch","Scully"])

    def test_measure_from_real_mesh_positions(self):
        p=np.array([[0,0,.23],[.1,0,.24],[0,.1,.23],[.1,.1,.24]],float)
        f=np.array([[0,1,2],[1,3,2]])
        probe=analyze_plane_region(p,f,np.array([1,1,1,1],dtype=bool),[0,0,1],.21)
        self.assertTrue(probe["region_topology_continuous"])
        self.assertAlmostEqual(probe["signed_excess_mm"],30,places=6)
        self.assertEqual(probe["target_boundary_edges"],4)
        self.assertEqual(probe["region_triangles"],2)
        self.assertEqual(len(probe["measurement_provenance"]["source_sha256"]),64)
        self.assertEqual(len(probe["measurement_provenance"]["source_sha256"]),64)

    def test_disconnected_region_is_not_continuous(self):
        p=np.array([[0,0,.3],[.1,0,.3],[0,.1,.3],
                    [2,0,.3],[2.1,0,.3],[2,.1,.3]])
        f=np.array([[0,1,2],[3,4,5]])
        m=analyze_plane_region(p,f,np.ones(6,dtype=bool),[0,0,1],.25)
        self.assertFalse(m["region_topology_continuous"])
        self.assertEqual(m["region_components"],2)

    def test_bad_masks_and_faces_do_not_pass(self):
        p=np.zeros((4,3),float)
        f=np.array([[0,1,2]])
        with self.assertRaises(GeometryError):
            analyze_plane_region(p,f,np.ones(3,dtype=bool),[0,0,1],0)


if __name__=="__main__":
    unittest.main()
