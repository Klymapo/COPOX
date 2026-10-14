#!/usr/bin/env python3
"""Capturas reales CPU y auditoría de los 29 clips. No evalúa colisiones ni Godot."""
import argparse, copy, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import render

VIEWS=[('Frente',0),('3/4',45),('Perfil',90),('Espalda',180)]

def posed(path,clip,t):
    j,b=render.load(path); nodes=copy.deepcopy(j['nodes'])
    anim=next(a for a in j['animations'] if a['name']==clip)
    for c in anim['channels']:
        s=anim['samplers'][c['sampler']]; T=render.acc(j,b,s['input']).ravel(); vals=render.acc(j,b,s['output'])
        assert s.get('interpolation','LINEAR')=='LINEAR'
        k=int(np.clip(np.searchsorted(T,t)-1,0,max(0,len(T)-2)))
        if len(T)==1:v=vals[0]
        else:
            f=np.clip((t-T[k])/max(T[k+1]-T[k],1e-12),0,1); a,z=vals[k].copy(),vals[k+1].copy()
            if c['target']['path']=='rotation':
                dot=np.dot(a,z)
                if dot<0:z=-z;dot=-dot
                if dot>.9995:v=a*(1-f)+z*f
                else:
                    angle=np.arccos(np.clip(dot,-1,1));v=(np.sin((1-f)*angle)*a+np.sin(f*angle)*z)/np.sin(angle)
                v/=np.linalg.norm(v)
            else:v=a*(1-f)+z*f
        nodes[c['target']['node']][c['target']['path']]=v.tolist()
    world={}
    def walk(i,parent):
        world[i]=parent@render.node_mat(nodes[i])
        for child in nodes[i].get('children',[]):walk(child,world[i])
    for root in j['scenes'][j.get('scene',0)]['nodes']:walk(root,np.eye(4))
    sk=j['skins'][0];ib=render.acc(j,b,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    mats=np.array([world[n]@ib[k] for k,n in enumerate(sk['joints'])]);tris=[];points=[]
    for p in j['meshes'][0]['primitives']:
        A=p['attributes'];v=render.acc(j,b,A['POSITION']);ji=render.acc(j,b,A['JOINTS_0']).astype(int);w=render.acc(j,b,A['WEIGHTS_0'])
        assert ji.max()<56 and np.max(np.abs(w.sum(1)-1))<1e-5
        v4=np.c_[v,np.ones(len(v))];q=sum(w[:,k,None]*np.einsum('nij,nj->ni',mats[ji[:,k]],v4)[:,:3] for k in range(4))
        assert np.isfinite(q).all();points.append(q)
        f=render.acc(j,b,p['indices']).astype(int).reshape(-1,3);color=render.srgb(np.array(j['materials'][p['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]))
        tris.append((q[f],color,None,None,None))
    return tris,points


def sheet(tris,bounds,views,w,h,title,out):
    img=Image.new('RGB',(w*len(views),h+36),'#eeeae4');d=ImageDraw.Draw(img)
    for i,(label,yaw) in enumerate(views):
        img.paste(render.render(tris,yaw,W=w,H=h,bounds=bounds),(i*w,36));d.text((i*w+12,10),f'{title} | {label}',fill='black')
    img.save(out)
    return img


def evaluate(base,candidate,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    bt=render.gather(base);ct=render.gather(candidate)
    bverts=np.concatenate([t[0].reshape(-1,3) for t in bt]);bounds=(bverts.min(0),bverts.max(0))
    head_bounds=(np.array([-.28,.52,-.28]),np.array([.28,.985,.28]))
    for name,tris in [('base',bt),('candidato',ct)]:
        sheet(tris,bounds,VIEWS,420,640,name,out/f'{name}_4v.png')
        sheet(tris[:2],head_bounds,VIEWS,560,560,name,out/f'{name}_detalle.png')
    ious=[]
    bg=np.array([237,234,229])
    for label,yaw in VIEWS:
        a=np.array(render.render(bt,yaw,W=420,H=640,bounds=bounds));c=np.array(render.render(ct,yaw,W=420,H=640,bounds=bounds))
        ma=np.any(a!=bg,axis=2);mc=np.any(c!=bg,axis=2)
        ious.append({'view':label,'iou':float((ma&mc).sum()/(ma|mc).sum())})
    clips=[];j,b=render.load(base)
    for a in j['animations']:
        end=float(max(render.acc(j,b,s['input']).max() for s in a['samplers']))
        for t in (0,end*.5,end):
            _,bp=posed(base,a['name'],t);_,cp=posed(candidate,a['name'],t)
            assert all(np.array_equal(x,y) for x,y in zip(bp[2:],cp[2:])),(a['name'],t,'body differs')
            assert np.array_equal(bp[0],cp[0][:len(bp[0])]),(a['name'],t,'face positions differ')
        clips.append({'clip':a['name'],'times':[0,end*.5,end],'finite':True,'body_and_face_vertices_identical':True})
    for clip,t in [('Wave',.6),('Sit-pose',.033333335),('HeadShake',.7),('Nod',.55)]:
        pt,points=posed(candidate,clip,t);bp,_=posed(base,clip,t)
        vv=np.concatenate([q[0].reshape(-1,3) for q in bp]);pb=(vv.min(0),vv.max(0))
        sheet(pt,pb,VIEWS,360,520,f'{clip} t={t:.3f}',out/f'pose_{clip}.png')
        if clip in ('HeadShake','Nod'):
            vv=np.concatenate(points[:2]);hb=(vv.min(0)-.015,vv.max(0)+.015)
            sheet(pt[:2],hb,VIEWS,420,460,f'{clip} t={t:.3f}',out/f'detalle_{clip}.png')
    result={'candidate':candidate,'baseline':base,'silhouette':ious,'all_views_iou_at_least_95':all(v['iou']>=.95 for v in ious),'clips_sampled':clips,'samples_total':len(clips)*3,'renderer':'render.py CPU numpy z-buffer; real GLB triangles; flat shading','pose_interpolation':'LINEAR translation/scale and quaternion SLERP','not_verified':['Godot','collision/self-intersection','all continuous animation frames','artistic approval']}
    (out/'evaluacion.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))}
    (out/'capturas_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='clips_sampled'},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('candidate');p.add_argument('out');a=p.parse_args();evaluate(a.base,a.candidate,a.out)
