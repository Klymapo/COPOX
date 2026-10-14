"""G2-C5 experiment: combined A+B2+C, rebuilt right-ear surface & facial backing.
This is a deliberately unapproved candidate, exports structural proof and real renders.
"""
from __future__ import annotations
import copy,hashlib,json,struct
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
from glbutils import GLB,CT
from preview import render,mesh,sheet,front_depth
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent; OUT=Path('/mnt/data/COPOX_G2C5_CANDIDATO_SIN_APROBAR.glb');
SRC=ROOT/'V3_BASE_INMUTABLE.glb'; A=ROOT/'modelos/maniqui_G2C4_A_SIN_APROBAR.glb'; B=ROOT/'modelos/maniqui_G2C4_B2_SIN_APROBAR.glb'; C=ROOT/'modelos/maniqui_G2C4_C_SIN_APROBAR.glb'
HASHES={"V3":"0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b","A":"e5660a56d9d611dec63209a22d0857947ea44cadb871fee9026d67d24438e308","B2":"daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec","C":"3a045efdbef61dfe3f0f4c458ab1037ec2e815c7c6f46a3d1e74919bfc125bd9"}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_inputs():
 for name,path in [('V3',SRC),('A',A),('B2',B),('C',C)]:
  if digest(path)!=HASHES[name]:raise ValueError(f'SHA256 diferente: {name}')
 return [GLB(x) for x in [SRC,A,B,C]]
def region_patch(v,f,removed):
 tri=f[removed];remain=np.delete(f,removed,axis=0)
 boundary=np.intersect1d(np.unique(tri),np.unique(remain));
 parent={int(x):int(x) for x in np.unique(tri)}
 def root(i):
  i=int(i)
  while parent[i]!=i:i=parent[i]
  return i
 for T in tri:
  for q in T[1:]: parent[root(q)]=root(T[0])
 cc=defaultdict(list)
 for fi,T in enumerate(tri):cc[root(T[0])].append(fi)
 selected=np.concatenate([np.asarray(ids) for ids in cc.values() if len(ids)>=30 and len(np.intersect1d(np.unique(tri[ids]),boundary))>=5]);
 T=tri[selected];bd=np.intersect1d(np.unique(T),np.unique(remain));inter=np.setdiff1d(np.unique(T),bd)
 adj={int(i):set() for i in np.unique(T)}
 for face in T:
  for t in face:adj[int(t)].update(int(x) for x in face if x!=t)
 lookup={int(i):j for j,i in enumerate(inter)}
 r=[];c=[];val=[];rhs=np.zeros((len(inter),3))
 for k,vid in enumerate(inter):
  nb=adj[vid];r.append(k);c.append(k);val.append(len(nb))
  for v2 in nb:
   if v2 in lookup:r.append(k);c.append(lookup[v2]);val.append(-1)
   else:rhs[k]+=v[v2]
 L=coo_matrix((val,(r,c)),shape=(len(inter),len(inter))).tocsr()
 smooth=np.column_stack([spsolve(L,rhs[:,dim]) for dim in range(3)])
 trial=v.copy();trial[inter]=.70*v[inter]+.30*smooth
 orig_n=np.cross(v[T[:,1]]-v[T[:,0]],v[T[:,2]]-v[T[:,0]])
 new_n=np.cross(trial[T[:,1]]-trial[T[:,0]],trial[T[:,2]]-trial[T[:,0]])
 inverted=np.einsum('ij,ij->i',orig_n,new_n)<0
 if inverted.any() or np.min(np.linalg.norm(new_n,axis=1))<=1e-9:raise ValueError('Reparación de oreja: degeneración o inversión')
 return trial,T,inter,{'input_right_hair_faces':len(removed),'reconstructed_skin_faces':len(T),'isolated_fragments_left_shaved':len(removed)-len(T),'edited_interior_vertices':len(inter),'protected_border_vertices':len(bd),'max_smoothing_displacement_m':float(np.linalg.norm(trial[inter]-v[inter],axis=1).max()),'new_inversions':int(inverted.sum())}

