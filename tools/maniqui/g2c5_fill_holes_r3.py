"""R3: constrained fill of measured facial gaps, without crossing retained skin."""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parent),'/workspace/g2c5-deps']
from shapely.geometry import Polygon,MultiPoint,Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import render
from g2c5_recover_face import source_selection,append_original_faces
from g2c5_fill_holes import boundary_cycles,split_pinches
from g2c4_inspect import BASE,SHA
from g2c4_candidates import topology
from g2c4_intersections import intersections
from reparar_v03 import add_accessor,write_glb
ROOT=Path('build/g2c5');DOC=Path('docs/maniqui/g2c5')

def subdivide(polygon,maxarea=8e-6):
 tris=list(constrained_delaunay_triangles(polygon).geoms);uv=[];faces=[];lookup={}
 def point_id(q):
  k=tuple(np.round(q,12));
  if k not in lookup:lookup[k]=len(uv);uv.append(np.array(q,dtype=float))
  return lookup[k]
 for tri in tris:
  coords=np.array(tri.exterior.coords[:-1]);stack=[coords]
  while stack:
   t=stack.pop();area=abs(np.cross(t[1]-t[0],t[2]-t[0]))*.5
   if area>maxarea:
    c=t.mean(0);stack.extend([np.array([t[0],t[1],c]),np.array([t[1],t[2],c]),np.array([t[2],t[0],c])])
   else:
    ix=[point_id(q) for q in t]
    if area>1e-12:faces.append(ix)
 return np.array(uv),np.array(faces,dtype=int)

