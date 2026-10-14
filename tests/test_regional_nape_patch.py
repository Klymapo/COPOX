"""Tests for a nape patch that must not be vetoed by unfinished face work."""
import unittest
import numpy as np
from copox.geometry.regional_nape_patch import patch_nape_arc
from copox.geometry.kernel import boundary_loops,GeometryError


def cap(n=64):
    a=np.arange(n)*2*np.pi/n
    ring=np.stack((.20*np.cos(a),np.full(n,.765),.20*np.sin(a)),axis=1)
    pts=np.vstack((ring,[[0,.89,0]]))
    tri=np.asarray([[n,i,(i+1)%n] for i in range(n)],int)
    return pts,tri


class RegionalNapePatchTests(unittest.TestCase):
    def test_rear_only_preserves_all_old_vertices_and_faces(self):
        v,f=cap()
        saved_v=v.copy();saved_f=f.copy()
        r=patch_nape_arc(v,f,rear_z_max=-.06,drop_m=.025,depth_m=.003,rings=3)
        self.assertGreater(r.selected_boundary_edges,5)
        self.assertEqual(r.added_triangles,r.selected_boundary_edges*2*3)
        self.assertEqual(r.added_vertices,(r.selected_boundary_edges+1)*3)
        self.assertEqual(len(boundary_loops(r.faces)),1)
        np.testing.assert_array_equal(r.positions[:len(v)],v)
        np.testing.assert_array_equal(r.faces[:len(f)],f)
        np.testing.assert_array_equal(v,saved_v)
        np.testing.assert_array_equal(f,saved_f)
        self.assertLess(np.max(r.positions[len(v):,2]),0)
        self.assertEqual(r.status,"LOCAL_NAPE_ONLY_UNAPPROVED")

    def test_displacement_budget_rejects_excess(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            patch_nape_arc(v,f,drop_m=.10,max_displacement_m=.05)

    def test_nonexistent_rear_arc_rejected(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            patch_nape_arc(v,f,rear_z_max=-2)

    def test_missing_or_incompatible_border_rejected(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            patch_nape_arc(v,np.concatenate([f,np.array([[0,1,2]])]))

    def test_same_inputs_same_indices_and_vertex_locations(self):
        v,f=cap()
        a=patch_nape_arc(v,f)
        b=patch_nape_arc(v,f)
        np.testing.assert_array_equal(a.positions,b.positions)
        np.testing.assert_array_equal(a.faces,b.faces)


if __name__=="__main__":
    unittest.main()
