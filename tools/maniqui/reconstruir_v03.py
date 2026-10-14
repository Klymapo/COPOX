#!/usr/bin/env python3
"""Candidatos hermanos: reconstrucción paramétrica de frente y sienes, sólo desde v0.3."""
import argparse, copy, hashlib, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
import render
from reparar_v03 import add_accessor, write_glb


def boundary(theta, front, side, iteration=1):
    f=np.maximum(np.sin(theta),0)**4
    if iteration==2:
        f=np.clip((np.sin(theta)-.35)/.40,0,1); f=f*f*(3-2*f)
    return side+(front-side)*f


def build(source, target, report, iteration):
    if Path(target).exists(): raise FileExistsError(f"No sobrescribir versiones: {target}")
    assert hashlib.sha256(Path(source).read_bytes()).hexdigest()=="3c4374a0238537d838bfadc6819ed9f56da07f405401914c402ff1313b285dd8", "Se exige la base v0.3 registrada"
    j,b=render.load(source); original=copy.deepcopy(j)
    ps=j['meshes'][0]['primitives']; face,cap=ps[:2]
    assert face['extras']['pieza']=='Cabeza' and cap['extras']['pieza']=='Craneo'
    assert len(j['skins'][0]['joints'])==56 and len(j['animations'])==29
    V=render.acc(j,b,face['attributes']['POSITION']); F=render.acc(j,b,face['indices']).astype(int).reshape(-1,3)
    C=render.acc(j,b,cap['attributes']['POSITION'])[:557]
    fit=least_squares(lambda q:np.sum(((C-q[:3])/q[3:])**2,axis=1)-1,[0,.712,-.0105,.241,.2505,.2501])
    center,radii=fit.x[:3],fit.x[3:]
    front,side,sigma,blend_height=[(.765,.705,2.2,.84),(.775,.701,3.,.94),(.775,.701,3.,.94)][iteration-1]
    theta=np.arctan2(V[:,2]-center[2],V[:,0]-center[0])
    # Protected features: every triangle wholly below the contour remains byte-identical.
    h=boundary(theta,front,side,iteration)
    remove=np.all(V[F,1]>h[F],axis=1)
    feature_vertex=(V[:,2]>.155)&(np.abs(V[:,0])<.185)&(V[:,1]<.775)
    protected_features=np.any(feature_vertex[F],axis=1)
    if iteration>=2: remove &= ~protected_features
    # Every face touching the protected region is retained; shell overlaps their cut edge.
    kept=F[~remove]
    clipped_count=0
    if iteration==3:
        # Clip the remaining non-feature fragments at the bottom of the new band.
        # Original face attributes remain an untouched prefix; only crossings are appended.
        attrs={key:render.acc(j,b,idx) for key,idx in face['attributes'].items()}
        extras={key:[] for key in attrs}; crossings={}; polygons=[]
        overlap_v=.005+.024*(1-np.clip((np.sin(theta)-.35)/.40,0,1))
        cut=h-overlap_v+.003
        d=V[:,1]-cut
        ear=np.any(((np.abs(V[:,0])>.205)&(V[:,1]<.712))[F],axis=1)
        protected_features |= ear
        for fi,tri in enumerate(F):
            if protected_features[fi]:polygons.append(tri.tolist());continue
            if np.all(d[tri]<=0):polygons.append(tri.tolist());continue
            clipped_count+=1;poly=[]
            for a,z in zip(tri,np.roll(tri,-1)):
                if d[a]<=0:poly.append(int(a))
                if (d[a]<=0)!=(d[z]<=0):
                    edge=tuple(sorted((int(a),int(z))))
                    if edge not in crossings:
                        mix=float(d[a]/(d[a]-d[z]));idx=len(V)+len(crossings);crossings[edge]=idx
                        for key,values in attrs.items():extras[key].append(values[a]*(1-mix)+values[z]*mix)
                    poly.append(crossings[edge])
            for k in range(1,len(poly)-1):polygons.append([poly[0],poly[k],poly[k+1]])
        kept=np.array(polygons,dtype=np.uint32)
        for key,values in attrs.items():
            attrs[key]=np.vstack([values,np.array(extras[key])]) if extras[key] else values
        remove=~protected_features & np.all(d[F]>0,axis=1)
    NT,NR=128,32
    ang=np.linspace(-np.pi,np.pi,NT,endpoint=False)
    heights=boundary(ang,front,side,iteration)
    rr=np.hypot(V[:,0]-center[0],V[:,2]-center[2])
    sampled=[]
    for t,hh in zip(ang,heights):
        dist=np.abs(np.angle(np.exp(1j*(theta-t))))
        near=(dist<.12)&(V[:,1]>hh-.025)&(V[:,1]<hh+.008)
        vals=rr[near]
        sampled.append(np.percentile(vals,65) if len(vals)>2 else np.nan)
    sampled=np.array(sampled);valid=np.isfinite(sampled)
    assert valid.sum()>NT//2
    sampled=np.interp(np.arange(NT),np.tile(np.where(valid)[0],3)+np.repeat([-NT,0,NT],valid.sum()),np.tile(sampled[valid],3))
    sampled=gaussian_filter1d(sampled,sigma,mode='wrap')
    # Ring below the trim bridges gaps; boundary follows same anatomical contour as cut.
    overlap=np.full(NT,.006) if iteration==1 else .005+.024*(1-np.clip((np.sin(ang)-.35)/.40,0,1))
    P=[]
    for k in range(NR):
        t=k/NR
        yy=(heights-overlap)*(1-t)+(center[1]+radii[1])*t
        re=np.sqrt(np.maximum(0,1-((yy-center[1])/radii[1])**2))/np.sqrt((np.cos(ang)/radii[0])**2+(np.sin(ang)/radii[2])**2)
        rb=np.sqrt(np.maximum(0,1-((heights-overlap-center[1])/radii[1])**2))/np.sqrt((np.cos(ang)/radii[0])**2+(np.sin(ang)/radii[2])**2)
        f=np.clip((yy-(heights-overlap))/(blend_height-(heights-overlap)),0,1); f=f*f*(3-2*f)
        radius=re*(sampled/rb*(1-f)+f)
        P.extend(np.c_[center[0]+radius*np.cos(ang),yy,center[2]+radius*np.sin(ang)])
    P=np.vstack([P,center+[0,radii[1],0]])
    faces=[]
    for k in range(NR-1):
        for a in range(NT):
            x=k*NT+a;y=k*NT+(a+1)%NT;z=x+NT;w=y+NT
            faces.extend([[x,z,y],[y,z,w]])
    for a in range(NT):faces.append([(NR-1)*NT+a,NR*NT,(NR-1)*NT+(a+1)%NT])
    faces=np.array(faces,dtype=np.uint32)
    normals=np.zeros_like(P);cross=np.cross(P[faces[:,1]]-P[faces[:,0]],P[faces[:,2]]-P[faces[:,0]])
    for k in range(3):np.add.at(normals,faces[:,k],cross)
    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
    assert np.min(np.sum(normals*(P-center),axis=1))>0
    raw=bytearray(b)
    if iteration==3:
        for key,values in attrs.items():
            old=original['accessors'][face['attributes'][key]]
            if key=='NORMAL':
                tail=values[len(V):];tail/=np.maximum(np.linalg.norm(tail,axis=1,keepdims=True),1e-12)
            face['attributes'][key]=add_accessor(j,raw,values.astype(render.CT[old['componentType']]),old['componentType'],old['type'],34962,key=='POSITION')
    face['indices']=add_accessor(j,raw,kept.astype(np.uint32).ravel(),5125,'SCALAR',34963)
    joint=int(render.acc(j,b,cap['attributes']['JOINTS_0'])[0,0])
    for name,arr,ct,typ in [('POSITION',P.astype('float32'),5126,'VEC3'),('NORMAL',normals.astype('float32'),5126,'VEC3'),('JOINTS_0',np.tile([joint,0,0,0],(len(P),1)).astype('uint16'),5123,'VEC4'),('WEIGHTS_0',np.tile([1,0,0,0],(len(P),1)).astype('float32'),5126,'VEC4')]:
        cap['attributes'][name]=add_accessor(j,raw,arr,ct,typ,34962,name=='POSITION')
    cap['indices']=add_accessor(j,raw,faces.ravel(),5125,'SCALAR',34963)
    cap['extras']['reparacion']=f'v0.3 continuación candidato {iteration}; banda paramétrica'
    j['asset'].setdefault('extras',{})['copox']=f'v0.3-r{iteration} experimental; no aprobado'
    write_glb(target,j,raw)
    jj,bb=render.load(target)
    assert all(jj[k]==original[k] for k in ['nodes','skins','animations','materials'])
    assert bb[:len(b)]==b and jj['meshes'][0]['primitives'][2:]==original['meshes'][0]['primitives'][2:]
    protected=~np.any(V[F,1]>h[F],axis=1)
    result=dict(iteration=iteration,source=str(source),target=str(target),source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),sha256=hashlib.sha256(Path(target).read_bytes()).hexdigest(),bones=56,clips=29,original_binary_prefix_unchanged=True,nodes_skin_animation_materials_unchanged=True,body_unchanged=True,face_original_attribute_prefix_unchanged=True,clipped_triangles=clipped_count,protected_triangles=int(protected.sum()),kept_face_triangles=len(kept),removed_band_triangles=int(remove.sum()),new_cap_vertices=len(P),new_cap_triangles=len(faces),center=center.tolist(),radii=radii.tolist(),parameters=dict(front=front,side=side,sigma=sigma,blend_height=blend_height,overlap_min_max_m=[float(overlap.min()),float(overlap.max())]),protected_feature_triangles_removed=int((remove&protected_features).sum()),status='EXPERIMENTAL',limitation='Borde inferior solapado; no soldado topológicamente')
    Path(report).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('target');a.add_argument('report');a.add_argument('--iteration',type=int,choices=[1,2,3],required=True);args=a.parse_args();build(args.source,args.target,args.report,args.iteration)
