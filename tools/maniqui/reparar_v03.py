#!/usr/bin/env python3
"""COPOX — propuesta MANIQUI v0.3. Borde frontal craneal reparado SIN borrar facciones.
Uso: python reparar_v03.py original.glb candidato.glb reporte.json
No modifica originales. Conserva skin, nodos y animaciones, y expone metrica de distancias.
"""
import hashlib, json, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render

def add_buffer_view(doc, raw, arr, target):
    while len(raw) % 4: raw.append(0)
    off=len(raw); raw.extend(arr.tobytes())
    doc['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(raw)-off,'target':target})
    return len(doc['bufferViews'])-1

def add_accessor(doc,raw,array,component,type_name,target,bounds=False):
    arr=np.ascontiguousarray(array)
    v=add_buffer_view(doc,raw,arr,target)
    d={'bufferView':v,'componentType':component,'count':int(len(arr)),'type':type_name}
    if bounds:
        d['min']=arr.min(axis=0).astype(float).tolist()
        d['max']=arr.max(axis=0).astype(float).tolist()
    doc['accessors'].append(d)
    return len(doc['accessors'])-1

def write_glb(path,j,b):
    while len(b)%4:b.append(0)
    j['buffers'][0]['byteLength']=len(b)
    txt=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    txt+=b' '*((-len(txt))%4)
    out=(struct.pack('<4sII',b'glTF',2,28+len(txt)+len(b))
        +struct.pack('<I4s',len(txt),b'JSON')+txt
        +struct.pack('<I4s',len(b),b'BIN\\x00')+bytes(b))
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_bytes(out)

def process(source,target,report):
    src=Path(source).read_bytes()
    j,b=render.load(source)
    if len(j.get('skins',[]))!=1 or len(j['skins'][0]['joints'])!=56 or len(j.get('animations',[]))!=29:
        raise RuntimeError('Baseline distinto de 56 huesos y 29 clips: no generar salida')
    mesh=j['meshes'][0]
    named={p.get('extras',{}).get('pieza'):p for p in mesh['primitives']}
    if not all(n in named for n in ('Craneo','Cabeza')):
        raise RuntimeError('No se encontraron primitivas Craneo y Cabeza')
    cap=named['Craneo']; face=named['Cabeza']
    def array(p,key): return render.acc(j,b,p['attributes'][key])
    v=array(cap,'POSITION'); n=array(cap,'NORMAL')
    joints=array(cap,'JOINTS_0').astype(np.uint16)
    weights=array(cap,'WEIGHTS_0').astype(np.float32)
    f=render.acc(j,b,cap['indices']).astype(np.uint32).ravel().reshape(-1,3)
    fv=array(face,'POSITION')
    # Determinar borde de cráneo: aristas unidas a una sola cara, con orientación.
    e=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]),axis=0)
    es=np.sort(e,axis=1)
    _, inv, counts=np.unique(es,axis=0,return_inverse=True,return_counts=True)
    border=e[counts[inv]==1]
    if len(border)<10:raise RuntimeError('No se detecto borde abierto de craneo')
    # Sólo sector frontal/temporal alto: la nuca y las orejas quedan protegidas.
    cv=v[border].mean(axis=1)
    sel=((cv[:,2]>0.040)&(cv[:,1]>0.744)
        &(np.abs(cv[:,0])<0.235))
    chosen=border[sel]
    if len(chosen)<8:raise RuntimeError('Borde frontal insuficiente para reparación segura')
    ids=np.unique(chosen)
    # Anillo nuevo sobre ceja; anclajes geométricos cercanos, sin usar bordes UV rotos.
    positions={}
    distances=[]
    accepted=0
    for vid in ids:
        p=v[vid]
        low=np.array([p[0]*0.985,p[1]-0.024,p[2]+0.006],float)
        d=fv-p
        mask=((d[:,1]<-0.004)&(d[:,1]>-0.065)&(np.abs(d[:,0])<0.070)
              &(np.abs(d[:,2])<0.080))
        if mask.any():
            candidates=fv[mask]
            dist=np.linalg.norm((candidates-low)*np.array([1,0.60,1]),axis=1)
            k=int(np.argmin(dist))
            nearest=candidates[k]
            d0=float(np.linalg.norm(nearest-low))
            if d0<0.060:
                low=low*0.48+nearest*0.52
                low[2]+=0.004
                accepted+=1
                distances.append(d0)
        positions[int(vid)]=low
    new_ids={int(vid):len(v)+i for i,vid in enumerate(ids)}
    V=np.vstack([v,np.array([positions[int(vid)] for vid in ids])])
    J=np.vstack([joints,joints[ids]]).astype(np.uint16)
    W=np.vstack([weights,weights[ids]]).astype(np.float32)
    N=np.vstack([n,n[ids]]).astype(np.float32)
    new_faces=[]
    for a,bb in chosen:
        a=int(a);bb=int(bb); c=new_ids[a];d=new_ids[bb]
        # Giro invertido con respecto a la arista de la malla original.
        new_faces.extend(([bb,a,c],[bb,c,d]))
    F=np.vstack([f,np.array(new_faces,np.uint32)])
    # Normales de los vertices nuevos, promedio por triangulo (sombreado suave).
    normals=np.zeros_like(V)
    tri=V[np.array(new_faces,dtype=int)]
    fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    for k in range(3):np.add.at(normals,np.array(new_faces,dtype=int)[:,k],fn)
    active=np.linalg.norm(normals,axis=1)>1e-10
    normals[active]/=np.linalg.norm(normals[active],axis=1)[:,None]
    N[active]=(N[active]*0.45+normals[active]*0.55)
    N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-10)
    if not np.isfinite(V).all() or not np.isfinite(N).all():
        raise RuntimeError('Vertices o normales no finitos')
    if np.max(np.abs(W.sum(axis=1)-1))>0.005 or int(J.max())>=56:
        raise RuntimeError('Influencias de skin dañadas')
    # Conservar original: agregar buffers de cráneo al final, sin tocar canales, esqueleto ni cara.
    raw=bytearray(b)
    p=cap['attributes']
    p['POSITION']=add_accessor(j,raw,V.astype(np.float32),5126,'VEC3',34962,True)
    p['NORMAL']=add_accessor(j,raw,N.astype(np.float32),5126,'VEC3',34962)
    p['JOINTS_0']=add_accessor(j,raw,J.astype(np.uint16),5123,'VEC4',34962)
    p['WEIGHTS_0']=add_accessor(j,raw,W.astype(np.float32),5126,'VEC4',34962)
    cap['indices']=add_accessor(j,raw,F.astype(np.uint32).reshape(-1),5125,'SCALAR',34963)
    cap['extras']['reparacion']='v0.3 banda craneal frontal/temporal, sin recorte de cara'
    j.setdefault('asset',{}).setdefault('extras',{})['copox']='Maniqui v0.3 experimental: no aprobado'
    write_glb(target,j,raw)
    j2,b2=render.load(target)
    if j2['animations']!=j['animations'] or j2['skins']!=j['skins'] or len(j2['skins'][0]['joints'])!=56:
        raise RuntimeError('Animaciones o jerarquia de skin cambiaron')
    a=j2['meshes'][0]['primitives']
    if len(a)!=len(mesh['primitives']):
        raise RuntimeError('Se perdieron primitivas del personaje')
    result={'base_sha256':hashlib.sha256(src).hexdigest(),
        'candidate_sha256':hashlib.sha256(Path(target).read_bytes()).hexdigest(),
        'base_path':str(source),'candidate_path':str(target),'status':'CANDIDATO - REVISION VISUAL OBLIGATORIA',
        'bones':56,'clips':29,'old_craneo_verts':int(len(v)),'new_craneo_verts':int(len(V)),
        'old_craneo_tris':int(len(f)),'new_craneo_tris':int(len(F)),
        'patched_border_edges':int(len(chosen)),'boundary_total_before':int(len(border)),
        'anchors_to_face':int(accepted),'mean_anchor_distance_m':float(np.mean(distances)) if distances else None,
        'face_untouched':True,'other_mesh_parts_untouched':True,
        'caveats':['No recorta islas faciales antiguas','Conexión a cara es visual, no soldadura topológica','Importar a Godot para evaluar normales/deformaciones']}
    Path(report).parent.mkdir(parents=True,exist_ok=True)
    Path(report).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Uso: reparar_v03.py origen.glb salida.glb validacion.json')
    process(*sys.argv[1:])
