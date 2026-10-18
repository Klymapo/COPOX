"""Limpieza sin riesgo de Adán: quita malla Face vacía, morphs en cero (accesor sin bufferView),
materiales/texturas/imágenes/samplers sin uso. No toca geometría, UV, pesos, huesos ni morphs con efecto."""
import sys,json,struct,numpy as np
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import glb
src,dst=sys.argv[1],sys.argv[2]
j,b=glb.load(src); log={}
FACE_NODE,FACE_MESH=2,1
# 1) animaciones: quitar canales a Face; clips vacíos -> canal nulo en Root (rotación de reposo)
root=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='Root')
rr=j['nodes'][root].get('rotation',[0,0,0,1])
newacc=[]  # (type, np.array) a agregar
nulos=[]
for a in j['animations']:
    keep=[ch for ch in a['channels'] if ch['target'].get('node')!=FACE_NODE]
    if not keep:
        tmax=max(j['accessors'][a['samplers'][ch['sampler']]['input']]['max'][0] for ch in a['channels'])
        a['_null']=(tmax,); nulos.append(a['name'])
    a['channels']=keep
log['clips_con_canal_nulo']=nulos
# 2) eliminar nodo y malla Face con remapeo
def rn(i): return i-1 if i>FACE_NODE else i
j['nodes'].pop(FACE_NODE); j['meshes'].pop(FACE_MESH)
for n in j['nodes']:
    if 'children' in n: n['children']=[rn(c) for c in n['children'] if c!=FACE_NODE]
    if 'mesh' in n and n['mesh']>FACE_MESH: n['mesh']-=1
for s in j['scenes']: s['nodes']=[rn(c) for c in s['nodes']]
for s in j['skins']:
    s['joints']=[rn(c) for c in s['joints']]
    if 'skeleton' in s: s['skeleton']=rn(s['skeleton'])
for a in j['animations']:
    for ch in a['channels']: ch['target']['node']=rn(ch['target']['node'])
root=rn(root)
# 3) morphs en cero -> accesor sin bufferView (glTF lo interpreta como ceros)
cero=0
for m in j['meshes']:
    for p in m['primitives']:
        for t in p.get('targets',[]):
            for k,v in list(t.items()):
                a=j['accessors'][v]
                if 'bufferView' in a and np.abs(glb.acc(j,b,v)).max()==0:
                    na=dict(a); na.pop('bufferView',None); na.pop('byteOffset',None)
                    na['min']=[0.0]*len(na.get('min',[0,0,0])); na['max']=[0.0]*len(na.get('max',[0,0,0]))
                    j['accessors'].append(na); t[k]=len(j['accessors'])-1; cero+=1
log['accesores_morph_cero']=cero
# 4) materiales/texturas/imágenes/samplers en uso
um=sorted({p['material'] for m in j['meshes'] for p in m['primitives'] if 'material' in p})
mm={o:i for i,o in enumerate(um)}; j['materials']=[j['materials'][i] for i in um]
for m in j['meshes']:
    for p in m['primitives']:
        if 'material' in p: p['material']=mm[p['material']]
def texrefs(mat):
    out=[]
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v: out.append(v)
                else: walk(v)
        elif isinstance(o,list):
            for v in o: walk(v)
    walk(mat); return out
refs=[r for mt in j['materials'] for r in texrefs(mt)]
ut=sorted({r['index'] for r in refs}); tm={o:i for i,o in enumerate(ut)}
for r in refs: r['index']=tm[r['index']]
j['textures']=[j['textures'][i] for i in ut]
ui=sorted({t['source'] for t in j['textures']}); im={o:i for i,o in enumerate(ui)}
us=sorted({t['sampler'] for t in j['textures'] if 'sampler' in t}); sm={o:i for i,o in enumerate(us)}
for t in j['textures']:
    t['source']=im[t['source']]
    if 'sampler' in t: t['sampler']=sm[t['sampler']]
