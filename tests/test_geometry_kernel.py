"""Casos sintéticos sin GLB de terceros ni llamadas a IA."""
import unittest
import numpy as np
from copox.geometry.kernel import GeometryError, fit_axis_ellipsoid, resample_closed, boundary_loops, bridge_equal_loops


class GeometryKernelTests(unittest.TestCase):
    def test_ellipsoid_fit_recovers_known_parameters(self):
        rng=np.random.default_rng(23)
        u=rng.normal(size=(900,3));u/=np.linalg.norm(u,axis=1)[:,None]
        c=np.array([0.3,0.7,-0.1])
        radius=np.array([0.22,0.26,0.20])
        pts=c+u*radius
        fit=fit_axis_ellipsoid(pts)
        np.testing.assert_allclose(fit.center,c,atol=1e-4)
        np.testing.assert_allclose(fit.radii,radius,atol=1e-4)
        self.assertLess(fit.rms_residual,1e-4)

    def test_resample_closed_square_without_duplicate(self):
        p=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],float)
        r=resample_closed(p,8)
        self.assertEqual(r.shape,(8,3))
        np.testing.assert_allclose(r[0],[0,0,0])
        np.testing.assert_allclose(r[2],[1,0,0])
        np.testing.assert_allclose(r[4],[1,1,0])
        self.assertTrue(np.all(np.linalg.norm(np.roll(r,-1,axis=0)-r,axis=1)>0))

    def test_detect_two_loops_and_bridge_into_closed_manifold(self):
        vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,0,1],[0,1,1]],float)
        faces=np.array([[0,1,2],[3,5,4]],int)
        loops=boundary_loops(faces)
        self.assertEqual(len(loops),2)
        joined,report=bridge_equal_loops(vertices,faces,loops[0],loops[1],max_gap=2)
        self.assertEqual(report["bridge_triangles"],6)
        self.assertEqual(report["remaining_open_loops"],0)
        self.assertTrue(report["same_mesh_shared_indices"])
        self.assertFalse(report["self_intersection_checked"])
        self.assertEqual(joined.shape,(8,3))

    def test_refuses_wrong_or_unequal_loops(self):
        verts=np.zeros((6,3))
        tris=np.array([[0,1,2],[3,4,5]])
        with self.assertRaises(GeometryError):
            bridge_equal_loops(verts,tris,[0,1,2],[3,4],max_gap=1)

    def test_seams_remain_separate_by_index(self):
        f=np.array([[0,1,2],[3,4,5]])
        loops=boundary_loops(f)
        self.assertEqual(len(loops),2)

    def test_nonmanifold_and_wrong_winding_rejected(self):
        for faces in (
            np.array([[0,1,2],[0,1,3]]),
            np.array([[0,1,2],[1,0,3],[0,1,4]])
        ):
            with self.assertRaises(GeometryError):boundary_loops(faces)

    def test_incomplete_or_degenerate_data_rejected(self):
        with self.assertRaises(GeometryError):fit_axis_ellipsoid(np.zeros((17,3)))
        with self.assertRaises(GeometryError):
            resample_closed([[0,0,0],[0,0,0],[1,0,0]],8)


if __name__=="__main__":unittest.main()
