#!/usr/bin/env python3
"""Audita archivos exportados, facciones, bytes de rig/animación y topología de la cúpula."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import render


def audit(base, candidates, output):
    j,b=render.load(base); p0=j['meshes'][0]['primitives'][0]
    v=render.acc(j,b,p0['attributes']['POSITION']); f=render.acc(j,b,p0['indices']).astype(int).reshape(-1,3)
    features=np.any(((v[:,2]>.155)&(np.abs(v[:,0])<.185)&(v[:,1]<.775))[f],axis=1)
    ears=np.any(((np.abs(v[:,0])>.205)&(v[:,1]<.712))[f],axis=1)
    result=[]
    for candidate in candidates:
        jj,bb=render.load(candidate); ps=jj['meshes'][0]['primitives'];face=ps[0];cap=ps[1]
        assert bb[:len(b)]==b
        assert all(j[k]==jj[k] for k in ('nodes','skins','animations','materials'))
        assert ps[2:]==j['meshes'][0]['primitives'][2:]
        for key,idx in p0['attributes'].items():
            assert np.array_equal(render.acc(j,b,idx),render.acc(jj,bb,face['attributes'][key])[:len(v)])
        cf=render.acc(jj,bb,face['indices']).astype(int).reshape(-1,3)
        triangles={tuple(t) for t in cf}
        missing_face=sum(tuple(t) not in triangles for t in f[features])
        missing_ear=sum(tuple(t) not in triangles for t in f[ears])
        cp=render.acc(jj,bb,cap['attributes']['POSITION']);ci=render.acc(jj,bb,cap['indices']).astype(int).reshape(-1,3)
        area=np.linalg.norm(np.cross(cp[ci[:,1]]-cp[ci[:,0]],cp[ci[:,2]]-cp[ci[:,0]]),axis=1)/2
        edges=np.sort(np.vstack([ci[:,[0,1]],ci[:,[1,2]],ci[:,[2,0]]]),axis=1)
        _,counts=np.unique(edges,axis=0,return_counts=True)
        assert np.isfinite(cp).all() and area.min()>1e-12 and counts.max()==2
        for p in ps:
            A=p['attributes'];pv=render.acc(jj,bb,A['POSITION']);w=render.acc(jj,bb,A['WEIGHTS_0']);joint=render.acc(jj,bb,A['JOINTS_0'])
            indices=render.acc(jj,bb,p['indices'])
            assert np.isfinite(pv).all() and indices.min()>=0 and indices.max()<len(pv)
            assert np.isfinite(w).all() and w.min()>=0 and np.max(np.abs(w.sum(1)-1))<1e-6 and joint.max()<56
        row=dict(path=candidate,sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),bones=56,clips=29,rig_animation_original_bytes_equal=True,all_body_primitives_equal=True,original_face_attribute_prefix_equal=True,protected_feature_triangles=int(features.sum()),missing_feature_triangles=int(missing_face),protected_ear_triangles=int(ears.sum()),missing_ear_triangles=int(missing_ear),cap_min_triangle_area_m2=float(area.min()),cap_degenerate_triangles=0,cap_nonmanifold_edges=0,cap_boundary_edges=int((counts==1).sum()),cap_watertight=False,cap_face_seam_welded=False)
        row['preservation_pass']=missing_face==missing_ear==0
        result.append(row)
    Path(output).write_text(json.dumps({'baseline':base,'baseline_sha256':hashlib.sha256(Path(base).read_bytes()).hexdigest(),'candidates':result},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('output');p.add_argument('candidates',nargs='+');a=p.parse_args();audit(a.baseline,a.candidates,a.output)
