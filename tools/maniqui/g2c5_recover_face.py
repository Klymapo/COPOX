"""Recover audited original skin/nose faces onto exact V3 plus B2 cleanup.
No guessed anatomy, mirrored coordinates, overwrites, or rejected parents.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
from reparar_v03 import add_accessor,write_glb
from g2c4_inspect import BASE,SHA,REFERENCE
from g2c4_candidates import topology
from g2c4_intersections import intersections
OUT=Path('build/g2c5');REPORT=Path('docs/maniqui/g2c5')
def triangle_key(t):return tuple(sorted(tuple(x) for x in np.round(t,6)))

def source_selection(j,b,keep):
 """This measured asset profile only. Seven texture samples, strict skin vote."""
 rj,rb=render.load(REFERENCE);rp=rj['meshes'][0]['primitives'][13];v=render.acc(rj,rb,rp['attributes']['POSITION']);rf=render.acc(rj,rb,rp['indices']).astype(int).reshape(-1,3)
 pr=j['meshes'][0]['primitives'][0];p=render.acc(j,b,pr['attributes']['POSITION']);original=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3)
 existing={triangle_key(p[t]) for t in keep};missing=np.array([triangle_key(v[t]) not in existing for t in rf]);geom=next(x for x in render.gather(REFERENCE) if len(x[0])==len(rf));uv,tex=geom[2:4]
 bary=np.array([[1/3]*3,[.8,.1,.1],[.1,.8,.1],[.1,.1,.8],[.45,.45,.1],[.45,.1,.45],[.1,.45,.45]])
 q=np.einsum('si,fij->fsj',bary,uv);h,w=tex.shape[:2];col=tex[(np.mod(q[:,:,1],1)*(h-1)).astype(int),(np.mod(q[:,:,0],1)*(w-1)).astype(int)];lum=col.mean(2);ch=(col+.004)/(col+.004).sum(2,keepdims=True)
 tri=v[rf];region=(tri[:,:,0].max(1)<.175)&(tri[:,:,0].min(1)>-.175)&(tri[:,:,1].min(1)>.59)&(tri[:,:,1].max(1)<.78)&(tri[:,:,2].min(1)>.14)
 skin=(lum>.38)&(ch[:,:,0]>.34)&(ch[:,:,0]<.46)&(ch[:,:,2]>.22)&(col[:,:,0]>col[:,:,1])&(col[:,:,1]>col[:,:,2])
 sel=np.flatnonzero(missing&region&(skin.sum(1)>=6))
 removed=json.loads(Path('docs/maniqui/g2c4/B2.json').read_text())['deleted_triangles'];forbidden={triangle_key(p[t]) for t in original[removed]}
 assert not any(triangle_key(v[rf[i]]) in forbidden for i in sel),'Never restore confirmed glasses'
 return rj,rb,rp,rf,sel,col[sel],skin.sum(1)[sel]

def append_original_faces(attrs,refattrs,faces):
 """Reuse full attribute matches; keep normal/weight seams and source indices."""
 keys=list(attrs)
 def sig(arrays,k):return b''.join(np.asarray(arrays[a][k],dtype=np.float32).tobytes() for a in keys)
 lookup={sig(attrs,k):k for k in range(len(attrs['POSITION']))};mapping={};app={k:[] for k in keys}
 for k in np.unique(faces):
  key=sig(refattrs,k)
  if key not in lookup:
   lookup[key]=len(attrs['POSITION'])+len(app['POSITION'])
   for a in keys:app[a].append(refattrs[a][k])
  mapping[int(k)]=lookup[key]
 result={a:np.vstack([attrs[a],app[a]]) if app[a] else attrs[a].copy() for a in keys}
 newfaces=np.array([[mapping[int(k)] for k in t] for t in faces],dtype=np.uint32)
 return result,newfaces,mapping

def main():
 OUT.mkdir(exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);target=OUT/'maniqui_G2C5_R1_PIEL_NARIZ_RECUPERADAS_SIN_APROBAR.glb'
 if target.exists():raise FileExistsError(target)
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
 j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];attrs={a:render.acc(j,b,k) for a,k in pr['attributes'].items()};f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3)
 b2=json.loads(Path('docs/maniqui/g2c4/B2.json').read_text());keep=np.delete(f,b2['deleted_triangles'],axis=0)
 rj,rb,rp,rf,ids,colors,votes=source_selection(j,b,keep)
 assert [j['nodes'][k].get('name') for k in j['skins'][0]['joints']]==[rj['nodes'][k].get('name') for k in rj['skins'][0]['joints']]
 assert np.array_equal(render.acc(j,b,j['skins'][0]['inverseBindMatrices']),render.acc(rj,rb,rj['skins'][0]['inverseBindMatrices']))
 refattrs={a:render.acc(rj,rb,rp['attributes'][a]) for a in attrs};newattrs,newfaces,mapping=append_original_faces(attrs,refattrs,rf[ids]);allfaces=np.vstack([keep,newfaces])
 d=copy.deepcopy(j);raw=bytearray(b);dest=d['meshes'][0]['primitives'][0]
 for a,array in newattrs.items():
  old=j['accessors'][pr['attributes'][a]];dest['attributes'][a]=add_accessor(d,raw,array.astype(render.CT[old['componentType']]),old['componentType'],old['type'],34962,a=='POSITION')
 dest['indices']=add_accessor(d,raw,allfaces.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
 write_glb(target,d,raw)
 # Audit readback, including sources and attributes, before expensive rendering.
 dj,db=render.load(target);ap=dj['meshes'][0]['primitives'][0];exported=render.acc(dj,db,ap['attributes']['POSITION']);ef=render.acc(dj,db,ap['indices']).astype(int).reshape(-1,3)
 assert db[:len(b)]==b and np.array_equal(ef,allfaces)
 for a,original in attrs.items():assert np.array_equal(render.acc(dj,db,ap['attributes'][a])[:len(original)],original)
 assert dj['meshes'][0]['primitives'][1:]==j['meshes'][0]['primitives'][1:]
 assert dj['meshes'][1:]==j['meshes'][1:]
 for k in ('nodes','skins','animations','materials','images','textures','scenes'):assert dj.get(k)==j.get(k)
 w=render.acc(dj,db,ap['attributes']['WEIGHTS_0']);joint=render.acc(dj,db,ap['attributes']['JOINTS_0']);assert np.allclose(w.sum(1),1) and np.all(w>=0) and np.all((joint>=0)&(joint<56))
 geo=render.gather(target);tri=np.concatenate([g[0] for g in geo]);cross,cop=intersections(tri,range(len(keep),len(ef)))
 before=topology(attrs['POSITION'],keep);after=topology(exported,ef)
 report={'candidate':'R1','source':str(BASE),'source_sha256':SHA,'cleanup_B2_reapplied':b2['deleted_triangles'],'reference':str(REFERENCE),'reference_sha256':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),'source_mesh':0,'source_primitive':13,'restored_source_triangles':ids.tolist(),'restored_source_vertex_mapping':mapping,'skin_texture_votes':votes.tolist(),'skin_texture_seven_samples_rgb':colors.tolist(),'glb':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'restored_triangles':len(ids),'added_vertices':len(exported)-len(attrs['POSITION']),'modified_original_vertices':0,'restored_bounds':[exported[newfaces].min((0,1)).tolist(),exported[newfaces].max((0,1)).tolist()],'before_B2':before,'after':after,'proper_crossings':sorted(cross),'coplanar_aabb_candidates':len(cop),'all_old_attributes_exact':True,'all_other_primitives_exact':True,'nodes_skin_materials_animations_morphs_exact':True,'source_bind_and_joint_order_exact':True,'forbidden_B2_glasses_faces_restored':0,'original_binary_prefix_exact':True,'production_approved':False,'geometry_status':'FAIL_CROSSINGS' if cross else 'PASS_REGIONAL_INITIAL','artistic_status':'PENDING_REAL_GODOT_CAPTURES','limitations':['Existing 15 facial clips/morph targets reference empty geometry; no expression repair claimed','Coplanar overlap and continuous animation collisions not certified','Historical lower jaw/neck opening is not capped by this face repair']}
 (REPORT/'R1.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');np.savez(OUT/'R1_edit.npz',triangles=exported[newfaces],source_triangles=ids)
 print({k:v for k,v in report.items() if k not in ('cleanup_B2_reapplied','restored_source_triangles','restored_source_vertex_mapping','skin_texture_votes','skin_texture_seven_samples_rgb','proper_crossings')});print('crossings',len(cross))
if __name__=='__main__':main()
