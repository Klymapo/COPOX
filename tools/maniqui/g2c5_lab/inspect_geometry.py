import numpy as np
from collections import Counter,defaultdict
from glbutils import GLB
root='/mnt/data/g2c5_lab/'
g=GLB(root+'V3_BASE_INMUTABLE.glb');p,f,a=g.prim(0);v=a['POSITION'];
ga=GLB(root+'modelos/maniqui_G2C4_A_SIN_APROBAR.glb');_,af,_=ga.prim(0)
gb=GLB(root+'modelos/maniqui_G2C4_B2_SIN_APROBAR.glb');_,bf,_=gb.prim(0)
# faces removals use tuples
fids={tuple(x):i for i,x in enumerate(f)}
remA=np.array([i for i,x in enumerate(f) if tuple(x) not in set(map(tuple,af))]); remB=np.array([i for i,x in enumerate(f) if tuple(x) not in set(map(tuple,bf))]);
print('A',len(remA),'B',len(remB),'overlap',len(set(remA)&set(remB)))
for name,rem in [('A',remA),('B',remB)]:
 pts=v[f[rem]].reshape(-1,3)
 print(name,'min max',pts.min(axis=0),pts.max(axis=0))

def edges_with_count(F):
   uv,inv=np.unique(np.round(v,6),axis=0,return_inverse=True)
   wf=inv[F]
   es=np.sort(np.vstack([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1)
   uniq,cnt=np.unique(es,axis=0,return_counts=True)
   return uv,uniq,cnt
u,ed,cnt=edges_with_count(af)
for name,F in [('base',f),('A',af),('B',bf)]:
 u,e,c=edges_with_count(F);e=e[c==1];pa=u[e]
 roi=(np.mean(pa[:,:,0],axis=1)>.12)&(np.mean(pa[:,:,2],axis=1)<0)&(np.mean(pa[:,:,1],axis=1)>.55)&(np.mean(pa[:,:,1],axis=1)<.78)
 print(name,'total boundaries',len(e),'ROI right ear',roi.sum())
 print('roi bounds',pa[roi].reshape(-1,3).min(axis=0) if roi.any() else None,pa[roi].reshape(-1,3).max(axis=0) if roi.any() else None)
# boundary differences A vs v3
u,eA,cA=edges_with_count(af);u,eV,cV=edges_with_count(f)
assert np.array_equal(u,u)
newE={tuple(x) for x in eA[cA==1]} - {tuple(x) for x in eV[cV==1]}
print('New hole edges A',len(newE))
P=np.array([u[list(x)] for x in newE]);print('bounds',P.reshape(-1,3).min(axis=0),P.reshape(-1,3).max(axis=0))
np.savez(root+'face_selection.npz',remove_A=remA,remove_B=remB)
