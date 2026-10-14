import unittest
import numpy as np
from copox.geometry.contour_graph import inspect_contour_graph


class ContourGraphTests(unittest.TestCase):
    def test_closed_annular_boundary_is_detected(self):
        # Una superficie tubular sin tapas: 2 loops y ninguna arista nonmanifold.
        n=12
        a=np.arange(n)*2*np.pi/n
        lower=np.c_[np.cos(a),np.sin(a),np.zeros(n)]
        upper=lower+[0,0,.5]
        p=np.vstack([lower,upper])
        f=[]
        for k in range(n):
            q=(k+1)%n
            f.extend([[k,q,n+k],[q,n+q,n+k]])
        t=inspect_contour_graph(p,np.asarray(f),upper,correspondence_distance=.01)
        self.assertEqual(t["closed_simple_cycles"],2)
        self.assertEqual(t["nonmanifold_edges"],0)
        self.assertEqual(t["potential_full_ring_cycles"],1)
        self.assertFalse(t["stitch_ready"])

    def test_open_disk_boundary_is_closed_loop(self):
        n=8;ang=np.arange(n)*2*np.pi/n
        p=np.vstack([np.c_[np.cos(ang),np.sin(ang),np.zeros(n)],[[0,0,0]]])
        f=np.asarray([[n,k,(k+1)%n] for k in range(n)])
        t=inspect_contour_graph(p,f,p[:n],correspondence_distance=.02)
        self.assertEqual(t["boundary_edges"],8)
        self.assertEqual(t["closed_simple_cycles"],1)
        self.assertFalse(t["stitch_ready"])

    def test_nonmanifold_is_reported_not_promoted(self):
        p=np.array([[0,0,0],[1,0,0],[0,1,0],[0,-1,0],[0,0,1]])
        f=np.asarray([[0,1,2],[1,0,3],[0,1,4]])
        r=np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],
                    [2,0,0],[2,1,0],[1,0,1]])
        t=inspect_contour_graph(p,f,r)
        self.assertGreater(t["nonmanifold_edges"],0)
        self.assertFalse(t["stitch_ready"])

    def test_coincident_raw_vertices_only_weld_for_diagnosis(self):
        p=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,0],[0,1,0],[-1,0,0]])
        f=np.asarray([[0,1,2],[3,4,5]])
        r=np.array([[0,0,0],[1,0,0],[0,1,0],[-1,0,0]])
        before=p.copy()
        t=inspect_contour_graph(p,f,r)
        self.assertEqual(t["quantized_positions"],4)
        np.testing.assert_array_equal(p,before)


if __name__=="__main__":unittest.main()
