#!/usr/bin/env python3
"""COPOX v0.4 · ronda controlada de nuca y patillas sobre r3.
3 candidatos HERMANOS, no se sobrescribe ninguna version.
glTF Y-up, metros, cara +Z; Python/NumPy (sin servicios pagados).
El resultado es experimental: NO afirma soldadura topologica.
"""
import argparse, copy, hashlib, json
from pathlib import Path
import numpy as np
import render
from reparar_v03 import add_accessor, write_glb

EXPECTED="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
NT, NR = 128, 32
PARAMS = {
  1: dict(nape_drop=.010, side_drop=.004, nape_inset=.001, trim=False, side_trim=False),
  2: dict(nape_drop=.018, side_drop=.009, nape_inset=.003, trim=True, side_trim=False),
  3: dict(nape_drop=.018, side_drop=.012, nape_inset=.003, trim=True, side_trim=True),
}

def smooth01(x):
    x=np.clip(x,0,1); return x*x*(3-2*x)

def build(source,target,report,iteration):
    if iteration not in PARAMS: raise ValueError("Solo tres candidatos 1/2/3")
    if Path(target).exists() or Path(report).exists(): raise FileExistsError("No sobrescribir artefactos")
    raw_source=Path(source).read_bytes()
    original_sha=hashlib.sha256(raw_source).hexdigest()
    if original_sha != EXPECTED: raise RuntimeError("Fuente inesperada. Requiere r3 exacto")
    j,b=render.load(source); original=copy.deepcopy(j)
    face,cap=j['meshes'][0]['primitives'][:2]
    if face.get('extras',{}).get('pieza')!='Cabeza' or cap.get('extras',{}).get('pieza')!='Craneo':
        raise RuntimeError("Piezas faciales inesperadas")
    if len(j['skins'][0]['joints'])!=56 or len(j['animations'])!=29:
        raise RuntimeError("Rig de origen diferente a 56/29")
    metadata=json.loads(Path("docs/MANIQUI_V03_R3.json").read_text())
    center=np.asarray(metadata["center"],float); radii=np.asarray(metadata["radii"],float)
    V=render.acc(j,b,face['attributes']['POSITION'])
    F=render.acc(j,b,face['indices']).astype(int).reshape(-1,3)
    CP=render.acc(j,b,cap['attributes']['POSITION'])
    CI=render.acc(j,b,cap['indices']).astype(int).reshape(-1,3)
    if len(CP)!=4097 or len(CI)!=8064:raise RuntimeError("Cran eo no corresponde a r3")
    p=PARAMS[iteration]
    q=CP.copy()
    theta=np.arctan2(q[:,2]-center[2],q[:,0]-center[0])
    rear=smooth01((-np.sin(theta)-.10)/.72)
    # Patillas: franja lateral que no modifica el tercio frontal de la cupula.
    lateral=smooth01((np.abs(np.cos(theta))-.60)/.30)
    lateral*=smooth01((np.sin(theta)+.10)/.40)
    idx=np.arange(len(CP)); band=smooth01((8-idx//NT)/8)
    band[idx>=NT*NR]=0
    lower=p['nape_drop']*rear*band + p['side_drop']*lateral*band
    q[:,1]-=lower
    delta=p['nape_inset']*rear*band
    # Pequeño suavizado radial local en la nuca, sin desplazar la cara.
    rad=np.hypot(q[:,0]-center[0],q[:,2]-center[2])
    scalar=1-delta/np.maximum(rad,1e-6)
    q[:,0]=center[0]+(q[:,0]-center[0])*scalar
    q[:,2]=center[2]+(q[:,2]-center[2])*scalar
    # Calculamos normales para la cupula; no se tocan las facciones.
    norm=np.zeros_like(q)
    cross=np.cross(q[CI[:,1]]-q[CI[:,0]],q[CI[:,2]]-q[CI[:,0]])
    for k in range(3):np.add.at(norm,CI[:,k],cross)
    length=np.linalg.norm(norm,axis=1,keepdims=True)
    if (length<1e-10).any():raise RuntimeError("Vertice craneal sin normal")
    norm/=length
    if not np.isfinite(q).all() or not np.isfinite(norm).all():raise RuntimeError("NaN")
    # Mascara no destructiva de facciones y orejas: todos los triangulos que
    # tocaban zonas protegidas DEBEN persistir en cada candidato.
    protected_face=np.any(((V[:,2]>.155)&(np.abs(V[:,0])<.185)&(V[:,1]<.775))[F],axis=1)
    protected_ear=np.any(((np.abs(V[:,0])>.205)&(V[:,1]<.712))[F],axis=1)
    protected=protected_face|protected_ear
    removed=np.zeros(len(F),bool)
    if p['trim']:
        fv=V[F]; x=fv[:,:,0]; y=fv[:,:,1]; z=fv[:,:,2]
        # Sólo placas superiores de nuca, donde el cráneo las cubre. Los
        # segmentos de cuello, mandibula y las orejas quedan intactos.
        rear_mask=np.all((z<-.040)&(y>.700)&(y<.830)&(np.abs(x)<.205),axis=1)
        # Excluir triangulos exteriores a la envolvente craneal,
        # para no borrar por accidente una superficie que se necesite.
        e=np.sqrt((((fv-center)/radii)**2).sum(2))
        inside=np.all(e<1.07,axis=1)
        removed |= rear_mask & inside & ~protected
        if p['side_trim']:
            # Placas junto a patillas ALTO, fuera de ojos y oreja protegidos.
            side_mask=np.all((np.abs(x)>.150)&(np.abs(x)<.204)&(z>-.015)&(z<.105)&(y>.755)&(y<.835),axis=1)
            removed |= side_mask & inside & ~protected
        # Guardarrail por si una mascara se vuelve demasiado agresiva.
        if removed.sum()>320:raise RuntimeError("Mas de 320 triangulos candidatos a eliminar")
        kept=F[~removed].astype(np.uint32)
    else: kept=F.astype(np.uint32)
    raw=bytearray(b)
    face['indices']=add_accessor(j,raw,kept.reshape(-1),5125,'SCALAR',34963)
    cap['attributes']['POSITION']=add_accessor(j,raw,q.astype(np.float32),5126,'VEC3',34962,True)
    cap['attributes']['NORMAL']=add_accessor(j,raw,norm.astype(np.float32),5126,'VEC3',34962)
    cap['extras']['reparacion']=f"v0.4-nuca-patillas-i{iteration} conservador"
    j['asset'].setdefault('extras',{})['copox']=f"Maniqui v0.4-i{iteration} NO APROBADO"
    write_glb(target,j,raw)
    jj,bb=render.load(target)
    if not all(jj[k]==original[k] for k in ('nodes','skins','animations','materials')):
        raise RuntimeError("Rig/animaciones/nodos alterados")
    if bb[:len(b)]!=b or jj['meshes'][0]['primitives'][2:]!=original['meshes'][0]['primitives'][2:]:
        raise RuntimeError("Cuerpo o binarios originales alterados")
    present=set(map(tuple,kept.tolist()))
    missing_face=sum(tuple(t) not in present for t in F[protected_face])
    missing_ear=sum(tuple(t) not in present for t in F[protected_ear])
    if missing_face or missing_ear:raise RuntimeError("Facciones/orejas perdidas")
    delta_p=np.linalg.norm(q-CP,axis=1)
    result=dict(status="CANDIDATO EXPERIMENTAL NO APROBADO",iteration=iteration,
        base=source,base_sha256=original_sha,candidate=target,
        candidate_sha256=hashlib.sha256(Path(target).read_bytes()).hexdigest(),
        bones=56,clips=29,skin_and_animations_equal=True,body_equal=True,
        face_positions_originals_preserved=True,protected_face_triangles_missing=missing_face,
        protected_ear_triangles_missing=missing_ear,removed_nape_side_triangles=int(removed.sum()),
        altered_cap_vertices=int((delta_p>1e-7).sum()),
        max_cap_shift_m=float(delta_p.max()),params=p,
        limitations=["Conserva aristas abiertas del borde inferior","No afirma soldadura de la cara",
                     "Requiere cuatro vistas, poses y evaluacion de Admin"])
    Path(report).parent.mkdir(parents=True,exist_ok=True)
    Path(report).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source");parser.add_argument("target");parser.add_argument("report")
    parser.add_argument("--iteration",type=int,choices=[1,2,3],required=True)
    a=parser.parse_args();build(a.source,a.target,a.report,a.iteration)