def skin_panels(face_pos,orig_joints,orig_weights,depth_grid,project):
 """Recessed, pixel-targeted prototype inpainting. Only place cells where
 a genuine front-facing ray is empty; never draw over a real facial surface.
 These are new meshes, NOT watertight patches. For evaluation only.
 """
 from scipy.ndimage import distance_transform_edt
 valid=depth_grid>.07
 _,nearest=distance_transform_edt(~valid,return_indices=True)
 nearest_depth=depth_grid[tuple(nearest)]
 pos=[];faces=[];norm=[];joints=[];weights=[];stats={}
 candidates=np.where((face_pos[:,1]<.74)&(face_pos[:,2]<.205)&(face_pos[:,2]>.015))[0]
 for name,xs,ys in [('facial_voids',np.linspace(-.165,.165,130),np.linspace(.605,.736,66)),
                    ('submandibular_voids',np.linspace(-.133,.133,99),np.linspace(.540,.61,38))]:
  X,Y=np.meshgrid(xs,ys)
  px,py=project(X,Y);depth=depth_grid[py,px]
  holes=depth<-900
  # If any corner already shows a protected cheek/eye, skip the quad.
  inside=holes[:-1,:-1]&holes[1:,:-1]&holes[:-1,1:]&holes[1:,1:]
  original_shape=inside.shape
  kept=int(inside.sum())
  vertmap={}
  def getvert(iy,ix):
   key=(int(iy),int(ix))
   if key in vertmap:return vertmap[key]
   x=float(xs[ix]);y=float(ys[iy]);near=float(nearest_depth[py[iy,ix],px[iy,ix]])
   # In the missing region, sit just *behind* the existing cheek boundary.
   z=.153 if name=='facial_voids' else .113
   point=np.array([x,y,z]);nidx=candidates[np.linalg.norm((face_pos[candidates]-point)*np.array([1,1,1.2]),axis=1).argmin()]
   idx=len(face_pos)+len(pos);pos.append(point);norm.append([0,0,1]);joints.append(orig_joints[nidx]);weights.append(orig_weights[nidx]);vertmap[key]=idx
   return idx
  initial=len(faces)
  for iy,ix in np.argwhere(inside):
   a=getvert(iy,ix);b=getvert(iy,ix+1);c=getvert(iy+1,ix);d=getvert(iy+1,ix+1)
   faces.extend(((a,b,c),(b,d,c)))
  stats[name]={'filled_grid_cells':kept,'new_faces':len(faces)-initial,'new_vertices':len(vertmap),'original_grid_shape':list(original_shape)}
 if not pos:raise ValueError('No true optical holes were detected')
 return np.asarray(pos,dtype=np.float32),np.asarray(faces,dtype=np.int64),np.asarray(norm,dtype=np.float32),np.asarray(joints),np.asarray(weights),stats

def write_glb(orig,c,face_pos,face_norm,face_index,extra_pos,extra_tri,extra_normal,extra_j,extra_w):
 j=copy.deepcopy(c.doc);raw=bytearray(c.bin)
 old=j['meshes'][0]['primitives'][0]
 def add(arr,typ,component,target):
  arr=np.asarray(arr,dtype=CT[component]);raw.extend(b'\0'*((-len(raw))%4));off=len(raw);raw.extend(arr.tobytes())
  j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':arr.nbytes,'target':target});a={'bufferView':len(j['bufferViews'])-1,'componentType':component,'count':len(arr),'type':typ}
  if typ=='VEC3':a.update({'min':arr.min(axis=0).tolist(),'max':arr.max(axis=0).tolist()})
  j['accessors'].append(a);return len(j['accessors'])-1
 p,curr_f,att=c.prim(0)
 att2={'POSITION':np.vstack([face_pos,extra_pos]),'NORMAL':np.vstack([face_norm,extra_normal]),'JOINTS_0':np.vstack([att['JOINTS_0'],extra_j]),'WEIGHTS_0':np.vstack([att['WEIGHTS_0'],extra_w])}
 for key,data in att2.items():
  oldid=old['attributes'][key]; oldacc=j['accessors'][oldid]
  old['attributes'][key]=add(data,oldacc['type'],oldacc['componentType'],34962)
 old['indices']=add(np.concatenate([face_index,extra_tri]).astype(np.uint32).ravel(),'SCALAR',5125,34963)
 old.setdefault('extras',{})['copox_candidate']=('G2C5 experimental optical backing (not welded)' if len(extra_pos) else 'G2C5 conservative: A partial inpainting + B2 + C, no new backing');j['asset'].setdefault('extras',{})['copox_review']='NOT APPROVED / DO NOT MERGE'
 j['buffers'][0]['byteLength']=len(raw)
 raw.extend(b'\0'*((-len(raw))%4));s=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();s+=b' '*((-len(s))%4)
 payload=b'glTF'+struct.pack('<II',2,12+8+len(s)+8+len(raw))+struct.pack('<I4s',len(s),b'JSON')+s+struct.pack('<I4s',len(raw),b'BIN\0')+raw
 OUT.write_bytes(payload)
 return j

