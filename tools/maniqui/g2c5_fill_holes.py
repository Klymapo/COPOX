"""R2: exact source recovery plus measured front-face boundary patches."""
from pathlib import Path
import sys,json,hashlib,copy,collections
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parent),'/workspace/g2c5-deps']
from shapely.geometry import Polygon
import render
from g2c5_recover_face import source_selection,append_original_faces,triangle_key
from g2c4_inspect import BASE,SHA
from g2c4_surface_patch import triangulate_harmonic
from g2c4_candidates import topology
from g2c4_intersections import intersections
from reparar_v03 import add_accessor,write_glb
ROOT=Path('build/g2c5');DOC=Path('docs/maniqui/g2c5')

def split_pinches(loop):
 for i,k in enumerate(loop):
  if k in loop[:i]:
   a=loop.index(k);return split_pinches(loop[a:i])+split_pinches(loop[:a]+loop[i:])
 return [loop] if len(loop)>2 else []

def boundary_cycles(p,f):
 """Traverse the adjacent triangle fan at pinches; no invented connections."""
 u,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=inv[f];E={}
 for i,t in enumerate(ff):
  for k in range(3):E.setdefault(tuple(sorted((int(t[k]),int(t[(k+1)%3])))),[]).append((i,k))
 boundary={(fi,k) for entries in E.values() if len(entries)==1 for fi,k in entries};seen=set();loops=[];fail=[]
 for first in sorted(boundary):
  if first in seen:continue
  cur=first;loop=[]
  for count in range(3000):
   if cur in seen:break
   seen.add(cur);fi,k=cur;loop.append(int(ff[fi,k]));nk=(k+1)%3;nfi=fi
   for turn in range(1000):
    a,bb=int(ff[nfi,nk]),int(ff[nfi,(nk+1)%3]);es=E[tuple(sorted((a,bb)))]
    if len(es)==1:break
    if len(es)!=2:raise ValueError('Nonmanifold fan: cannot infer a hole')
    nf,ne=next(x for x in es if x[0]!=nfi)
    if ff[nf,ne]!=bb:raise ValueError('Inconsistent face winding')
    nfi,nk=nf,(ne+1)%3
   else:raise ValueError('Fan traversal bound')
   cur=(nfi,nk)
   if cur==first:break
  if cur==first:loops.extend(split_pinches(loop))
  else:fail.append(loop)
 # Choose an actually used vertex index for each spatial seam.
 used=np.unique(f);representative={int(inv[k]):int(k) for k in used}
 return [[representative[k] for k in loop] for loop in loops],fail

