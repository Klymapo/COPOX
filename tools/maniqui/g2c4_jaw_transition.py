"""C2: anatomical underside experiment; measured V3 profile, immutable input.
Generic bridge uses explicit ordered anchors and a rig-aligned open ring.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[2])]
from g2c4_inspect import provenance,SHA
from g2c4_candidates import topology
from reparar_v03 import add_accessor,write_glb
from g2c4_intersections import intersections
import render
OUT=Path('build/g2c4_continuacion')

def bridge(outer,center,axis,radii,levels=5):
 ex=np.array([1.,0,0]);ex-=axis*np.dot(ex,axis);ex/=np.linalg.norm(ex);ez=np.cross(ex,axis)
 offset=outer-center;theta=np.arctan2(offset@ez,offset@ex)
 inner=center+np.cos(theta)[:,None]*radii[0]*ex+np.sin(theta)[:,None]*radii[1]*ez
 rows=[outer*(1-t)+inner*t for t in np.linspace(0,1,levels)]
 p=np.concatenate(rows);n=len(outer);faces=[]
 for row in range(levels-1):
  for k in range(n):
   a=row*n+k;b=row*n+(k+1)%n;c=(row+1)*n+k;d=(row+1)*n+(k+1)%n
   faces.extend([[a,b,c],[b,d,c]])
 f=np.array(faces);tr=p[f];norm=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);flip=(norm@axis)>0;f[flip]=f[flip][:,[0,2,1]]
 return p,f,inner

def main():
 label='C3' if '--c3' in sys.argv else 'C2'
 path=OUT/f'maniqui_G2C4_{label}_TRANSICION_MANDIBULAR_SIN_APROBAR.glb'
 if path.exists():raise FileExistsError(path)
 j,b,p,f,_,_,_=provenance();head=j['meshes'][0]['primitives'][0];cap=j['meshes'][0]['primitives'][1];oldneck=j['meshes'][0]['primitives'][2]
 u,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=inv[f];edges=np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1);eu,co=np.unique(edges,axis=0,return_counts=True)
 low=eu[(co==1)&(u[eu][:,:,1].max(1)<.564)&(u[eu][:,:,2].min(1)>-.005)]
 adj={}
 for a,c in low:adj.setdefault(int(a),[]).append(int(c));adj.setdefault(int(c),[]).append(int(a))
 assert all(len(v)<=2 for v in adj.values())
 ends=[k for k,v in adj.items() if len(v)==1];assert len(ends)==2
 start=min(ends,key=lambda k:u[k,0]);chain=[start]
 while True:
  nxt=[k for k in adj[chain[-1]] if k not in chain]
  if not nxt:break
  chain.append(nxt[0])
 assert len(chain)==len(adj)
 ids=[int(np.flatnonzero(inv==k)[0]) for k in chain];outerfront=p[ids].copy()
 # Measured V3 artistic target: chin 0.538 m, angle 0.560 m.
 # Lift laterally, retain the front/back and lateral coordinates exactly.
 span=max(abs(outerfront[:,0]));depth=np.ptp(outerfront[:,2]);front=outerfront[:,2].max()
 ytarget=.538+.014*(outerfront[:,0]/span)**2+.010*((front-outerfront[:,2])/depth)**2
 pp=p.copy();changed=[]
 for k,y in zip(chain,ytarget):
  indices=np.flatnonzero(inv==k);pp[indices,1]=y;changed.extend(indices.tolist())
 changed=np.array(changed);affected=np.flatnonzero(np.isin(f,changed).any(1))
 on=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);nn=np.cross(pp[f[:,1]]-pp[f[:,0]],pp[f[:,2]]-pp[f[:,0]])
 inverted=np.flatnonzero((on*nn).sum(1)<-1e-18)
 if len(inverted):raise ValueError(f'Jaw movement inverts faces {inverted.tolist()}')
 cp=render.acc(j,b,cap['attributes']['POSITION']);capids=np.arange(5041,5078) if label=='C3' else np.arange(5037,5082)
 assert np.all(cp[capids,1]<=.57218) and cp[capids[0],0]>.11 and cp[capids[-1],0]<-.15
 outer=np.vstack([pp[ids],cp[capids]])
 neck=np.array([0,.50180505,.01353791]);head_origin=np.array([0,.53068592,.01805054]);axis=head_origin-neck;axis/=np.linalg.norm(axis);center=neck+axis*(.026 if label=='C3' else .015)
 radii=np.array([.064,.050]);vp,vf,ring=bridge(outer,center,axis,radii)
 # Same head joint at measured outer anchors; interpolate into original neck mix.
 ha={k:render.acc(j,b,v) for k,v in head['attributes'].items()};ca={k:render.acc(j,b,v) for k,v in cap['attributes'].items()};na={k:render.acc(j,b,v) for k,v in oldneck['attributes'].items()}
 oj=np.vstack([ha['JOINTS_0'][ids],ca['JOINTS_0'][capids]]);ow=np.vstack([ha['WEIGHTS_0'][ids],ca['WEIGHTS_0'][capids]])
 influences=[]
 for joints,weights in zip(oj,ow):
  d={int(k):float(v) for k,v in zip(joints,weights) if v>0};influences.append(d)
 nj=na['JOINTS_0'][0];nw=na['WEIGHTS_0'][0];neckmix={int(k):float(v) for k,v in zip(nj,nw) if v>0}
 jointrows=[];weightrows=[]
 for t in np.linspace(0,1,5):
  for d in influences:
   mix={k:(1-t)*d.get(k,0)+t*neckmix.get(k,0) for k in set(d)|set(neckmix)};ordered=sorted(mix.items(),key=lambda x:-x[1]);assert len(ordered)<=4
   jointrows.append([k for k,v in ordered]+[0]*(4-len(ordered)));weightrows.append([v for k,v in ordered]+[0.]*(4-len(ordered)))
 vn=np.zeros_like(vp);fn=np.cross(vp[vf[:,1]]-vp[vf[:,0]],vp[vf[:,2]]-vp[vf[:,0]])
 for k in range(3):np.add.at(vn,vf[:,k],fn)
 vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-12)
 # Preserve all normal seams except vertices whose positions actually move.
 hn=ha['NORMAL'].copy();sums=np.zeros_like(pp)
 for k in range(3):np.add.at(sums,f[:,k],nn)
 hn[changed]=sums[changed]/np.maximum(np.linalg.norm(sums[changed],axis=1,keepdims=True),1e-12)
 d=copy.deepcopy(j);raw=bytearray(b);dest=d['meshes'][0]['primitives']
 dest[0]['attributes']['POSITION']=add_accessor(d,raw,pp.astype(np.float32),5126,'VEC3',34962,True)
 dest[0]['attributes']['NORMAL']=add_accessor(d,raw,hn.astype(np.float32),5126,'VEC3',34962)
 arrays={'POSITION':vp,'NORMAL':vn,'JOINTS_0':np.array(jointrows),'WEIGHTS_0':np.array(weightrows)}
 assert set(arrays)==set(oldneck['attributes']), 'Do not lose unknown attributes'
 for key,a in arrays.items():
  old=j['accessors'][oldneck['attributes'][key]];dest[2]['attributes'][key]=add_accessor(d,raw,a.astype(render.CT[old['componentType']]),old['componentType'],old['type'],34962,key=='POSITION')
 dest[2]['indices']=add_accessor(d,raw,vf.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 for key in ('nodes','skins','animations','materials','textures','images'):assert j.get(key)==d.get(key)
 assert j['meshes'][1:]==d['meshes'][1:] and cap==dest[1] and j['meshes'][0]['primitives'][3:]==dest[3:]
 assert raw[:len(b)]==b
 assert np.allclose(np.sum(arrays['WEIGHTS_0'],axis=1),1)
 # In-memory full geometry comparison before publishing a candidate.
 gg=render.gather(str(__import__('g2c4_inspect').BASE));bt=np.concatenate([g[0] for g in gg]);ct=np.concatenate([pp[f],gg[1][0],vp[vf],*[g[0] for g in gg[3:]]]);start=len(f)+len(gg[1][0]);cross,co=intersections(ct,np.r_[affected,np.arange(start,start+len(vf))]);basecross,_=intersections(bt,affected)
 report={'name':label,'baseline_sha256':SHA,'glb':str(path),'modified_face_vertices':changed.tolist(),'modified_face_count':len(affected),'affected_face_triangles':affected.tolist(),'max_jaw_displacement_m':float(np.linalg.norm(pp-p,axis=1).max()),'jaw_bounds':[p[changed].min(0).tolist(),p[changed].max(0).tolist()],'old_transition_faces_replaced':360,'new_transition_topology':topology(vp,vf),'new_transition_vertices':len(vp),'outer_face_anchor_ids':ids,'outer_cap_anchor_ids':capids.tolist(),'neck_ring':{'center':center.tolist(),'normal':axis.tolist(),'radii_m':radii.tolist(),'vertex_count':len(ring),'indices':list(range(len(vp)-len(ring),len(vp))),'open_not_capped':True},'protected_primitives_exact':True,'original_rig_materials_morphs_animations_exact':True,'proper_crossings_after':sorted(cross),'proper_crossings_jaw_before':sorted(basecross),'coplanar_aabb_candidates':len(co),'original_binary_prefix_exact':True,'inverted_original_faces':inverted.tolist(),'artistic_status':'PENDING','geometry_status':'REJECTED_CROSSINGS' if cross else 'PASS_INITIAL_FILTERS','production_approved':False}
 write_glb(path,d,raw);report['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 (OUT/f'{label}.json').write_text(json.dumps(report,indent=2)+'\n');np.savez(OUT/f'{label}_patch.npz',positions=vp,faces=vf,changed_positions=pp[f[affected]].reshape(-1,3))
 print({k:v for k,v in report.items() if k not in ('proper_crossings_after','outer_face_anchor_ids','outer_cap_anchor_ids','modified_face_vertices','affected_face_triangles')})
 print('Proper crossings',len(cross))
if __name__=='__main__':main()
