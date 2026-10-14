"""G2-C4: operaciones localizadas desde V3 exacta; nunca sobrescribe un GLB.

Los selectores son un perfil medido de ESTE asset, no reglas anatómicas
universales. La operación reutilizable recibe listas auditadas de caras o
vértices; otro personaje necesita su propio perfil y una revisión nueva.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2c4_inspect import BASE,SHA,REFERENCE,provenance
import render
from reparar_v03 import add_accessor,write_glb
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from g2c3_v3_rapar_mechon_izquierdo import unique_components
OUT=Path('build/g2c4/models');REPORT=Path('docs/maniqui/g2c4')

def delete_faces(faces,ids):
 ids=np.asarray(ids,dtype=int)
 if len(ids)!=len(np.unique(ids)) or len(ids)==0 or ids.min()<0 or ids.max()>=len(faces):raise ValueError('Selección inválida')
 return np.delete(faces,ids,axis=0)

def topology(p,f):
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=inv[f]
 e=np.sort(np.vstack([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1)
 eu,co=np.unique(e,axis=0,return_counts=True)
 tri=p[f];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);areas=np.linalg.norm(cross,axis=1)*.5
 return {'faces':len(f),'used_vertices':len(np.unique(f)), 'welded_boundary_edges':int(sum(co==1)), 'welded_nonmanifold_edges':int(sum(co>2)), 'degenerate_faces':np.flatnonzero(areas<1e-12).tolist(),'min_area':float(areas.min()),'components':len(unique_components(p,f))}

def boundary_edges(p,f):
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);wf=inv[f]
 edges=np.vstack([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]);e,cnt=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
 return {tuple(x) for x in e[cnt==1]}

def profile(j,b,p,f,mp,c):
 cen=p[f].mean(1);lum=c.mean(2);ch=(c+.004)/(c+.004).sum(2,keepdims=True)
 hair=(ch[:,:,0]>.43)&(ch[:,:,2]<.24)&(lum<.56)
 A=(mp>=0)&(hair.sum(1)>=6)&(p[f][:,:,0].min(1)>.155)&(cen[:,2]<-.025)&(cen[:,1]>.56)&(cen[:,1]<.79)
 # Navy/neutral frame samples, unlike warm brown iris/lashes. Restrict to
 # lower peripheral remnants, explicitly exclude upper lids/brows/nose.
 navy=(c[:,:,2]-c[:,:,0]>-.018)&(lum<.30)&(c[:,:,0]-c[:,:,1]<.025)
 B=(mp>=0)&(navy.sum(1)>=6)&(cen[:,2]>.18)&(cen[:,1]>.62)&(cen[:,1]<.70)&(abs(cen[:,0])>.031)
 # Derive the jaw boundary from actual connectivity, not a mirrored template.
 u,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);wf=inv[f]
 e=np.vstack([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]);eu,counts=np.unique(np.sort(e,axis=1),axis=0,return_counts=True)
 edge=eu[counts==1];low=edge[(u[edge][:,:,1].max(1)<.564)&(u[edge][:,:,2].min(1)>-.005)]
 uv=np.unique(low);q=u[uv]
 # Robust quadratic height fit to measured boundary. X/Z remain exact.
 scale=np.ptp(q,axis=0);cx=np.median(q[:,0]);x=(q[:,0]-cx)/scale[0];z=(q[:,2]-q[:,2].mean())/scale[2]
 design=np.column_stack([np.ones(len(q)),x,x*x,z])
 from scipy.optimize import least_squares
 coef=least_squares(lambda v:design@v-q[:,1],np.linalg.lstsq(design,q[:,1],rcond=None)[0],loss='soft_l1',f_scale=.002).x
 target=design@coef
 # Same rounded spatial position gets same displacement on all seam copies.
 pp=p.copy();delta={int(v):float(target[k]-q[k,1]) for k,v in enumerate(uv)}
 for i in np.unique(f):
  if int(inv[i]) in delta:pp[i,1]+=delta[int(inv[i])]*.9
 moved=np.flatnonzero(np.linalg.norm(pp-p,axis=1)>1e-8)
 assert np.all(p[moved,1]<.564) and np.all(p[moved,2]>-.005)
 return np.flatnonzero(A),np.flatnonzero(B),pp,{'boundary_spatial_vertices':len(uv),'quadratic_coefficients':coef.tolist(),'design_x_center':cx,'design_x_span':scale[0],'design_z_mean':float(q[:,2].mean()),'design_z_span':scale[2],'old_fit_rms':float(np.std(q[:,1]-target)),'new_fit_rms':float(np.std((q[:,1]+.9*(target-q[:,1]))-target))}

def write_candidate(label,j,b,p,f,remove=(),updated=None,extra=None):
 path=OUT/f'maniqui_G2C4_{label}_SIN_APROBAR.glb'
 if path.exists():raise FileExistsError(path)
 d=copy.deepcopy(j);raw=bytearray(b);pr=d['meshes'][0]['primitives'][0]
 rem=np.array(remove,dtype=int);outf=delete_faces(f,rem) if len(rem) else f.copy()
 outp=p.copy() if updated is None else updated
 changed=np.flatnonzero(np.any(outp!=p,axis=1));affected=np.flatnonzero(np.any(np.isin(f,changed),axis=1))
 if len(rem):pr['indices']=add_accessor(d,raw,outf.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 normalids=[]
 if len(changed):
  pr['attributes']['POSITION']=add_accessor(d,raw,outp.astype(np.float32),5126,'VEC3',34962,True)
  oldn=render.acc(j,b,j['meshes'][0]['primitives'][0]['attributes']['NORMAL']);nn=oldn.copy()
  # Recompute only edited vertex normals, retaining normal seams and all
  # untouched face/eye/ear normals. No attribute welding or reindexing.
  tri=outp[outf];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);summ=np.zeros_like(p)
  for k in range(3):np.add.at(summ,outf[:,k],cross)
  for k in changed:
   n=summ[k];ln=np.linalg.norm(n)
   if ln>1e-12:nn[k]=n/ln;normalids.append(int(k))
  pr['attributes']['NORMAL']=add_accessor(d,raw,nn.astype(np.float32),5126,'VEC3',34962)
 pr.setdefault('extras',{})['copox_g2c4']=label+' experimental; independent V3 baseline'
 write_glb(path,d,raw);dj,db=render.load(path)
 for key in ('nodes','skins','animations','materials','textures','images','scenes'):assert dj.get(key)==j.get(key),key
 assert db[:len(b)]==b
 assert dj['meshes'][0]['primitives'][1:]==j['meshes'][0]['primitives'][1:]
 assert dj['meshes'][1:]==j['meshes'][1:]
 oldattr=j['meshes'][0]['primitives'][0]['attributes'];newattr=dj['meshes'][0]['primitives'][0]['attributes']
 for key in oldattr:
  if key not in ('POSITION','NORMAL') or not len(changed):assert oldattr[key]==newattr[key]
 actual=render.acc(dj,db,newattr['POSITION']);keep=np.ones(len(p),bool);keep[changed]=False;assert np.array_equal(p[keep],actual[keep])
 of=p[f];nf=actual[f];on=np.cross(of[:,1]-of[:,0],of[:,2]-of[:,0]);nn=np.cross(nf[:,1]-nf[:,0],nf[:,2]-nf[:,0]);inverted=np.flatnonzero(np.sum(on*nn,axis=1)<-1e-18)
 before=topology(p,f);after=topology(actual,outf)
 report={'candidate':label,'source':str(BASE),'source_sha256':SHA,'glb':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'deleted_triangles':rem.tolist(),'deleted_count':len(rem),'modified_vertices':changed.tolist(),'modified_vertex_count':len(changed),'modified_normal_vertices':normalids,'affected_retained_triangles':affected.tolist(),'before':before,'after':after,'new_degenerate_faces_count':max(0,len(after['degenerate_faces'])-len(before['degenerate_faces'])),'new_inverted_faces':inverted.tolist(),'new_boundary_edges':len(boundary_edges(p,outf)-boundary_edges(p,f)),'max_vertex_displacement_m':float(np.linalg.norm(actual-p,axis=1).max()),'original_binary_prefix_exact':True,'nodes_materials_skins_animations_exact':True,'cranium_nape_all_other_primitives_exact':True,'facial_morph_mesh_exact':True,'bones':len(j['skins'][0]['joints']),'animation_definitions':len(j['animations']),'new_intersections': 'Impossible by deletion alone: remaining triangles unchanged' if not len(changed) else 'PENDING regional pair comparison','artistic_status':'PENDING_REAL_CAPTURES','production_approved':False,'extra':extra or {}}
 assert not len(inverted), 'Local smoothing inverted triangles'
 assert report['new_degenerate_faces_count']==0
 REPORT.mkdir(parents=True,exist_ok=True);(REPORT/f'{label}.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 return report

def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 j,b,p,f,mp,c,t=provenance();a,bb,pp,fit=profile(j,b,p,f,mp,c)
 manifest={'base_sha256':SHA,'reference':str(REFERENCE),'reference_sha256':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),'exact_source_triangle_matches':int(sum(mp>=0)),'rounding_m':1e-6,'A':{'mesh':0,'primitive':0,'connectivity_island':0,'deleted_faces':a.tolist(),'source_faces':mp[a].tolist(),'bounds_min':p[f[a]].min((0,1)).tolist(),'bounds_max':p[f[a]].max((0,1)).tolist()},'B':{'mesh':0,'primitive':0,'deleted_faces':bb.tolist(),'source_faces':mp[bb].tolist(),'bounds_min':p[f[bb]].min((0,1)).tolist(),'bounds_max':p[f[bb]].max((0,1)).tolist()},'C_fit':fit}
 (REPORT/'selecciones_v3.json').write_text(json.dumps(manifest,indent=2)+'\n')
 for label,kwargs in [('A',{'remove':a}),('B',{'remove':bb}),('C',{'updated':pp,'extra':fit})]:
  r=write_candidate(label,j,b,p,f,**kwargs);print(label,r['deleted_count'],r['modified_vertex_count'],r['before'],r['after'])
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
if __name__=='__main__':main()