def main():
 g,ga,gb,gc=read_inputs();_,F,orig=g.prim(0);_,FA,_=ga.prim(0);_,FB,_=gb.prim(0);_,FC,Catt=gc.prim(0)
 d=np.load(ROOT/'face_selection.npz');remA=d['remove_A'];remB=d['remove_B']
 vnew,reinstate,inter,stat=region_patch(Catt['POSITION'],F,remA)
 # Existing jaw improvement from C preserved; eyes B2 frame removed.
 keep=np.delete(F,np.union1d(remA,remB),axis=0);face_index=np.vstack((keep,reinstate))
 face_normal=Catt['NORMAL'].copy()
 # Recompute only newly inpainted vertices; other C normals remain EXACT.
 tri=vnew[reinstate];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);summ=np.zeros_like(vnew)
 for i in range(3):np.add.at(summ,reinstate[:,i],cross)
 for i in inter:
  n=summ[i];L=np.linalg.norm(n)
  if L>1e-9:face_normal[i]=n/L
 # Use B2-cleaned, A-reconstructed and C-jaw geometry for occlusion.
 extra_scene=[vnew[face_index]]
 for pid in [1,2]:
  _,fi,attp=gc.prim(pid);extra_scene.append(attp['POSITION'][fi])
 depth_grid,project=front_depth(extra_scene)
 extra_pos,extra_tri,extra_n,extra_j,extra_w,panel_stats=skin_panels(vnew,Catt['JOINTS_0'],Catt['WEIGHTS_0'],depth_grid,project)
 # ensure no new triangles are degenerate
 vv=np.vstack((vnew,extra_pos));allf=np.vstack((face_index,extra_tri));cr=np.cross(vv[allf[:,1]]-vv[allf[:,0]],vv[allf[:,2]]-vv[allf[:,0]])
 area=np.linalg.norm(cr,axis=1)/2
 # baseline old degenerate triangles are historical; only compare newly added
 if np.min(area[-len(extra_tri):])<1e-9:raise ValueError('New underlay degenerate triangles')
 write_glb(g,gc,vnew,face_normal,face_index,extra_pos,extra_tri,extra_n,extra_j,extra_w)
 out=GLB(OUT);_,nf,atts=out.prim(0)
 if len(out.doc['skins'][0]['joints'])!=56 or len(out.doc['animations'])!=29 or len(nf)!=len(allf):raise ValueError('GLB invalid')
 if out.doc['meshes'][0]['primitives'][1:]!=gc.doc['meshes'][0]['primitives'][1:]:raise ValueError('Non-face primitives changed')
 if any(out.doc.get(k)!=gc.doc.get(k) for k in ['skins','animations','nodes','materials','scenes','textures','images']):raise ValueError('Scene/rig changed')
 if not np.array_equal(atts['POSITION'][:len(vnew)],vnew):raise ValueError('Position roundtrip changed')
 stat.update(panel_stats)
 info={'status':'EXPERIMENTAL_VISUAL_REVIEW_REQUIRED','glb':str(OUT),'sha256':digest(OUT),'sources':HASHES,'face_triangles_previous':len(F),'face_triangles_new':len(nf),'removed_frame_B2':len(remB),'removed_hair_A':len(remA),'restored_skin_right_ear':stat,'retained_C_jaw_displaced_count':int(np.count_nonzero(np.any(vnew!=orig['POSITION'],axis=1))),'underlays_are_true_meshes_not_welded':True,'known_limitations':['Added eye and jaw underlay surfaces cover visible gaps but are not boundary welded','No claim of rigged neck or functional facial animation','Needs Godot structural QA and aesthetic approval'],'no_merge':True}
 Path('/mnt/data/COPOX_G2C5_REPORTE.json').write_text(json.dumps(info,indent=2,ensure_ascii=False))
 return info
if __name__=='__main__':
 x=main();print(json.dumps(x,indent=2,ensure_ascii=False))
 sheet([('V3 ORIGINAL',SRC),('A CON HUECO',A),('G2-C5 COMBINADO',OUT)],filename='/mnt/data/COPOX_G2C5_COMPARATIVA_4V.png')
