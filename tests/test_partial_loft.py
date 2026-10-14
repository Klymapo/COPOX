import unittest
import numpy as np
from copox.geometry.partial_loft import extend_rear_arc
from copox.geometry.kernel import boundary_loops,GeometryError


def cap(n=64):
    t=np.arange(n)*2*np.pi/n
    rim=np.c_[.21*np.cos(t),np.full(n,.78),.20*np.sin(t)]
    v=np.vstack((rim,[[0,.94,0]]))
    f=np.array([[n,i,(i+1)%n] for i in range(n)],int)
    return v,f


class RearArcTests(unittest.TestCase):
    def test_only_rear_arcs_extended_and_origins_unchanged(self):
        v,f=cap()
        v0=v.copy();f0=f.copy()
        r=extend_rear_arc(v,f,drop_m=.024)
        self.assertGreater(r.selected_boundary_edges,4)
        self.assertLess(r.selected_boundary_edges,32)
        self.assertEqual(r.report["remaining_open_loops"],1)
        self.assertFalse(r.report["front_sector_selected"])
        self.assertFalse(r.report["full_mesh_watertight"])
        np.testing.assert_array_equal(r.positions[:len(v)],v0)
        np.testing.assert_array_equal(r.faces[:len(f)],f0)
        np.testing.assert_array_equal(v,v0)
        np.testing.assert_array_equal(f,f0)
        self.assertTrue(np.all(v[r.source_vertex_ids,2]<0))

    def test_invalid_geometry_is_rejected(self):
        v,f=cap()
        with self.assertRaises(GeometryError):
            extend_rear_arc(v,f,sector_threshold=1)
        with self.assertRaises(GeometryError):
            extend_rear_arc(v,f,drop_m=0)
        with self.assertRaises(GeometryError):
            extend_rear_arc(v,f,rear_direction=(0,0))

    def test_original_contour_remains_continuous(self):
        v,f=cap()
        r=extend_rear_arc(v,f)
        self.assertEqual(len(boundary_loops(r.faces)),1)
        self.assertEqual(len(r.faces)-len(f),2*r.selected_boundary_edges)


if __name__=="__main__":
    unittest.main()
