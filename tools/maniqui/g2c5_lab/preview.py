import numpy as np, math
from numba import njit
from PIL import Image,ImageDraw
from glbutils import GLB
LO=np.array([-.295,.455,-.29]);HI=np.array([.295,1.0,.29]);CTR=(LO+HI)/2
@njit(cache=True)
def raster(p,zs,cols,H,W):
 out=np.zeros((H,W,3),dtype=np.uint8);out[:,:,:]=np.array([239,236,232],dtype=np.uint8)
 zb=np.full((H,W),-1000.,dtype=np.float64)
 for i in range(len(p)):
  if cols[i,0]==255 and cols[i,1]==0 and cols[i,2]==255:continue
  x0,y0=p[i,0];x1,y1=p[i,1];x2,y2=p[i,2]
  minx=max(0,int(math.floor(min(x0,x1,x2))));maxx=min(W-1,int(math.ceil(max(x0,x1,x2))))
  miny=max(0,int(math.floor(min(y0,y1,y2))));maxy=min(H-1,int(math.ceil(max(y0,y1,y2))))
  d=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
  if abs(d)<1e-12:continue
  for y in range(miny,maxy+1):
   for x in range(minx,maxx+1):
    w0=((y1-y2)*(x+.5-x2)+(x2-x1)*(y+.5-y2))/d
    w1=((y2-y0)*(x+.5-x2)+(x0-x2)*(y+.5-y2))/d
    w2=1.-w0-w1
    if w0>=-1e-6 and w1>=-1e-6 and w2>=-1e-6:
     z=w0*zs[i,0]+w1*zs[i,1]+w2*zs[i,2]
     if z>zb[y,x]:
      zb[y,x]=z
      out[y,x,:]=cols[i]
 return out

def mesh(glb,prim_ids=(0,1,2)):
 triangles=[];normals=[]
 for i in prim_ids:
  _,f,a=glb.prim(i); p=a['POSITION'][f]
  triangles.append(p)
 return np.vstack(triangles)

def render(triangles,angle,W=420,H=470, lo=LO,hi=HI,colors=None):
 angle=np.deg2rad(angle);ry=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
 ctr=(lo+hi)/2;ext=hi-lo;sc=.92*min(W/max(ext[0],ext[2]),H/ext[1]);p=(triangles-ctr)@ry.T
 X=p[:,:,0]*sc+W*.5;Y=-p[:,:,1]*sc+H*.5
 coords=np.stack([X,Y],axis=-1)
 nn=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-9)
 light=np.array([.35,.6,.65]);light/=np.linalg.norm(light)
 shade=.46+.54*np.abs(nn@light)
 if colors is None:co=np.stack([shade*.79,shade*.79,shade*.79],axis=1)*255
 else:co=np.clip(colors*shade[:,None],0,1)*255
 co[nn[:,2]<=0]=np.array([255,0,255])
 return Image.fromarray(raster(coords,p[:,:,2],co.astype('uint8'),H,W))

def sheet(models, views=[('FRENTE',0),('DER',270),('DER 3/4',315),('ESPALDA',180)],filename=None):
 W=420;H=450; sheet=Image.new('RGB',(W*len(views),len(models)*(H+28)),'white');d=ImageDraw.Draw(sheet)
 for row,(title,glb) in enumerate(models):
  g=glb if isinstance(glb,GLB) else GLB(glb);tris=mesh(g)
  for col,(v,a) in enumerate(views):
   frame=render(tris,a,W=W,H=H)
   sheet.paste(frame,(col*W,row*(H+28)+28))
   d.text((col*W+6,row*(H+28)+5),title+' | '+v,fill=(0,0,0))
 if filename:sheet.save(filename)
 return sheet
if __name__=='__main__':
 import sys
 a=sheet([('V3','V3_BASE_INMUTABLE.glb'),('A','modelos/maniqui_G2C4_A_SIN_APROBAR.glb'),('B2','modelos/maniqui_G2C4_B2_SIN_APROBAR.glb'),('C','modelos/maniqui_G2C4_C_SIN_APROBAR.glb')],filename='/mnt/data/g2c5_lab/_preview.png')

@njit(cache=True)
def raster_depth(P,Z,H,W):
 zb=np.full((H,W),-1000.,dtype=np.float64)
 for i in range(len(P)):
  x0,y0=P[i,0];x1,y1=P[i,1];x2,y2=P[i,2]
  xlow=max(0,int(math.floor(min(x0,x1,x2))));xhigh=min(W-1,int(math.ceil(max(x0,x1,x2))))
  ylow=max(0,int(math.floor(min(y0,y1,y2))));yhigh=min(H-1,int(math.ceil(max(y0,y1,y2))))
  d=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
  if abs(d)<1e-12:continue
  for yy in range(ylow,yhigh+1):
   for xx in range(xlow,xhigh+1):
    a=((y1-y2)*(xx+.5-x2)+(x2-x1)*(yy+.5-y2))/d
    b=((y2-y0)*(xx+.5-x2)+(x0-x2)*(yy+.5-y2))/d
    c=1-a-b
    if a>=-1e-6 and b>=-1e-6 and c>=-1e-6:
     z=a*Z[i,0]+b*Z[i,1]+c*Z[i,2]
     if z>zb[yy,xx]:zb[yy,xx]=z
 return zb

def front_depth(meshes,W=900,H=900,lo=LO,hi=HI):
 tris=np.vstack(meshes); ctr=(lo+hi)/2;ext=hi-lo;scale=.92*min(W/max(ext[0],ext[2]),H/ext[1]);p=tris-ctr
 n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);kept=n[:,2]>0;p=p[kept]
 projected=np.stack([p[:,:,0]*scale+W/2,-p[:,:,1]*scale+H/2],axis=2)
 zb=raster_depth(projected,p[:,:,2],H,W)
 return zb,lambda x,y:(np.clip(((x-ctr[0])*scale+W/2).astype('int'),0,W-1),np.clip((-(y-ctr[1])*scale+H/2).astype('int'),0,H-1))
