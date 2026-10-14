"""G2-C: MeshPart conserva skin/UV/materiales, sin exportar falso GLB."""
import unittest
import numpy as np
from copox.geometry.surface_stitch import MeshPart,stitch_parts_unequal
from copox.geometry.kernel import GeometryError


def make_pair(a=12,b=17):
    def disk(n,z,offset=0):
        theta=np.arange(n)*np.pi*2/n
        vertices=np.concatenate([np.stack([.2*np.cos(theta),.2*np.sin(theta),np.full(n,z)],axis=1),[[0,0,z]]])
        faces=np.asarray([[n,k,(k+1)%n] if z==0 else [n,(k+1)%n,k] for k in range(n)],dtype=np.int64)
        joints=np.zeros((len(vertices),4),dtype=np.uint16)
        joints[:,0]=3
        weights=np.zeros((len(vertices),4),dtype=np.float32);weights[:,0]=1
        uv=np.stack([(vertices[:,0]+1)/2,(vertices[:,1]+1)/2],axis=1)
        normals=np.tile([0,0,1 if z==0 else -1],(len(vertices),1))
        return MeshPart(vertices,faces,{"JOINTS_0":joints,"WEIGHTS_0":weights,"TEXCOORD_0":uv,"NORMAL":normals},material_id=1 if z==0 else 2)
    return disk(a,0),disk(b,.12)


class AttributePreservationTests(unittest.TestCase):
    def test_unequal_indices_all_attributes_and_face_materials(self):
        from copox.geometry.kernel import boundary_loops
        a,b=make_pair()
        la=boundary_loops(a.faces)[0]
        lb=boundary_loops(b.faces)[0]
        r=stitch_parts_unequal(a,b,la,lb,max_gap=.35,bridge_material=5)
        self.assertEqual(len(r.faces),12+17+12+17)
        self.assertEqual(r.report["loops_after"],0)
        self.assertTrue(r.report["all_original_vertex_attributes_retained"])
        self.assertFalse(r.report["exported_glb_verified"])
        np.testing.assert_array_equal(r.attributes["JOINTS_0"][:len(a.positions)],a.attributes["JOINTS_0"])
        np.testing.assert_array_equal(r.attributes["TEXCOORD_0"][len(a.positions):],b.attributes["TEXCOORD_0"])
        np.testing.assert_array_equal(r.face_materials[:12],np.full(12,1))
        np.testing.assert_array_equal(r.face_materials[12:29],np.full(17,2))
        np.testing.assert_array_equal(r.face_materials[29:],np.full(29,5))
        self.assertFalse(r.report["production_ready"])

    def test_morph_targets_fail_closed(self):
        a,b=make_pair()
        from copox.geometry.kernel import boundary_loops
        with self.assertRaises(GeometryError):
            stitch_parts_unequal(a,b,boundary_loops(a.faces)[0],boundary_loops(b.faces)[0],
                                max_gap=.3,morph_targets_present=True)

    def test_uv_absent_on_one_side_blocks(self):
        a,b=make_pair()
        from copox.geometry.kernel import boundary_loops
        b=MeshPart(b.positions,b.faces,{k:v for k,v in b.attributes.items() if k!="TEXCOORD_0"},b.material_id)
        with self.assertRaises(GeometryError):
            stitch_parts_unequal(a,b,boundary_loops(a.faces)[0],boundary_loops(b.faces)[0],max_gap=.3)

    def test_unormalized_weights_block(self):
        a,b=make_pair()
        from copox.geometry.kernel import boundary_loops
        val={k:v.copy() for k,v in a.attributes.items()}
        val["WEIGHTS_0"][0,0]=.4
        a=MeshPart(a.positions,a.faces,val,a.material_id)
        with self.assertRaises(GeometryError):
            stitch_parts_unequal(a,b,boundary_loops(a.faces)[0],boundary_loops(b.faces)[0],max_gap=.3)

if __name__=="__main__":unittest.main()
