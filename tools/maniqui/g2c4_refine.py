"""Segunda prueba independiente: cada operación vuelve a V3, nunca a un rechazo."""
import json
import numpy as np
from g2c4_inspect import provenance
from g2c4_candidates import write_candidate,REPORT
j,b,p,f,mp,c,t=provenance();cen=p[f].mean(1)
a=np.array(json.loads((REPORT/'A.json').read_text())['deleted_triangles'])
# The first deletion exposed the missing substrate. This probe preserves
# lower connected hair/skin and tests only the measured upper protrusion.
a=a[cen[a,1]>.66]
print(write_candidate('A2',j,b,p,f,remove=a,extra={'reason':'Only upper confirmed protrusion; lower scaffold kept after A exposed a hole','independent_parent':'V3'})['sha256'])
bb=json.loads((REPORT/'B.json').read_text())['deleted_triangles']
# Exact face IDs inspected in V3 texture provenance and before/after views.
# These become isolated remnants of the old frame, not eyelids or iris.
extra=[567,768,769,770,963,964,967,1876,1881,2432]
assert all(mp[i]>=0 for i in extra)
bb=np.array(sorted(set(bb+extra)))
print(write_candidate('B2',j,b,p,f,remove=bb,extra={'residual_frame_faces_reviewed':extra,'reference_triangle_ids':mp[extra].tolist(),'reason':'Residual lower frame and two lateral struts, proven by original texture and connectivity','independent_parent':'V3'})['sha256'])
