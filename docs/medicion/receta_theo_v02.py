import sys,json;sys.path.insert(0,'.');import numpy as np
from copox.medicion import rostro_edicion as re
ED=0.1349;YO=0.6479
y=lambda v:YO-v*ED
E=re.Editor('../med2/ADAN_V09_ESTILO.glb')
PIEL='PIEL_REFERENCIAS_THEO_ALASTOR_v04';BOCA='BOCA_INTERIOR_NEGRO'
es_cabeza=lambda V:len(V)>10000 and V[:,1].max()>0.75
k=(0.94-0.3)/(1.05-0.3)
E.deformar(PIEL,re.campo_compresion_mandibula(y(0.3),k,-0.04,0.16),'mandibula: barbilla 1.05 -> 0.94 ED',primitiva=es_cabeza)
E.deformar(BOCA,re.campo_compresion_mandibula(y(0.3),k,-0.04,0.16),'mandibula (boca interior)')
v_boca=0.3+(0.75-0.3)*k;dyb=(v_boca-0.61)*ED
E.deformar(PIEL,re.campo_boca((0,y(v_boca)),0.075,0.022,1.8,dyb,0.10),'boca: v 0.75 -> 0.61 ED, ancho x1.8',primitiva=es_cabeza)
E.deformar(BOCA,re.campo_rigido(1.8,1.0,(0,y(v_boca),0),(0,dyb,0)),'boca interior')
E.deformar(BOCA,re.campo_rigido(1.4,1.5,(0,y(0.61),0.12),(0,0.0005,-0.009)),'boca interior: x1.4 ancho, x1.5 alto, 9 mm hacia adentro')
yb=y(0.61)
def campo_cerrar(V):
  r=np.sqrt((V[:,0]/0.05)**2);w=np.clip(1-r,0,1)**0.5*np.clip(1-np.abs(V[:,1]-yb)/0.008,0,1)*(V[:,2]>0.09)
  V1=V.copy();V1[:,1]=V[:,1]+(yb-V[:,1])*0.55*w
  J=np.tile(np.eye(3),(len(V),1,1));J[:,1,1]=1-0.55*w
  return V1,J
E.deformar(PIEL,campo_cerrar,'labios cerrados a línea fina (abertura x0.45)',primitiva=es_cabeza)
def peso_labios(V):
  r=np.sqrt((V[:,0]/0.07)**2+((V[:,1]-yb)/0.03)**2);w=np.clip(1-r,0,1)**0.5*(V[:,2]>0.09)
  linea=np.abs(V[:,1]-yb)<0.0035
  return np.where(linea&(np.abs(V[:,0])<0.04),0.0,w)
re.suavizar_region(E,PIEL,peso_labios,iteraciones=10,primitiva=es_cabeza,nombre='suavizado labios (protege la línea de la boca)')
def peso_barbilla(V):
  return np.clip(1-np.abs(V[:,1]-0.50)/0.025,0,1)*np.clip((V[:,2]+0.02)/0.06,0,1)
re.suavizar_region(E,PIEL,peso_barbilla,iteraciones=10,primitiva=es_cabeza,nombre='suavizado bajo la barbilla')
for lado,mat in (('L','C7V2_brow_BAKE_L'),('R','C7V2_brow_BAKE_R')):
  E.deformar(mat,re.campo_rigido(1.0,1.0,(0,y(-0.36),0),(0,0.04*ED,0)),'ceja '+lado+': +0.04 ED (la barra ya trae el grosor)')
for mat in ('C7V2_eye_BAKE_L','C7V2_eye_BAKE_R'):
  E.textura(mat,re.iris_ancho(1.6),'iris x1.6 '+mat[-1])
E.guardar('../med2/THEO_V02_ROSTRO.glb',nota='Theo V02: derivado de Adán V09 hacia el canon de rostro neutro de Theo. SIN APROBAR.')
print([ (x['operacion'],x.get('vertices_movidos')) for x in E.log])