def main():
 target=ROOT/'maniqui_G2C5_R3_HUECOS_NARIZ_SIN_APROBAR.glb'
 if target.exists():raise FileExistsError(target)
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
 j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];attrs={a:render.acc(j,b,k) for a,k in pr['attributes'].items()};f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3);removed=json.loads(Path('docs/maniqui/g2c4/B2.json').read_text())['deleted_triangles'];keep=np.delete(f,removed,axis=0)
 rj,rb,rp,rf,src,_,_=source_selection(j,b,keep);excluded=[2826,3781,3782,3784];src=np.array([k for k in src if k not in excluded]);refattrs={a:render.acc(rj,rb,rp['attributes'][a]) for a in attrs};a,recovered,source_map=append_original_faces(attrs,refattrs,rf[src]);faces=np.vstack([keep,recovered]);restored_end=len(faces)
 geo=render.gather(BASE);other=np.concatenate([g[0] for g in geo[1:]])
 # Actual front-facing skin/feature union; subtraction protects the visible eyes/nose.
 tri_xyz=a['POSITION'][faces];cross3=np.cross(tri_xyz[:,1]-tri_xyz[:,0],tri_xyz[:,2]-tri_xyz[:,0]);frontmask=(cross3[:,2]>1e-12)&(tri_xyz[:,:,2].mean(1)>.14)
 frontfaces=faces[frontmask];frontpolys=[Polygon(a['POSITION'][t][:,:2]) for t in frontfaces if Polygon(a['POSITION'][t][:,:2]).area>1e-13]
 visible=unary_union(frontpolys);loop_ids,failed=boundary_cycles(a['POSITION'],faces);records=[];addedfaces=[];added_positions=[];added_weights=[];added_joints=[]
 # Surface query used for the outer boundary introduced by clipping to real retained front-facing geometry.
 face_coords=a['POSITION'][frontfaces];face2=face_coords[:,:,:2]
 def locate(q):
  direct=np.flatnonzero(np.linalg.norm(a['POSITION'][:,:2]-q,axis=1)<1e-9)
  if len(direct):
   k=int(direct[0]);return a['POSITION'][k].copy(),a['JOINTS_0'][k].copy(),a['WEIGHTS_0'][k].copy()
  options=[]
  for tid,t in enumerate(face2):
   poly=Polygon(t)
   if not poly.covers(Point(q)):continue
   m=np.column_stack((t[1]-t[0],t[2]-t[0]));uv=np.linalg.solve(m,q-t[0]);bary=np.array([1-uv.sum(),uv[0],uv[1]])
   z=float(bary@face_coords[tid,:,2]);joint=attrs['JOINTS_0'][frontfaces[tid,0]];weight=attrs['WEIGHTS_0'][frontfaces[tid,0]]
   options.append((z,joint,weight))
  if options:
   z,joint,weight=max(options,key=lambda x:x[0]);return np.r_[q,z],joint.copy(),weight.copy()
  raise ValueError('Clipped boundary point is not on an existing front triangle')
 for loopnum,ids in enumerate(loop_ids):
  p=a['POSITION'];bd=p[ids];xy=bd[:,:2];signed=sum(x[0]*y[1]-y[0]*x[1] for x,y in zip(xy,np.roll(xy,-1,axis=0)))/2
  if not (bd[:,2].min()>.14 and bd[:,1].min()>.595 and bd[:,1].max()<.77 and np.max(abs(bd[:,0]))<.17 and signed<-1e-9):continue
  if bd[:,1].min()>.66 and np.min(abs(bd[:,0]))>.04 and bd[:,2].max()<.185:
   records.append({'loop':loopnum,'status':'PROTECTED_OCULAR_CAVITY','boundary':ids});continue
  valid=Polygon(xy)
  if not valid.is_valid:valid=__import__('shapely').make_valid(valid)
  domain=valid.difference(visible)
  pieces=[x for x in (list(domain.geoms) if hasattr(domain,'geoms') else [domain]) if x.geom_type=='Polygon' and x.area>1e-8]
  if not pieces:records.append({'loop':loopnum,'status':'NO_MISSING_VISIBLE_AREA','boundary':ids});continue
  for subnum,piece in enumerate(pieces):
   if piece.area<1e-8:continue
   try:uv,tf=subdivide(piece)
   except Exception as e:records.append({'loop':loopnum,'sub':subnum,'status':'CDT_FAILURE','reason':str(e)});continue
   # Boundary values are prescribed from existing edges; interiors use a harmonic graph solve.
   exterior=np.asarray(piece.exterior.coords[:-1]);holecoords=[np.asarray(x.coords[:-1]) for x in piece.interiors]
   boundary_uv=np.vstack([exterior,*holecoords]);bd_ids=set()
   for q in boundary_uv:
    ix=int(np.argmin(np.linalg.norm(uv-q,axis=1)));bd_ids.add(ix)
   known={};failed_boundary=False
   for ix in bd_ids:
    try:known[ix]=locate(uv[ix])
    except ValueError:failed_boundary=True;break
   if failed_boundary:records.append({'loop':loopnum,'sub':subnum,'status':'BOUNDARY_NOT_ON_RETAINED_SURFACE'});continue
   # Add all triangle centroids until the surface is suitably soft, without splitting contour edges.
   # subdivide() inserts points inside every triangle; all internal graph edges are shared.
   # Weighted harmonic Z and V3's single head influence preserve skin behavior.
   ei=np.vstack([tf[:,[0,1]],tf[:,[1,2]],tf[:,[2,0]]]);ei=np.sort(ei,axis=1);ei=np.unique(ei,axis=0);n=len(uv);free=[i for i in range(n) if i not in bd_ids]
   index={k:i for i,k in enumerate(free)};rr=[];cc=[];vv=[];rhs=np.zeros(len(free))
   for ii,k in enumerate(free):
    neighbors=ei[np.any(ei==k,axis=1)];neighbors=np.unique(neighbors);degree=0.
    for m in neighbors:
     if m==k:continue
     w=1/max(float(np.sum((uv[k]-uv[m])**2)),1e-12);degree+=w
     if int(m) in known:rhs[ii]+=w*known[int(m)][0][2]
     else:rr.append(ii);cc.append(index[int(m)]);vv.append(-w)
    rr.append(ii);cc.append(ii);vv.append(degree)
   if free:zz=spsolve(coo_matrix((vv,(rr,cc)),shape=(len(free),len(free))).tocsr(),rhs)
   else:zz=[]
   coords=np.column_stack([uv,np.zeros(n)]);joints=np.zeros((n,4));weights=np.zeros((n,4))
   for ix,val in known.items():coords[ix]=val[0];joints[ix]=val[1];weights[ix]=val[2]
   for k,z in zip(free,zz):coords[k]=[uv[k,0],uv[k,1],z];joints[k]=[5,0,0,0];weights[k]=[1,0,0,0]
   # Preserve exact indexed anchors; otherwise append explicit spatial seam samples.
   local=np.empty(n,dtype=int);newp=[];newj=[];neww=[]
   for k,q in enumerate(coords):
    match=np.flatnonzero(np.linalg.norm(a['POSITION']-q,axis=1)<1e-8)
    if len(match):local[k]=int(match[0])
    else:local[k]=len(a['POSITION'])+len(newp);newp.append(q);newj.append(joints[k]);neww.append(weights[k])
   nf=local[tf];newp=np.asarray(newp,dtype=float).reshape(-1,3);newj=np.asarray(newj,dtype=np.uint16).reshape(-1,4);neww=np.asarray(neww,dtype=float).reshape(-1,4);allpositions=np.vstack([a['POSITION'],newp])
   normal=np.cross(allpositions[nf[:,1]]-allpositions[nf[:,0]],allpositions[nf[:,2]]-allpositions[nf[:,0]]);good=np.linalg.norm(normal,axis=1)>1e-12
   nf=nf[good]
   if not len(nf):continue
   triadd=np.concatenate([a['POSITION'][faces],other,allpositions[nf]])
   start=len(faces)+len(other);hit,_=intersections(triadd,range(start,len(triadd)))
   if hit:records.append({'loop':loopnum,'sub':subnum,'status':'REJECTED_CROSSINGS','count':len(hit)});continue
   # Reject any newly overfull spatial edge before it enters the master.
   candidate=np.vstack([faces,nf]);top=topology(allpositions,candidate)
   prior=topology(a['POSITION'],faces)
   if top['welded_nonmanifold_edges']>prior['welded_nonmanifold_edges']:
    records.append({'loop':loopnum,'sub':subnum,'status':'REJECTED_NONMANIFOLD','after':top['welded_nonmanifold_edges']});continue
   oldv=len(a['POSITION']);a['POSITION']=np.vstack([a['POSITION'],newp]);a['JOINTS_0']=np.vstack([a['JOINTS_0'],newj]);a['WEIGHTS_0']=np.vstack([a['WEIGHTS_0'],neww]);
   normals=np.zeros_like(a['POSITION']);faceverts=a['POSITION'][nf];nn=np.cross(faceverts[:,1]-faceverts[:,0],faceverts[:,2]-faceverts[:,0])
   for c in range(3):np.add.at(normals,nf[:,c],nn)
   normtail=normals[oldv:];normtail/=np.maximum(np.linalg.norm(normtail,axis=1,keepdims=True),1e-12);a['NORMAL']=np.vstack([a['NORMAL'],normtail]);first=len(faces);faces=np.vstack([faces,nf]);addedfaces.extend(nf.tolist());added_positions.extend(a['POSITION'][nf].reshape(-1,3).tolist());records.append({'loop':loopnum,'sub':subnum,'status':'ADDED','faces':len(nf),'vertices':len(newp),'area_m2':piece.area,'bounds':piece.bounds,'face_range':[first,len(faces)]})
 d=copy.deepcopy(j);raw=bytearray(b);dest=d['meshes'][0]['primitives'][0]
 for key,x in a.items():
  old=j['accessors'][pr['attributes'][key]];dest['attributes'][key]=add_accessor(d,raw,x.astype(render.CT[old['componentType']]),old['componentType'],old['type'],34962,key=='POSITION')
 dest['indices']=add_accessor(d,raw,faces.astype(np.uint32).reshape(-1),5125,'SCALAR',34963);write_glb(target,d,raw)
 ej,eb=render.load(target);ep=ej['meshes'][0]['primitives'][0];pv=render.acc(ej,eb,ep['attributes']['POSITION']);ef=render.acc(ej,eb,ep['indices']).astype(int).reshape(-1,3);assert eb[:len(b)]==b
 for key,x in attrs.items():assert np.array_equal(render.acc(ej,eb,ep['attributes'][key])[:len(x)],x)
 assert ej['meshes'][0]['primitives'][1:]==j['meshes'][0]['primitives'][1:] and ej['meshes'][1:]==j['meshes'][1:]
 for key in ('nodes','skins','animations','materials','images','textures','scenes'):assert ej.get(key)==j.get(key)
 w=render.acc(ej,eb,ep['attributes']['WEIGHTS_0']);assert np.isfinite(w).all() and np.all(w>=0) and np.allclose(w.sum(1),1)
 allgeo=render.gather(target);cross,cop=intersections(np.concatenate([g[0] for g in allgeo]),range(len(keep),len(ef)));after=topology(pv,ef);prior=topology(attrs['POSITION'],keep)
 report={'candidate':'R3','source':str(BASE),'source_sha256':SHA,'cleanup_B2_reapplied':removed,'reference':str(__import__('g2c4_inspect').REFERENCE),'reference_sha256':hashlib.sha256(__import__('g2c4_inspect').REFERENCE.read_bytes()).hexdigest(),'glb':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'restored_source_triangles':src.tolist(),'excluded_source_faces_due_R1_crossings':excluded,'restored_triangle_count':len(src),'interpolated_fill_triangles':len(ef)-restored_end,'added_vertices':len(pv)-len(attrs['POSITION']),'modified_original_vertices':0,'patches':records,'unresolved_boundary_fans':failed,'before_B2':prior,'after':after,'proper_crossings':sorted(cross),'coplanar_aabb_candidates':len(cop),'maximum_original_edge_overfill_change':after['welded_nonmanifold_edges']-prior['welded_nonmanifold_edges'],'original_binary_prefix_exact':True,'all_original_vertex_attributes_exact':True,'protected_morph_rig_material_nodes_exact':True,'GLTF_error43_compat_limitation_inherited':True,'production_approved':False,'geometry_status':'FAIL_CROSSINGS' if cross else ('FAIL_NONMANIFOLD' if after['welded_nonmanifold_edges']>prior['welded_nonmanifold_edges'] else 'PASS_REGIONAL_INITIAL'),'artistic_status':'PENDING_GODOT'}
 (DOC/'R3.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');np.savez(ROOT/'R3_edit.npz',triangles=pv[ef[len(keep):]])
 print('R3',report['sha256'],'original restore',len(src),'patch',len(ef)-restored_end,'vertices',report['added_vertices'],'crossings',len(cross),'nonmanifold',prior['welded_nonmanifold_edges'],'->',after['welded_nonmanifold_edges']);print({x:sum(y['status']==x for y in records) for x in {y['status'] for y in records}})
if __name__=='__main__':main()