def main():
 target=ROOT/'maniqui_G2C5_R2_HUECOS_NARIZ_SIN_APROBAR.glb'
 if target.exists():raise FileExistsError(target)
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
 j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];attrs={a:render.acc(j,b,v) for a,v in pr['attributes'].items()};f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3);remove=json.loads(Path('docs/maniqui/g2c4/B2.json').read_text())['deleted_triangles'];keep=np.delete(f,remove,axis=0)
 rj,rb,rp,rf,source,_,_=source_selection(j,b,keep);excluded=[2826,3781,3782,3784];source=np.array([k for k in source if k not in excluded]);refattrs={a:render.acc(rj,rb,rp['attributes'][a]) for a in attrs}
 assert np.array_equal(render.acc(j,b,j['skins'][0]['inverseBindMatrices']),render.acc(rj,rb,rj['skins'][0]['inverseBindMatrices']))
 a,restored,mapping=append_original_faces(attrs,refattrs,rf[source]);faces=np.vstack([keep,restored]);restored_end=len(faces);loops,failed=boundary_cycles(a['POSITION'],faces)
 basegeo=render.gather(BASE);other=np.concatenate([g[0] for g in basegeo[1:]]);log=[]
 for num,ids in enumerate(loops):
  p=a['POSITION'];boundary=p[ids];xy=boundary[:,:2];signed=sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(xy,np.roll(xy,-1,axis=0)))/2
  # V3 facial zone, excluding eyes' deeper internal surface.
  if not (boundary[:,2].min()>.14 and boundary[:,1].min()>.595 and boundary[:,1].max()<.77 and np.max(abs(boundary[:,0]))<.17 and signed<-1e-9):continue
  ocular=boundary[:,1].min()>.66 and np.min(abs(boundary[:,0]))>.04 and boundary[:,2].max()<.185
  if ocular:log.append({'loop':num,'ids':ids,'status':'PROTECTED_OCULAR_CAVITY'});continue
  poly=Polygon(xy)
  if not poly.is_valid:log.append({'loop':num,'ids':ids,'status':'REJECTED_SELF_CROSSING_XY'});continue
  if not np.all(a['JOINTS_0'][ids]==a['JOINTS_0'][ids[0]]) or not np.all(a['WEIGHTS_0'][ids]==a['WEIGHTS_0'][ids[0]]):
   log.append({'loop':num,'ids':ids,'status':'REJECTED_NONUNIFORM_BOUNDARY_WEIGHTS'});continue
  try:s,t=triangulate_harmonic(boundary[:,[2,0,1]],.004);s=s[:,[1,2,0]]
  except (ValueError,AssertionError) as ex:log.append({'loop':num,'ids':ids,'status':'REJECTED_CHART','reason':str(ex)});continue
  n=len(boundary);tmap=np.r_[ids,np.arange(len(p),len(p)+len(s)-n)];newf=tmap[t];positions=np.vstack([p,s[n:]]);alltri=np.concatenate([positions[faces],other,positions[newf]]);start=len(faces)+len(other)
  cross,co=intersections(alltri,range(start,len(alltri)))
  if cross:log.append({'loop':num,'ids':ids,'status':'REJECTED_CROSSINGS','count':len(cross)});continue
  normals=np.zeros_like(s);tn=np.cross(s[t[:,1]]-s[t[:,0]],s[t[:,2]]-s[t[:,0]])
  for k in range(3):np.add.at(normals,t[:,k],tn)
  normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
  count=len(s)-n;a['POSITION']=positions;a['NORMAL']=np.vstack([a['NORMAL'],normals[n:]]);a['JOINTS_0']=np.vstack([a['JOINTS_0'],np.tile(a['JOINTS_0'][ids[0]],(count,1))]);a['WEIGHTS_0']=np.vstack([a['WEIGHTS_0'],np.tile(a['WEIGHTS_0'][ids[0]],(count,1))])
  oldlen=len(faces);faces=np.vstack([faces,newf]);log.append({'loop':num,'ids':ids,'status':'ADDED','added_faces':len(newf),'added_vertices':count,'face_range':[oldlen,len(faces)],'area_xy_m2':abs(signed),'bounds':[s.min(0).tolist(),s.max(0).tolist()]})
 d=copy.deepcopy(j);raw=bytearray(b);dest=d['meshes'][0]['primitives'][0]
 for key,arr in a.items():
  old=j['accessors'][pr['attributes'][key]];dest['attributes'][key]=add_accessor(d,raw,arr.astype(render.CT[old['componentType']]),old['componentType'],old['type'],34962,key=='POSITION')
 dest['indices']=add_accessor(d,raw,faces.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 write_glb(target,d,raw);ej,eb=render.load(target);ep=ej['meshes'][0]['primitives'][0];pv=render.acc(ej,eb,ep['attributes']['POSITION']);ef=render.acc(ej,eb,ep['indices']).astype(int).reshape(-1,3)
 assert eb[:len(b)]==b
 for key,original in attrs.items():assert np.array_equal(render.acc(ej,eb,ep['attributes'][key])[:len(original)],original)
 assert ej['meshes'][0]['primitives'][1:]==j['meshes'][0]['primitives'][1:] and ej['meshes'][1:]==j['meshes'][1:]
 for key in ('nodes','skins','animations','materials','images','textures','scenes'):assert ej.get(key)==j.get(key)
 w=render.acc(ej,eb,ep['attributes']['WEIGHTS_0']);assert np.isfinite(w).all() and np.all(w>=0) and np.allclose(w.sum(1),1)
 geo=render.gather(target);cross,co=intersections(np.concatenate([g[0] for g in geo]),range(len(keep),len(ef)))
 after=topology(pv,ef);assert not after['degenerate_faces']
 report={'candidate':'R2','glb':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source':str(BASE),'source_sha256':SHA,'cleanup_B2_reapplied':remove,'restored_source_triangles':source.tolist(),'excluded_source_faces_due_to_R1_crossings':excluded,'restored_triangles':len(source),'interpolated_patch_triangles':len(ef)-restored_end,'modified_original_vertices':0,'added_vertices':len(pv)-len(attrs['POSITION']),'patches':log,'boundary_fan_failures':failed,'before_B2':topology(attrs['POSITION'],keep),'after':after,'proper_crossings':sorted(cross),'coplanar_aabb_candidates':len(co),'all_old_attributes_exact':True,'all_other_primitives_exact':True,'original_binary_prefix_exact':True,'nodes_skin_materials_animations_morphs_exact':True,'geometry_status':'FAIL_NONMANIFOLD' if after['welded_nonmanifold_edges']>1 else ('FAIL_CROSSINGS' if cross else 'PASS_REGIONAL_INITIAL'),'artistic_status':'PENDING_GODOT','production_approved':False}
 (DOC/'R2.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');np.savez(ROOT/'R2_edit.npz',triangles=pv[ef[len(keep):]])
 print('R2',report['sha256'],'restored',len(source),'patchfaces',len(ef)-restored_end,'addedverts',report['added_vertices'],'crossings',len(cross),'topology',after);print(collections.Counter(x['status'] for x in log))
if __name__=='__main__':main()
