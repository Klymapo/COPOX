"""Adán neutro: (1) boca neutral = línea con sonrisa leve, horneada en la forma base de cabeza y boca;
(2) short y guía capilar separados como capas (mallas/nodos propios, mismo esqueleto).
Uso: neutro.py entrada.glb salida.glb [sonrisa_mm=3] [abertura_mm=1.6]"""
import os,sys,json,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import glb
src,dst=sys.argv[1],sys.argv[2]
SM=float(sys.argv[3]) if len(sys.argv)>3 else 3.0
GAP=float(sys.argv[4]) if len(sys.argv)>4 else 1.6
j,b=glb.load(src); out=bytearray(b); log={}
def add(arr,typ,target=None):
    arr=np.ascontiguousarray(arr,np.float32)
    while len(out)%4: out.append(0)
    v={'buffer':0,'byteOffset':len(out),'byteLength':arr.nbytes}
    if target: v['target']=target
    out.extend(arr.tobytes()); j['bufferViews'].append(v)
    a={'bufferView':len(j['bufferViews'])-1,'componentType':5126,'count':len(arr),'type':typ}
    if typ=='VEC3': a['min']=arr.min(0).tolist(); a['max']=arr.max(0).tolist()
    j['accessors'].append(a); return len(j['accessors'])-1
body_node=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='Detective')
mesh=j['meshes'][j['nodes'][body_node]['mesh']]; P=mesh['primitives']
mat=lambda p:j['materials'][p['material']]['name']
HEAD=next(i for i,p in enumerate(P) if mat(p).startswith('PIEL') and glb.acc(j,b,p['attributes']['POSITION'])[:,1].max()>0.79 and len(glb.acc(j,b,p['attributes']['POSITION']))>10000)
MOUTH=next(i for i,p in enumerate(P) if mat(p)=='BOCA_INTERIOR_NEGRO')
# --- 1) boca
H=glb.acc(j,b,P[HEAD]['attributes']['POSITION']).astype(float); I=glb.acc(j,b,P[HEAD]['indices']).reshape(-1,3)
Mi=glb.acc(j,b,P[MOUTH]['attributes']['POSITION']).astype(float)
yc=(Mi[:,1].min()+Mi[:,1].max())/2; half_w=(Mi[:,0].max()-Mi[:,0].min())/2
from collections import Counter
e=Counter(tuple(sorted(x)) for t in I for x in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])))
bv=np.unique(np.array([k for k,v in e.items() if v==1]).ravel())
rim=bv[(H[bv,2]>0.12)&(np.abs(H[bv,0])<half_w*1.6)&(np.abs(H[bv,1]-yc)<0.02)]
a=(SM/1000)/half_w**2
def curve(x): return yc-0.0015+a*np.minimum(np.abs(x),half_w)**2
D=np.zeros_like(H)
up=H[rim,1]>=yc
tgt=curve(H[rim,0])+np.where(up,GAP/2000,-GAP/2000)
D[rim,1]=tgt-H[rim,1]
# vecinos: arrastre suave hasta 9 mm por distancia al borde
R=0.009
zone=np.where((H[:,2]>0.11)&(np.abs(H[:,0])<half_w*2.2)&(np.abs(H[:,1]-yc)<0.03))[0]
zone=np.setdiff1d(zone,rim)
d=np.linalg.norm(H[zone,None,:]-H[None,rim,:],axis=2)
k=np.argsort(d,1)[:,:4]; dk=np.take_along_axis(d,k,1)
w=1/(dk+1e-5); w/=w.sum(1,keepdims=True)
fall=np.clip(1-dk[:,0]/R,0,1)**2
D[zone,1]=(w*D[rim][k][:,:,1]).sum(1)*fall
Hn=H+D
# pieza interior: aplanar a la curva (queda como línea oscura detrás del corte)
Mn=Mi.copy(); Mn[:,1]=curve(Mi[:,0])+(Mi[:,1]-yc)*(GAP/1000)/(Mi[:,1].max()-Mi[:,1].min())
log['boca']={'vertices_borde':int(len(rim)),'vertices_zona':int((np.abs(D[zone,1])>1e-6).sum()),'desplazamiento_max_mm':round(float(np.abs(D).max())*1000,2),'sonrisa_mm':SM,'abertura_mm':GAP}
P[HEAD]['attributes']['POSITION']=add(Hn,'VEC3',34962)
# pieza interior: se agranda 25 % en X/Y alrededor de su centro (misma profundidad) para tapar las comisuras
c=(Mi.min(0)+Mi.max(0))/2; Mn=Mi.copy(); Mn[:,:2]=c[:2]+(Mi[:,:2]-c[:2])*1.25
P[MOUTH]['attributes']['POSITION']=add(Mn,'VEC3',34962)
# --- 2) capas
layers={'CAPA_SHORT':'ADAN_SHORT_AZUL','CAPA_GUIA_CAPILAR':'GUIA_CAPILAR'}
keep=[];moved={k:[] for k in layers}
for p in P:
    tag=next((k for k,v in layers.items() if mat(p).startswith(v)),None)
    if tag:
        q=dict(p); q.pop('targets',None); moved[tag].append(q)
    else: keep.append(p)
mesh['primitives']=keep; mesh['name']='ADAN_CUERPO'; j['nodes'][body_node]['name']='ADAN_CUERPO'
arm=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='Armature')
for tag,prims in moved.items():
    j['meshes'].append({'name':tag,'primitives':prims})
    j['nodes'].append({'name':tag,'mesh':len(j['meshes'])-1,'skin':0})
    j['nodes'][arm]['children'].append(len(j['nodes'])-1)
log['capas']={k:len(v) for k,v in moved.items()}
log['nota_animaciones']='clips con canales weights apuntan a ADAN_CUERPO (nodo sin cambio de índice)'
j['asset'].setdefault('extras',{})['copox_neutro']={'fecha':'2026-10-17','autor':'Elio (Claude)','estado':'DERIVADO_SIN_APROBAR',**log}
while len(out)%4: out.append(0)
j['buffers']=[{'byteLength':len(out)}]
js=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode()
while len(js)%4: js+=b' '
with open(dst,'wb') as f:
    f.write(struct.pack('<III',0x46546C67,2,28+len(js)+len(out))); f.write(struct.pack('<II',len(js),0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II',len(out),0x004E4942)); f.write(out)
print(json.dumps(log,ensure_ascii=False))
