import sys,json;sys.path.insert(0,'.');import numpy as np
from copox.medicion import rostro_edicion as re
from copox.medicion.gltf import Modelo
ED=0.1349;YO=0.6479;y=lambda v:YO-v*ED
SRC='../med2/ADAN_V08_PROPORCIONES.glb'
PIEL='PIEL_REFERENCIAS_THEO_ALASTOR_v04'
es_cabeza=lambda V:len(V)>10000 and V[:,1].max()>0.75
H=Modelo(SRC).prims[27].pos
# radio del cráneo justo delante de la oreja, por altura
ys0=np.linspace(0.54,0.70,17);ys=[];xs=[]
for yy in ys0:
  b=H[(np.abs(H[:,1]-yy)<0.006)&(H[:,2]>0.0)&(H[:,2]<0.03)]
  if len(b): ys.append(yy);xs.append(np.abs(b[:,0]).max()-0.002)
print('craneo',[(round(a,3),round(b,3)) for a,b in zip(ys,xs)])
x_craneo=lambda Y:np.interp(Y,ys,xs)
E=re.Editor(SRC)
# 1) orejas viejas hundidas contra el cráneo
E.deformar(PIEL,re.campo_aplanar_oreja((0.548,0.686),(-0.07,0.002),x_craneo),'orejas viejas aplanadas contra el cráneo',primitiva=es_cabeza)
def peso_oreja_vieja(V):
  return re._suave((V[:,1]-0.540)/0.015)*re._suave((0.696-V[:,1])/0.015)*re._suave((V[:,2]+0.085)/0.015)*re._suave((0.017-V[:,2])/0.015)*(np.abs(V[:,0])>0.12)
re.suavizar_region(E,PIEL,peso_oreja_vieja,iteraciones=25,primitiva=es_cabeza,nombre='zona de oreja vieja suavizada')
# 2) orejas nuevas en bloque (canon: v 0.0..0.55, borde exterior u 1.5)
xc=float(np.interp(y(0.275),ys,xs))
for s in (1,-1):
  E.log.append({'nota':f'craneo x en oreja {xc:.4f}'})
  re.agregar_caja(E,'ADAN_CUERPO',PIEL,(s*(xc+0.010),y(0.275),-0.030),(0.016,0.275*ED,0.026),'Head',bisel=0.25)
# 3) nariz más cúbica
nz=H[(np.abs(H[:,0])<0.035)&(H[:,1]>0.578)&(H[:,1]<0.622)&(H[:,2]>0.148)]
c=(0.0,(nz[:,1].min()+nz[:,1].max())/2,0.150);h=(np.abs(nz[:,0]).max()+0.001,(nz[:,1].max()-nz[:,1].min())/2+0.001,0.021)
E.deformar(PIEL,re.campo_cubificar(c,h,0.75,z_min=0.148),'nariz cubificada',primitiva=es_cabeza)
# 4) anillo de labios suavizado (protege la línea de la boca)
yb=y(0.75)
def peso_labios(V):
  r=np.sqrt((V[:,0]/0.06)**2+((V[:,1]-yb)/0.028)**2);w=np.clip(1-r,0,1)**0.5*(V[:,2]>0.09)
  return np.where((np.abs(V[:,1]-yb)<0.003)&(np.abs(V[:,0])<0.03),0.0,w)
re.suavizar_region(E,PIEL,peso_labios,iteraciones=14,primitiva=es_cabeza,nombre='anillo de labios suavizado')
# 5) cejas en barra (textura nueva, misma tarjeta y morphs)
for mat in ('C7V2_brow_BAKE_L','C7V2_brow_BAKE_R'):
  E.textura(mat,re.textura_ceja_barra(),'ceja en barra '+mat[-1])
E.guardar('../med2/ADAN_V09_ESTILO.glb',nota='Adán V09: estilo ALTH en rostro (cejas barra, nariz cúbica, orejas bloque, labios lisos). SIN APROBAR.')
print([(x.get('operacion') or x.get('nota'),x.get('vertices_movidos',x.get('triangulos'))) for x in E.log])
