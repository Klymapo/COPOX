"""Comparación regional de cruces propios de triángulos, con broad phase AABB.
No clasifica contactos coplanares como intersecciones: se informan aparte.
"""
from pathlib import Path
import sys,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
from g2c4_inspect import BASE

def segment_hits_triangles(a,b,tri,eps=1e-8):
 direction=b-a;e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
 h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
 ok=abs(det)>1e-12;inv=np.zeros_like(det);inv[ok]=1/det[ok]
 s=a-tri[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.einsum('j,ij->i',direction,q);t=inv*np.einsum('ij,ij->i',e2,q)
 return ok&(u>eps)&(v>eps)&(u+v<1-eps)&(t>eps)&(t<1-eps)

def intersections(tris,changed):
 lo=tris.min(1);hi=tris.max(1);pairs=set();coplanar=set()
 for idx in changed:
  tr=tris[idx];ids=np.flatnonzero(np.all(hi>=lo[idx]-1e-8,axis=1)&np.all(lo<=hi[idx]+1e-8,axis=1));ids=ids[ids!=idx]
  # Spatial seams are adjacent even when index split; don't count contact.
  same=(np.linalg.norm(tris[ids,:,None,:]-tr[None,None,:,:],axis=3)<1e-6).any((1,2));ids=ids[~same]
  if not len(ids):continue
  other=tris[ids];hit=np.zeros(len(ids),bool)
  for e in range(3):hit|=segment_hits_triangles(tr[e],tr[(e+1)%3],other)
  # Reverse edges, vectorized Möller-Trumbore against fixed triangle.
  n=np.cross(tr[1]-tr[0],tr[2]-tr[0]);ln=np.linalg.norm(n)
  if ln>1e-12:
   distances=np.einsum('nij,j->ni',other-tr[0],n/ln)
   co=np.max(abs(distances),axis=1)<1e-7
   for k in ids[co]:coplanar.add(tuple(sorted([int(idx),int(k)])))
  for k,ot in enumerate(other):
   if hit[k]:continue
   for e in range(3):
    if segment_hits_triangles(ot[e],ot[(e+1)%3],tr[None])[0]:hit[k]=True;break
  for k in ids[hit]:pairs.add(tuple(sorted([int(idx),int(k)])))
 return pairs,coplanar

def main():
 r=json.loads(Path('docs/maniqui/g2c4/C.json').read_text());changed=np.array(r['affected_retained_triangles'])
 base=render.gather(BASE);cand=render.gather(r['glb']);bt=np.concatenate([t[0] for t in base if len(t[0])]);ct=np.concatenate([t[0] for t in cand if len(t[0])]);a,ac=intersections(bt,changed);b,bc=intersections(ct,changed)
 d={'region':'C, changed jaw triangles vs all visible body/head triangles','changed_faces':changed.tolist(),'proper_crossings_before':sorted(a),'proper_crossings_after':sorted(b),'new_proper_crossings':sorted(b-a),'removed_proper_crossings':sorted(a-b),'coplanar_aabb_candidates_before':len(ac),'coplanar_aabb_candidates_after':len(bc),'limitations':['excludes shared-position adjacency and mere touching','coplanar overlap not certified','rest pose only; no continuous swept-volume test']}
 Path('docs/maniqui/g2c4/C_intersections.json').write_text(json.dumps(d,indent=2)+'\n');print({k:v for k,v in d.items() if not isinstance(v,list)})
 print('proper crossing counts',len(a),len(b),'new',len(b-a))
if __name__=='__main__':main()
