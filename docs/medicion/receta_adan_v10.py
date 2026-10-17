import sys;sys.path.insert(0,'.');import numpy as np
from copox.medicion import rostro_edicion as re
from copox.medicion.gltf import Modelo
ED=0.1349;YO=0.6479;y=lambda v:YO-v*ED
SRC='../med2/ADAN_V09_ESTILO.glb';PIEL='PIEL_REFERENCIAS_THEO_ALASTOR_v04'
es_cabeza=lambda V:len(V)>10000 and V[:,1].max()>0.75
H=Modelo(SRC).prims[27].pos
# perfil frontal de referencia: z de la columna x≈0.04 (sin nariz) por altura
vs=np.linspace(0.3,1.1,17);zc=[]
for v in vs:
  b=H[(np.abs(H[:,1]-y(v))<0.003)&(np.abs(np.abs(H[:,0])-0.04)<0.005)];zc.append(b[:,2].max() if len(b) else np.nan)
vs=vs[~np.isnan(zc)];zc=np.array(zc)[~np.isnan(zc)]
def campo_aplanar(V):
  v=(YO-V[:,1])/ED
  zt=np.interp(v,vs,zc)-0.004*(np.abs(V[:,0])/0.10)**2          # plano frontal con curvatura mínima
  wx=re._suave((0.135-np.abs(V[:,0]))/0.035)                       # se desvanece hacia la esquina de la mandíbula
  wv=re._suave((v-0.30)/0.28)*re._suave((1.15-v)/0.22)              # solo bajo los ojos y sobre el borde de la barbilla
  wz=(V[:,2]>0.05)&(V[:,2]<zt)                                     # solo adelantar (nunca hundir boca/nariz)
  w=wx*wv*wz
  V1=V.copy();V1[:,2]=V[:,2]+w*(zt-V[:,2])
  J=np.tile(np.eye(3),(len(V),1,1));J[:,2,2]=1-w
  return V1,J
E=re.Editor(SRC)
E.deformar(PIEL,campo_aplanar,'mitad inferior de la cara aplanada (estilo bloque)',primitiva=es_cabeza)
def peso_orillas(V):
  v=(YO-V[:,1])/ED
  banda=np.clip(1-np.abs(v-0.45)/0.18,0,1)+np.clip(1-np.abs(v-1.02)/0.15,0,1)
  return np.clip(banda,0,1)*(V[:,2]>0.06)*(np.abs(V[:,0])<0.15)*~((np.abs(V[:,0])<0.04)&(V[:,2]>0.145))
re.suavizar_region(E,PIEL,peso_orillas,iteraciones=12,primitiva=es_cabeza,nombre='orillas del aplanado suavizadas (protege nariz)')
E.guardar('../med2/ADAN_V10_ESTILO.glb',nota='Adán V10: V09 + cara inferior aplanada (estilo ALTH). SIN APROBAR.')
print([(x['operacion'],x.get('vertices_movidos')) for x in E.log])