j['images']=[j['images'][i] for i in ui]; j['samplers']=[j['samplers'][i] for i in us]
log.update(materiales=len(j['materials']),texturas=len(j['textures']),imagenes=len(j['images']))
# 5) reconstruir buffer: solo bufferViews referenciados + accesores nuevos para canales nulos
out=bytearray(); views=[]; vmap={}
def addview(data,target=None):
    while len(out)%4: out.append(0)
    v={'buffer':0,'byteOffset':len(out),'byteLength':len(data)}
    if target: v['target']=target
    out.extend(data); views.append(v); return len(views)-1
def cv(i):
    if i not in vmap:
        bv=j['bufferViews'][i]; o=bv.get('byteOffset',0)
        nv=addview(b[o:o+bv['byteLength']],bv.get('target'))
        if 'byteStride' in bv: views[nv]['byteStride']=bv['byteStride']
        vmap[i]=nv
    return vmap[i]
# accesores: renumerar sólo los usados
used=set()
for m in j['meshes']:
    for p in m['primitives']:
        used|=set(p['attributes'].values())
        if 'indices' in p: used.add(p['indices'])
        for t in p.get('targets',[]): used|=set(t.values())
for s in j['skins']:
    if 'inverseBindMatrices' in s: used.add(s['inverseBindMatrices'])
for a in j['animations']:
    for ch in a['channels']:
        s=a['samplers'][ch['sampler']]; used|={s['input'],s['output']}
ua=sorted(used); am={o:i for i,o in enumerate(ua)}; acc=[]
for o in ua:
    a=dict(j['accessors'][o])
    if 'bufferView' in a: a['bufferView']=cv(a['bufferView'])
    acc.append(a)
for img in j['images']: img['bufferView']=cv(img['bufferView'])
for m in j['meshes']:
    for p in m['primitives']:
        p['attributes']={k:am[v] for k,v in p['attributes'].items()}
        if 'indices' in p: p['indices']=am[p['indices']]
        p['targets']=[{k:am[v] for k,v in t.items()} for t in p.get('targets',[])]
for s in j['skins']:
    if 'inverseBindMatrices' in s: s['inverseBindMatrices']=am[s['inverseBindMatrices']]
for a in j['animations']:
    used_s=sorted({ch['sampler'] for ch in a['channels']}); sm2={o:i for i,o in enumerate(used_s)}
    a['samplers']=[{**a['samplers'][i],'input':am[a['samplers'][i]['input']],'output':am[a['samplers'][i]['output']]} for i in used_s]
    for ch in a['channels']: ch['sampler']=sm2[ch['sampler']]
    if '_null' in a:
        tmax=a.pop('_null')[0]
        ti=np.array([0.0,tmax],np.float32); to=np.array([rr,rr],np.float32)
        acc.append({'bufferView':addview(ti.tobytes()),'componentType':5126,'count':2,'type':'SCALAR','min':[0.0],'max':[float(tmax)]}); ia=len(acc)-1
        acc.append({'bufferView':addview(to.tobytes()),'componentType':5126,'count':2,'type':'VEC4'}); oa=len(acc)-1
        a['samplers']=[{'input':ia,'output':oa,'interpolation':'LINEAR'}]
        a['channels']=[{'sampler':0,'target':{'node':root,'path':'rotation'}}]
        a.setdefault('extras',{})['copox_nota']='clip facial original apuntaba a malla Face vacía; conservado como movimiento nulo'
j['accessors']=acc; j['bufferViews']=views
while len(out)%4: out.append(0)
j['buffers']=[{'byteLength':len(out)}]
j['asset'].setdefault('extras',{})['copox_limpieza']={'fecha':'2026-10-17','autor':'Elio (Claude)','fuente_sha256':'a1936eb97586468ee5c2896879727d630a96d7f269191ea143e9169dd6f2ac14','estado':'DERIVADO_SIN_APROBAR',**log}
js=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode()
while len(js)%4: js+=b' '
tot=12+8+len(js)+8+len(out)
with open(dst,'wb') as f:
    f.write(struct.pack('<III',0x46546C67,2,tot)); f.write(struct.pack('<II',len(js),0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II',len(out),0x004E4942)); f.write(out)
print(json.dumps(log,ensure_ascii=False)); print('bytes',tot)
