import copy
import unittest
import numpy as np
from copox.geometry.eyewear_guard import (
    find_labeled_eyewear,remove_labeled_eyewear,eyewear_gate,
    classify_possible_embedded_eyewear
)


def miniature():
    return {
        "materials":[{"name":"GammaHead"}],
        "meshes":[{"primitives":[
            {"extras":{"pieza":"Cabeza"},"material":0,"indices":1},
            {"extras":{"pieza":"Lentes"},"material":0,"indices":2},
            {"extras":{"pieza":"Ojos"},"material":0,"indices":3},
            {"extras":{"pieza":"Cejas"},"material":0,"indices":4}
        ]}],
        "skins":[{"joints":[0,1]}],
        "animations":[{"name":"Blink","channels":[{"target":{"path":"translation"}}]}],
        "nodes":[{"mesh":0,"skin":0}]
    }


class EyewearGuardTests(unittest.TestCase):
    def test_separate_accessory_deleted_other_features_unchanged(self):
        src=miniature()
        before=copy.deepcopy(src)
        out,records=remove_labeled_eyewear(src,expected_count=1)
        self.assertEqual(len(records),1)
        self.assertEqual([x["extras"]["pieza"] for x in out["meshes"][0]["primitives"]],
                         ["Cabeza","Ojos","Cejas"])
        self.assertEqual(src,before)
        self.assertEqual(out["skins"],src["skins"])
        self.assertEqual(out["animations"],src["animations"])
        self.assertEqual(out["materials"],src["materials"])

    def test_empty_face_is_not_removed(self):
        src=miniature()
        src["meshes"][0]["primitives"]=[{"extras":{"pieza":"Cabeza"},"material":0}]
        self.assertFalse(find_labeled_eyewear(src))
        with self.assertRaises(ValueError):
            remove_labeled_eyewear(src,expected_count=1)

    def test_material_is_not_authoritative(self):
        src=miniature()
        src["materials"][0]["name"]="Glasses"
        result,_=remove_labeled_eyewear(src,expected_count=1)
        self.assertEqual(len(result["meshes"][0]["primitives"]),3)

    def test_eyes_and_eyelids_are_never_eyewear(self):
        src=miniature()
        src["meshes"][0]["primitives"]=[
            {"extras":{"pieza":x}} for x in
            ["Eye","Eyelashes","Eyebrows","Iris","LensFlare","Ojos","Nariz","Orejas","Glasses"]]
        self.assertEqual(len(find_labeled_eyewear(src)),1)

    def test_protected_eyes_override_eyewear_proximity(self):
        p=np.array([[0,0,0],[.001,0,0],[0,.001,0],
                    [.020,0,0],[.021,0,0],[.020,.001,0]],float)
        f=np.array([[0,1,2],[3,4,5]],int)
        original=p.copy()
        r=classify_possible_embedded_eyewear(
            p,f,np.array([[0,.0001,0],[.020,.0001,0]]),
            np.array([True,False]),search_radius_m=.005)
        self.assertTrue(r["near_protected"][0])
        self.assertFalse(r["near_unprotected_for_review"][0])
        self.assertTrue(r["near_unprotected_for_review"][1])
        self.assertFalse(r["remove_allowed"])
        np.testing.assert_array_equal(original,p)

    def test_residue_requires_protected_array(self):
        p=np.array([[0,0,0],[1,0,0],[0,1,0]],float)
        with self.assertRaises(ValueError):
            classify_possible_embedded_eyewear(p,np.array([[0,1,2]]),p,
                                                np.zeros(3,dtype=bool))

    def test_gate_requires_eyewear_free_target(self):
        base=miniature()
        target=copy.deepcopy(base)
        target["meshes"][0]["primitives"]=target["meshes"][0]["primitives"][:1]
        report=eyewear_gate(target,base)
        self.assertEqual(report["source_face_explicit_eyewear_primitives"],[])
        self.assertEqual(len(report["source_wardrobe_explicit_eyewear_primitives"]),1)
        self.assertFalse(report["production_visual_approval"])


if __name__=="__main__":
    unittest.main()
