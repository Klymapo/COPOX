import numpy as np,hashlib,json
from pathlib import Path
import build_g2c5 as b
from glbutils import GLB
from preview import sheet
r=Path('/mnt/data/g2c5_lab');dst=Path('/mnt/data/COPOX_G2C5_REGIONALES_CONSERVADOR_SIN_APROBAR.glb')
g,a,b2,c=b.read_inputs();_,F,_=g.prim(0);_,_,Catt=c.prim(0)
d=np.load(r/'face_selection.npz');ra=d['remove_A'];rb=d['remove_B']
p,restored,inner,stats=b.region_patch(Catt['POSITION'],F,ra)
faces=np.vstack([np.delete(F,np.union1d(ra,rb),axis=0),restored]);norm=Catt['NORMAL'].copy()
tr=p[restored];cross=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);summ=np.zeros_like(p)
for k in range(3):np.add.at(summ,restored[:,k],cross)
for k in inner:
 n=summ[k];N=np.linalg.norm(n)
 if N>1e-9:norm[k]=n/N
b.OUT=dst
b.write_glb(g,c,p,norm,faces,np.empty((0,3),np.float32),np.empty((0,3),np.uint32),np.empty((0,3),np.float32),np.empty((0,4),Catt['JOINTS_0'].dtype),np.empty((0,4),Catt['WEIGHTS_0'].dtype))
got=GLB(dst);_,fnew,attr=got.prim(0)
assert len(fnew)==len(faces) and len(got.doc['animations'])==29 and len(got.doc['skins'][0]['joints'])==56
assert all(got.doc.get(k)==c.doc.get(k) for k in ('skins','animations','nodes','materials','scenes'))
assert got.doc['meshes'][0]['primitives'][1:]==c.doc['meshes'][0]['primitives'][1:]
assert np.array_equal(attr['POSITION'][:len(p)],p)
report={'status':'CONSERVATIVE_COMBINED_NOT_APPROVED','file':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source':'V3 + B2 eyeglasses removed + C jaw proposal + A right ear selective surface inpainting','A_removed_faces':int(len(ra)),'A_rebuilt_inpaint_faces':int(len(restored)),'A_tuft_faces_still_shaved':int(len(ra)-len(restored)),'B2_removed_goggle_faces':int(len(rb)),'C_jaw_vertex_change_included':True,'caveat':'Eye sockets and underside of chin still have original holes; not manifold or anatomically closed','rig_unchanged':True,'baseline_hashes':b.HASHES,'oreja_stats':stats,'no_merge':True}
Path('/mnt/data/COPOX_G2C5_CONSERVADOR_REPORTE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
sheet([('V3',r/'V3_BASE_INMUTABLE.glb'),('A HUECO',r/'modelos/maniqui_G2C4_A_SIN_APROBAR.glb'),('G2C5 CONSERVADOR',dst),('G2C5 RELLENO OPTICO',Path('/mnt/data/COPOX_G2C5_CANDIDATO_SIN_APROBAR.glb'))],filename='/mnt/data/COPOX_G2C5_LAMINA_FINAL_4V.png')
print(json.dumps(report,ensure_ascii=False,indent=2))
