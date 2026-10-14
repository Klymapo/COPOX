"""G2-C: la costura desigual CIERRA sólo anillos reales.

La verificación artística, autointersecciones y GLB skin-aware son gates
separados: PASSED topology != MODEL APPROVED.
"""
import unittest
import numpy as np
from copox.geometry.kernel import GeometryError,boundary_loops
from copox.geometry.advancing_stitch import stitch_unequal_loops


def two_disks(n=12,m=19,dist=.25,radius=1.):
    a=np.arange(n)*2*np.pi/n
    b=np.arange(m)*2*np.pi/m
    lower=np.column_stack((radius*np.cos(a),radius*np.sin(a),np.zeros(n)))
    upper=np.column_stack((radius*np.cos(b),radius*np.sin(b),np.full(m,dist)))
    vertices=np.vstack((lower,upper,[[0,0,0],[0,0,dist]]))
    bottom_center=n+m;top_center=n+m+1
    # upper winding opposite lower
    faces=np.array([[bottom_center,i,(i+1)%n] for i in range(n)]
      + [[top_center,n+(i+1)%m,n+i] for i in range(m)],dtype=int)
    return vertices,faces


class AdvancingFrontTests(unittest.TestCase):
    def test_closes_unequal_and_preserves_positions(self):
        v,f=two_disks(12,19)
        copy=v.copy(); old_faces=f.copy()
        a,b=boundary_loops(f)
        r=stitch_unequal_loops(v,f,a,b,max_gap=.65,max_aspect_ratio=30)
        self.assertEqual(len(r.new_faces),31)
        self.assertEqual(r.report["steps_a"],12)
        self.assertEqual(r.report["steps_b"],19)
        self.assertEqual(r.report["loops_after"],0)
        self.assertEqual(len(boundary_loops(r.faces)),0)
        np.testing.assert_array_equal(r.faces[:len(f)],old_faces)
        np.testing.assert_array_equal(v,copy)
        self.assertTrue(r.report["same_index_space"])
        self.assertFalse(r.report["self_intersections_checked"])
        self.assertFalse(r.report["production_ready"])

    def test_equal_lengths_are_supported(self):
        v,f=two_disks(16,16)
        a,b=boundary_loops(f)
        r=stitch_unequal_loops(v,f,a,b,max_gap=.65)
        self.assertEqual(len(r.new_faces),32)
        self.assertEqual(r.report["loops_after"],0)

    def test_large_loops_without_quadratic_distance_matrix(self):
        v,f=two_disks(128,257,dist=.15,radius=.5)
        a,b=boundary_loops(f)
        result=stitch_unequal_loops(v,f,a,b,max_gap=.3,max_aspect_ratio=50)
        self.assertEqual(result.report["triangles"],385)
        self.assertEqual(result.report["loops_after"],0)

    def test_disjoint_graph_has_too_many_loops_and_blocks(self):
        v,f=two_disks()
        nv=np.array([[3,0,0],[4,0,0],[3,1,0]],float)
        v=np.vstack((v,nv));f=np.vstack((f,[[len(v)-3,len(v)-2,len(v)-1]]))
        a,b=boundary_loops(f)[:2]
        with self.assertRaisesRegex(GeometryError,"exactly 2"):
            stitch_unequal_loops(v,f,a,b,max_gap=2)

    def test_wrong_loop_nonboundary_rejected(self):
        v,f=two_disks()
        a,b=boundary_loops(f)
        a=a.copy();a[1]=len(v)-1
        with self.assertRaises(GeometryError):
            stitch_unequal_loops(v,f,a,b,max_gap=2)

    def test_winding_reversal_not_allowed_as_input(self):
        v,f=two_disks()
        a,b=boundary_loops(f)
        with self.assertRaises(GeometryError):
            stitch_unequal_loops(v,f,a[::-1],b,max_gap=2)

    def test_distance_gate_blocks_too_far(self):
        v,f=two_disks(12,19,dist=1)
        a,b=boundary_loops(f)
        with self.assertRaises(GeometryError):
            stitch_unequal_loops(v,f,a,b,max_gap=.2)

    def test_nonmanifold_rejected(self):
        v,f=two_disks()
        f=np.vstack([f,[[0,1,2]]])
        with self.assertRaises(GeometryError):
            stitch_unequal_loops(v,f,[0,1,2],[3,4,5],max_gap=3)

    def test_too_long_skinny_triangles_rejected(self):
        v,f=two_disks(8,8,dist=.3)
        a,b=boundary_loops(f)
        with self.assertRaisesRegex(GeometryError,"alargados"):
            stitch_unequal_loops(v,f,a,b,max_gap=2,max_aspect_ratio=1.01)

    def test_determinism_without_randomness(self):
        v,f=two_disks(20,34)
        a,b=boundary_loops(f)
        x=stitch_unequal_loops(v,f,a,b,max_gap=1)
        y=stitch_unequal_loops(v,f,a,b,max_gap=1)
        np.testing.assert_array_equal(x.faces,y.faces)
        self.assertEqual(x.report["max_cross_gap_m"],y.report["max_cross_gap_m"])


if __name__=="__main__":
    unittest.main()
