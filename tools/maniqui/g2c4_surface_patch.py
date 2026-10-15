"""A3: parche lateral medido, anclado, con originales intocables.
No hay parámetros universales de personaje: perfil V3 verificado por SHA.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from g2c4_inspect import provenance,BASE,SHA
from g2c4_candidates import topology
from copox.geometry.kernel import boundary_loops
from reparar_v03 import add_accessor,write_glb
import render
OUT=Path('build/g2c4_continuacion');OUT.mkdir(exist_ok=True)
def inside(points,poly):
 x,y=points.T;ok=np.zeros(len(points),bool)
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  crossing=((a[1]>y)!=(b[1]>y))&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-30)+a[0]);ok^=crossing
 return ok

def constrained_polygon(poly,grid):
 """Ear clipping and point insertion; preserve every measured boundary edge.
 No geometry-library dependency or character-specific coordinate assumptions.
 """
 def cross(a,b):return a[0]*b[1]-a[1]*b[0]
 def orient(a,b,c):return cross(b-a,c-a)
 def contains(q,t,eps=1e-13):
  signs=np.array([orient(t[i],t[(i+1)%3],q) for i in range(3)])
  return np.all(signs>=-eps) or np.all(signs<=eps)
 # Refuse self-intersecting charts instead of bridging them silently.
 for i in range(len(poly)):
  a,b=poly[i],poly[(i+1)%len(poly)]
  for k in range(i+2,len(poly)):
   if (k+1)%len(poly)==i:continue
   c,d=poly[k],poly[(k+1)%len(poly)]
   if orient(a,b,c)*orient(a,b,d)<-1e-20 and orient(c,d,a)*orient(c,d,b)<-1e-20:
    raise ValueError(f'Self-crossing projected boundary: edges {i}, {k}')
 area=sum(cross(a,b) for a,b in zip(poly,np.roll(poly,-1,axis=0)))
 remaining=list(range(len(poly)))
 if area<0:remaining.reverse()
 tri=[]
 while len(remaining)>3:
  found=False
  for k,b in enumerate(remaining):
   a,c=remaining[k-1],remaining[(k+1)%len(remaining)]
   if orient(poly[a],poly[b],poly[c])<=1e-14:continue
   if any(contains(poly[v],poly[[a,b,c]]) for v in remaining if v not in (a,b,c)):continue
   tri.append([a,b,c]);remaining.pop(k);found=True;break
  if not found:raise ValueError('No nondegenerate ear; chart needs a different parameterization')
 tri.append(remaining);uv=list(poly)
 for q in grid:
  for k,t in enumerate(tri):
   pts=np.array([uv[v] for v in t])
   if contains(q,pts):
    if min(abs(orient(pts[i],pts[(i+1)%3],q)) for i in range(3))<1e-12:break
    v=len(uv);uv.append(q);a,b,c=tri.pop(k);tri.extend([[a,b,v],[b,c,v],[c,a,v]]);break
 # Lawson flips only convex internal quadrilaterals: constraints never move.
 uv=np.array(uv)
 for iteration in range(1000):
  edge_faces={}
  for k,t in enumerate(tri):
   for a,b in zip(t,t[1:]+t[:1]):edge_faces.setdefault(tuple(sorted((a,b))),[]).append(k)
  flipped=False
  for (a,b),fs in edge_faces.items():
   if len(fs)!=2:continue
   x,y=fs;c=next(v for v in tri[x] if v not in (a,b));d=next(v for v in tri[y] if v not in (a,b))
   if orient(uv[c],uv[d],uv[a])*orient(uv[c],uv[d],uv[b])>=-1e-20:continue
   t=uv[[a,b,c]]-uv[d];det=np.linalg.det(np.column_stack([t,(t*t).sum(1)]))
   scale=float(np.ptp(uv[[a,b,c,d]],axis=0).max())
   if det*orient(uv[a],uv[b],uv[c])<=max(1e-20,scale**6*1e-12):continue
   new=[[c,d,a],[d,c,b]]
   for nt in new:
    if orient(*uv[nt])<0:nt[1],nt[2]=nt[2],nt[1]
   tri[x],tri[y]=new;flipped=True;break
  if not flipped:break
 else:raise ValueError('Edge-flip convergence limit')
 return uv,np.array(tri)

def triangulate_harmonic(boundary,step):
 """Interpolate surface X inside measured YZ polygon; refuse broken borders."""
 poly=boundary[:,1:];low=poly.min(0);high=poly.max(0)
 grid=np.stack(np.meshgrid(np.arange(low[0]+step,high[0],step),np.arange(low[1]+step,high[1],step)),axis=-1).reshape(-1,2)
 grid=grid[inside(grid,poly)]
 if len(grid):grid=grid[np.linalg.norm(grid[:,None]-poly,axis=2).min(1)>step*.3]
 uv,tri=constrained_polygon(poly,grid)
 edges=np.sort(np.vstack([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1);eu,cnt=np.unique(edges,axis=0,return_counts=True)
 actual={tuple(x) for x in eu[cnt==1]};expected={tuple(sorted((i,(i+1)%len(poly)))) for i in range(len(poly))}
 if actual!=expected:raise ValueError(f'La triangulación no conserva el contorno: missing={len(expected-actual)}, extra={len(actual-expected)}')
 adjacency=[set() for _ in uv]
 for a,b in eu:adjacency[a].add(int(b));adjacency[b].add(int(a))
 n=len(poly);N=len(uv)-n;mat=lil_matrix((N,N));rhs=np.zeros(N)
 for i in range(n,len(uv)):
  adj=adjacency[i];mat[i-n,i-n]=len(adj)
  for k in adj:
   if k<n:rhs[i-n]+=boundary[k,0]
   else:mat[i-n,k-n]-=1
 xx=spsolve(mat.tocsr(),rhs);p=np.column_stack([np.r_[boundary[:,0],xx],uv])
 # +X exterior, preserving original anchor geometry.
 nn=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 tri[nn[:,0]<0]=tri[nn[:,0]<0][:,[0,2,1]]
 return p,tri

def main():
 target=OUT/'maniqui_G2C4_A3_PARCHE_LATERAL_SIN_APROBAR.glb'
 if target.exists():raise FileExistsError(target)
 j,b,p,f,mp,c,_=provenance();cap=j['meshes'][0]['primitives'][1];cp=render.acc(j,b,cap['attributes']['POSITION']);cf=render.acc(j,b,cap['indices']).astype(int).reshape(-1,3)
 rim=np.array(boundary_loops(cf)[0]);rp=cp[rim]
 def cap_anchor(q):
  dist=np.linalg.norm(rp-np.array(q),axis=1);i=int(dist.argmin());assert dist[i]<.0001;return i
 start=cap_anchor([.20913,.672,-.03114]);end=cap_anchor([.14339,.57217,-.12824]);arc=[];idx=start
 while True:
  arc.append(int(rim[idx]))
  if idx==end:break
  idx=(idx+1)%len(rim)
  assert len(arc)<100,'Selected wrong side of cap'
 # Face boundary tracked in the real retained mesh after hair indices removal.
 anchors=np.array([[.188946,.665068,-.029632],[.178762,.651830,-.028233],[.176487,.644617,-.027745],[.172985,.631110,-.026015],[.171942,.634490,-.026175],[.169869,.624741,-.024543],[.167202,.616528,-.023638],[.164970,.610225,-.021405],[.160750,.591817,-.024034],[.158039,.574796,-.034874],[.156522,.572575,-.036292],[.155798,.570969,-.039846]])
 faceids=[]
 for q in anchors:
  ds=np.linalg.norm(p-q,axis=1);i=int(ds.argmin());assert ds[i]<2e-6;faceids.append(i)
 # clockwise boundary: top cap -> front retained edge -> bottom cap -> rear cap.
 boundary=np.vstack([cp[arc[0]],p[faceids],cp[arc[:0:-1]]])
 surf,tris=triangulate_harmonic(boundary,.006)
 nboundary=len(boundary)
 # Boundary mappings reuse cap indices, copy face anchors into cap with their
 # exact skin weights; their spatial seam is explicit, never called welded.
 local_to_cap={0:arc[0]}
 for k,capid in enumerate(arc[:0:-1],start=1+len(faceids)):local_to_cap[k]=capid
 appendids=[i for i in range(len(surf)) if i not in local_to_cap]
 for k,i in enumerate(appendids):local_to_cap[i]=len(cp)+k
 newp=np.vstack([cp,surf[appendids]]);newf=np.array([[local_to_cap[int(i)] for i in t] for t in tris]);allf=np.vstack([cf,newf])
 attrs={key:render.acc(j,b,val) for key,val in cap['attributes'].items()};faceattrs={key:render.acc(j,b,val) for key,val in j['meshes'][0]['primitives'][0]['attributes'].items()}
 normals=np.zeros_like(surf);fn=np.cross(surf[tris[:,1]]-surf[tris[:,0]],surf[tris[:,2]]-surf[tris[:,0]])
 for k in range(3):np.add.at(normals,tris[:,k],fn)
 normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
 # All anchors must have identical head influence; fail rather than invent.
 cj=attrs['JOINTS_0'][arc];cw=attrs['WEIGHTS_0'][arc];fj=faceattrs['JOINTS_0'][faceids];fw=faceattrs['WEIGHTS_0'][faceids]
 assert np.all(cj==cj[0]) and np.all(cw==cw[0]) and np.all(fj==cj[0]) and np.all(fw==cw[0]),'Need explicit weight interpolation; do not guess'
 attrs['POSITION']=newp;attrs['NORMAL']=np.vstack([attrs['NORMAL'],normals[appendids]])
 attrs['JOINTS_0']=np.vstack([attrs['JOINTS_0'],np.tile(cj[0],(len(appendids),1))]);attrs['WEIGHTS_0']=np.vstack([attrs['WEIGHTS_0'],np.tile(cw[0],(len(appendids),1))])
 d=copy.deepcopy(j);raw=bytearray(b);dest=d['meshes'][0]['primitives'][1]
 for key,array in attrs.items():
  old=j['accessors'][cap['attributes'][key]];dtype=render.CT[old['componentType']]
  dest['attributes'][key]=add_accessor(d,raw,array.astype(dtype),old['componentType'],old['type'],34962,key=='POSITION')
 dest['indices']=add_accessor(d,raw,allf.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 removed=json.loads(Path('docs/maniqui/g2c4/A.json').read_text())['deleted_triangles']
 d['meshes'][0]['primitives'][0]['indices']=add_accessor(d,raw,np.delete(f,removed,axis=0).astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 write_glb(target,d,raw)
 assert raw[:len(b)]==b
 for key in ('nodes','skins','animations','materials'):assert d[key]==j[key]
 assert np.array_equal(newp[:len(cp)],cp) and np.array_equal(allf[:len(cf)],cf)
 report={'name':'A3','baseline_sha256':SHA,'glb':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'removed_faces':removed,'added_cap_vertices':len(appendids),'added_cap_triangles':len(newf),'original_cap_vertices_and_faces_exact':True,'original_face_attributes_exact':True,'ear_skin_and_facial_faces_retained':True,'cap_boundary_ids':arc,'face_anchor_ids':faceids,'patch_bounds':[surf.min(0).tolist(),surf.max(0).tolist()],'patch_topology':topology(surf,tris),'skin_weights_from_identical_boundary_influences':True,'cap_join_index_welded':True,'face_join_spatial_seam_only':True,'artistic_status':'PENDING','no_promotion':True}
 (OUT/'A3.json').write_text(json.dumps(report,indent=2)+'\n');np.savez(OUT/'A3_patch.npz',positions=surf,faces=tris,new_cap_faces=newf)
 print(json.dumps(report))
if __name__=='__main__':main()
