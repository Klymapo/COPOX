"""Pruebas sintéticas de las tres skills, sin activos Hunyuan ni rig del juego."""
import unittest
import numpy as np
from copox.geometry.kernel import GeometryError,boundary_loops
from copox.geometry.surface_sculpt import flatten_surface
from copox.geometry.anatomic_cut import cut_plane
from copox.geometry.surface_stitch import MeshPart,stitch_parts


class ScullyTests(unittest.TestCase):
    def test_flatten_and_protect(self):
        p=np.array([[0,0,.9],[.12,0,.8],[.4,0,.9],[0,.1,.95]],float)
        original=p.copy()
        n=np.array([0.,0.,1.])
        protected=np.array([False,True,False,False])
        result=flatten_surface(p,direction=n,target_projection=.7,
            region_center=np.zeros(3),region_radii=np.array([.25,.25,1]),
            protected=protected,max_displacement=.3)
        self.assertLess(result.positions[0,2],p[0,2])
        np.testing.assert_array_equal(result.positions[[1,2]],p[[1,2]])
        np.testing.assert_array_equal(p,original)
        np.testing.assert_array_equal(n,[0,0,1])
        self.assertEqual(result.changed_vertices,2)

    def test_displacement_budget_blocks(self):
        p=np.array([[0,0,.9],[0,.1,.8],[0,-.1,.85]])
        with self.assertRaises(GeometryError):
            flatten_surface(p,direction=[0,0,1],target_projection=.1,
                region_center=[0,0,0],region_radii=[1,1,1],
                max_displacement=.15)


class AnatomicCutTests(unittest.TestCase):
    def fixture(self):
        p=np.array([[-1,0,-1],[1,0,-1],[1,0,1],[-1,0,1]],float)
        return dict(POSITION=p,NORMAL=np.tile([0,1,0],(4,1)).astype(float),
          TEXCOORD_0=np.array([[0,0],[1,0],[1,1],[0,1]],float),
          JOINTS_0=np.array([[0,1,0,0],[0,1,0,0],[1,0,0,0],[1,0,0,0]],np.uint16),
          WEIGHTS_0=np.array([[.7,.3,0,0],[.6,.4,0,0],[.7,.3,0,0],[.6,.4,0,0]],float))

    def test_cut_with_uv_and_skin_preserved(self):
        attrs=self.fixture();f=np.array([[0,1,2],[0,2,3]],int)
        n=np.array([0.,0.,1.])
        result=cut_plane(attrs,f,n,0.0)
        self.assertEqual(result.clipped_faces,2)
        self.assertGreaterEqual(result.added_vertices,2)
        self.assertTrue(np.all(result.attributes["POSITION"][result.faces][:,:,2]<=1e-10))
        np.testing.assert_allclose(result.attributes["WEIGHTS_0"].sum(axis=1),1.0,atol=1e-10)
        np.testing.assert_array_equal(attrs["POSITION"],self.fixture()["POSITION"])
        np.testing.assert_array_equal(n,[0,0,1])
        self.assertTrue(np.isfinite(result.attributes["TEXCOORD_0"]).all())

    def test_protected_faces_are_not_cut(self):
        attrs=self.fixture();f=np.array([[0,1,2],[0,2,3]],int)
        res=cut_plane(attrs,f,[0,0,1],0,protected_faces=np.array([True,False]))
        self.assertEqual(res.protected_faces_preserved,1)
        self.assertIn([0,1,2],res.faces.tolist())

    def test_missing_skin_channel_and_morph_fail_closed(self):
        attrs=self.fixture();attrs.pop("WEIGHTS_0")
        with self.assertRaises(GeometryError):
            cut_plane(attrs,np.array([[0,1,2]]),[0,0,1],0)
        with self.assertRaises(GeometryError):
            cut_plane(self.fixture(),np.array([[0,1,2]]),[0,0,1],0,morph_targets_present=True)


class StitchTests(unittest.TestCase):
    def parts(self):
        positions_a=np.array([[0,0,0],[1,0,0],[0,1,0]],float)
        positions_b=np.array([[0,0,1],[1,0,1],[0,1,1]],float)
        attributes_a={"NORMAL":np.tile([0,0,-1],(3,1)).astype(float),
          "TEXCOORD_0":np.array([[0,0],[1,0],[0,1]],float),
          "JOINTS_0":np.tile([0,1,0,0],(3,1)).astype(np.uint16),
          "WEIGHTS_0":np.tile([1.,0,0,0],(3,1))}
        attributes_b={k:v.copy() for k,v in attributes_a.items()}
        a=MeshPart(positions_a,np.array([[0,1,2]]),attributes_a,material_id=3)
        b=MeshPart(positions_b,np.array([[0,2,1]]),attributes_b,material_id=5)
        return a,b

    def test_bridge_two_primitives_and_materials(self):
        a,b=self.parts()
        fa=boundary_loops(a.faces)[0]
        fb=boundary_loops(b.faces)[0]
        result=stitch_parts(a,b,fa,fb,max_gap=2,bridge_material=8)
        self.assertEqual(len(result.faces),8)
        self.assertEqual(len(boundary_loops(result.faces)),0)
        self.assertEqual(result.face_materials.tolist(),[3,5]+[8]*6)
        np.testing.assert_array_equal(result.positions[:3],a.positions)
        self.assertFalse(result.report["exported_glb_verified"])
        self.assertTrue(result.report["same_mesh_shared_indices"])

    def test_reject_incompatible_attribute_sets(self):
        a,b=self.parts();b=MeshPart(b.positions,b.faces,{},material_id=5)
        with self.assertRaises(GeometryError):
            stitch_parts(a,b,[0,1,2],[0,2,1],max_gap=2)


if __name__=="__main__":
    unittest.main()
