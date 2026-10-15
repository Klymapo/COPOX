"""Mediciones V3 y procedencia exacta; no modifica GLB."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
BASE=Path('assets/maniqui/maniqui_v0_3_r3_g2c3_v3_rapado_oreja_izquierda_SIN_APROBAR.glb')
SHA='0a100a9400e87251cbdd64328c0c13ffc4bbf829ae4c85d5b54aee2c1e67565b'
REFERENCE=Path('assets/alastor_delta/alastor_delta_v1_1_cuello.glb')
def provenance():
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
 j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];p=render.acc(j,b,pr['attributes']['POSITION']);f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3)
 rj,rb=render.load(REFERENCE);rp=rj['meshes'][0]['primitives'][13];v=render.acc(rj,rb,rp['attributes']['POSITION']);rf=render.acc(rj,rb,rp['indices']).astype(int).reshape(-1,3)
 def key(t):return tuple(sorted(tuple(x) for x in np.round(t,6)))
 lookup={key(v[t]):i for i,t in enumerate(rf)}
 mapping=np.array([lookup.get(key(p[t]),-1) for t in f]);matched=mapping>=0
 geom=next(t for t in render.gather(REFERENCE) if len(t[0])==len(rf));uv=geom[2][mapping];tex=geom[3]
 # 7 barycentric samples; center alone can cross a texture boundary.
 bary=np.array([[1/3]*3,[.8,.1,.1],[.1,.8,.1],[.1,.1,.8],[.45,.45,.1],[.45,.1,.45],[.1,.45,.45]])
 q=np.einsum('si,fij->fsj',bary,uv);h,w=tex.shape[:2];col=tex[(np.mod(q[:,:,1],1)*(h-1)).astype(int),(np.mod(q[:,:,0],1)*(w-1)).astype(int)]
 tris=render.gather(BASE)[:2];textured=(tris[0][0],geom[1],uv,tex,None)
 return j,b,p,f,mapping,col,[textured,tris[1]]
def render_pitch(tris,yaw,pitch,bounds,w=600,h=600):
 a=np.radians(pitch);r=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
 ctr=(np.array(bounds[0])+np.array(bounds[1]))/2
 t=[(((x[0]-ctr)@r.T+ctr),)+x[1:] for x in tris]
 return render.render(t,yaw,w,h,bounds)
def run():
 j,b,p,f,mp,c,t=provenance();cen=p[f].mean(1);lum=c.mean(2);ch=(c+.004)/(c+.004).sum(2,keepdims=True)
 hair=(ch[:,:,0]>.43)&(ch[:,:,2]<.24)&(lum<.56)
 am=(mp>=0)&(hair.sum(1)>=6)&(p[f,:,][...,0].min(1)>.155)&(cen[:,2]<-.025)&(cen[:,1]>.56)&(cen[:,1]<.79)
 # diagnostic only: neutral dark outside actual eyeball cores, texture based
 dark=(lum<.38)&((c.max(2)-c.min(2))<.11)
 bm=(mp>=0)&(dark.sum(1)>=5)&(cen[:,2]>.18)&(cen[:,1]>.625)&(cen[:,1]<.75)
 out=Path('build/g2c4');out.mkdir(parents=True,exist_ok=True)
 data={'A_diagnostic_faces':np.flatnonzero(am).tolist(),'B_diagnostic_faces':np.flatnonzero(bm).tolist()}
 (out/'diagnostic_selection.json').write_text(json.dumps(data,indent=2))
 for label,mask in [('A',am),('B',bm)]:
  ids=np.flatnonzero(mask);print(label,len(ids),'bounds',p[f[mask]].min((0,1)),p[f[mask]].max((0,1)))
  print('ids',ids.tolist())
  rgb=np.full((len(f),3),.65);rgb[mask]=[1,.07,.02]
  highlight=[(t[0][0],np.ones(3),None,None,rgb),t[1]]
  bounds=(np.array([-.28,.52,-.28]),np.array([.28,.98,.28])) if label=='A' else (np.array([-.18,.61,.05]),np.array([.18,.78,.30]))
  can=Image.new('RGB',(1800,1200),'white')
  for k,a in enumerate([0,270,225] if label=='A' else [0,45,315]):
   can.paste(render.render(t,a,600,600,bounds),(600*k,0));can.paste(render.render(highlight,a,600,600,bounds),(600*k,600))
  can.save(out/f'{label}_diagnostic.png')
 can=Image.new('RGB',(1800,600),'white')
 bounds=(np.array([-.26,.48,-.22]),np.array([.26,.65,.25]))
 for k,(yaw,pitch) in enumerate([(0,-75),(90,0),(270,0)]):can.paste(render_pitch(t,yaw,pitch,bounds),(600*k,0))
 can.save(out/'jaw_diagnostic.png')
if __name__=='__main__':run()
