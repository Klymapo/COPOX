import unittest
import numpy as np
from copox.geometry.kernel import GeometryError
from copox.geometry.anatomic_roi import RegionBox,classify_anatomic_band


def synthetic():
    n=24
    angles=2*np.pi*np.arange(n)/n
    rim=np.column_stack([.2*np.cos(angles),np.full(n,.8),.2*np.sin(angles)])
    # Candidate triangle exactly alongside the cap rim, and feature triangle
    # next to it (protected at least at one vertex).
    p=np.array([rim[0],rim[1],rim[0]+[0,-.012,0],
                rim[8],rim[9],rim[8]+[0,-.015,0]],float)
    faces=np.array([[0,1,2],[3,4,5]],int)
    boxes=[RegionBox("protected_face",tuple(p[4]-[.003,.003,.003]),
                      tuple(p[4]+[.003,.003,.003]))]
    return p,faces,rim,boxes


class G2RegionTests(unittest.TestCase):
    def test_candidate_is_different_from_protected(self):
        p,f,r,boxes=synthetic()
        saved=p.copy();faces=f.copy();rim=r.copy()
        result=classify_anatomic_band(p,f,r,boxes,seam_distance=.05,clearance=.025)
        self.assertTrue(result.candidate[0])
        self.assertTrue(result.protected[1])
        self.assertFalse(result.candidate[1])
        np.testing.assert_array_equal(saved,p)
        np.testing.assert_array_equal(faces,f)
        np.testing.assert_array_equal(rim,r)
        self.assertFalse(result.report["cut_allowed"])

    def test_no_gaps_in_classification(self):
        p,f,r,boxes=synthetic()
        data=classify_anatomic_band(p,f,r,boxes,seam_distance=.001,clearance=.02)
        flags=sum(np.asarray(m,dtype=int) for m in
                 (data.protected,data.candidate,data.review,data.unaffected))
        self.assertTrue(np.all(flags==1))

    def test_invalid_roi_rejected(self):
        p,f,r,boxes=synthetic()
        with self.assertRaises(GeometryError):
            classify_anatomic_band(p,f,r,[RegionBox("bad",(1,1,1),(0,0,0))],
                                  seam_distance=.05,clearance=.02)
        with self.assertRaises(GeometryError):
            classify_anatomic_band(p,f,r,boxes,seam_distance=-1,clearance=.02)

    def test_duplicate_named_protectors_rejected(self):
        p,f,r,boxes=synthetic()
        with self.assertRaises(GeometryError):
            classify_anatomic_band(p,f,r,boxes+boxes,seam_distance=.05,clearance=.02)

    def test_no_pretense_of_full_boundary_loop(self):
        p,f,r,boxes=synthetic()
        result=classify_anatomic_band(p,f,r,boxes,seam_distance=.05,clearance=.025)
        self.assertLess(result.rim_sector_coverage,1)
        self.assertFalse(result.report["cut_allowed"])


if __name__=="__main__":unittest.main()
