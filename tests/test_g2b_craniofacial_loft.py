import unittest
import numpy as np
from copox.geometry.kernel import boundary_loops, GeometryError
from copox.geometry.craniofacial_loft import extend_boundary_skin,vertex_normals


class CraniofacialLoftTests(unittest.TestCase):
    def fixture(self):
        n=32
        phi=np.arange(n)*2*np.pi/n
        circle=np.c_[.23*np.cos(phi),np.full(n,.79),.22*np.sin(phi)]
        v=np.vstack([circle,[[0,.92,0]]])
        f=np.array([[n,i,(i+1)%n] for i in range(n)])
        return v,f

    def test_close_preserves_original_triangles_and_is_watertight(self):
        p,f=self.fixture();pc=p.copy();fc=f.copy()
        r=extend_boundary_skin(p,f,rings=8,close_bottom=True)
        self.assertEqual(len(r.positions),len(p)+8*32+1)
        self.assertEqual(len(r.faces),len(f)+8*32*2+32)
        self.assertEqual(r.boundary_loops_after,0)
        self.assertEqual(r.degenerate_faces,0)
        np.testing.assert_array_equal(r.positions[:len(p)],p)
        np.testing.assert_array_equal(r.faces[:len(f)],f)
        np.testing.assert_array_equal(p,pc)
        np.testing.assert_array_equal(f,fc)
        self.assertEqual(len(r.correspondence),8*32+1)
        normals=vertex_normals(r.positions,r.faces)
        self.assertTrue(np.all(np.isfinite(normals)))
        self.assertTrue(np.allclose(np.linalg.norm(normals,axis=1),1))

    def test_open_loft_preserves_single_boundary(self):
        p,f=self.fixture()
        r=extend_boundary_skin(p,f,rings=4,close_bottom=False)
        self.assertEqual(len(boundary_loops(r.faces)),1)
        self.assertEqual(len(boundary_loops(r.faces)[0]),32)
        self.assertFalse(r.cap_closed)

    def test_no_loft_when_boundary_not_unique(self):
        p,f=self.fixture()
        f=np.vstack([f,np.array([[0,1,2]])])
        with self.assertRaises(GeometryError):
            extend_boundary_skin(p,f)

    def test_nonphysical_target_rejected(self):
        p,f=self.fixture()
        with self.assertRaises(GeometryError):
            extend_boundary_skin(p,f,front_end_y=.799)
        with self.assertRaises(GeometryError):
            extend_boundary_skin(p,f,front_end_radius=-1)
        with self.assertRaises(GeometryError):
            extend_boundary_skin(p,f,rings=1)


if __name__=="__main__":unittest.main()
