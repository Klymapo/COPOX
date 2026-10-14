#!/usr/bin/env python3
"""COPOX G2-C3 | Continuar la calva REAL y rapar restos posteriores / patillas.

Candidato NO aprobado: nunca toca r3, ni fusiona. Recorta exclusivamente
triangulos de Cara enteramente clasificados como pelo posterior/patilla;
se preservan todos los vertices/morphs originales. La superficie visible
que baja es una prolongacion del BORDE ORIGINAL de la primitiva Craneo.
"""
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from copox.geometry.kernel import boundary_loops, GeometryError

sys.path.insert(0, str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor, write_glb

SRC=Path("assets/maniqui/maniqui_v0_3_r3.glb")
SRC_SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/g2c3/visible")
CAMERAS=(("FRENTE",0),("PERFIL IZQ",90),("NUCA",180),("NUCA 3/4",225),
         ("PERFIL DER",270),("NUCA 3/4 DER",135))
BOUNDS=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
PROFILES={
 "conservador":{"z_cut":-.098,"sideburn_z":-.025,"drop":.158,"bulk":1.085},
 "completo":{"z_cut":-.075,"sideburn_z":.012,"drop":.188,"bulk":1.115},
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def boundary_arc(positions, faces):
    """El borde inferior del casquete suave; NO la cara rota situada debajo."""
    loops=boundary_loops(faces)
    if len(loops)!=1:
        raise GeometryError("El craneo no contiene un unico borde inferior")
    rim=np.asarray(loops[0],dtype=np.int64)
    p=positions[rim]
    # Back half of the bald dome (facing negative Z). Exclude ear zone
    # by fading the new surface toward both sides, not crossing ear.
    selected=(p[:,2]<-.017) & (np.abs(p[:,0])<.212)
    edges=selected & np.roll(selected,-1)
    starts=np.flatnonzero(edges & ~np.roll(edges,1))
    if len(starts)!=1: raise GeometryError("Arco de calva posterior no contiguo")
    start=int(starts[0]); arc=[int(rim[start])]
    i=start
    while edges[i]:
        arc.append(int(rim[(i+1)%len(rim)]))
        i=(i+1)%len(rim)
        if len(arc)>len(rim): raise GeometryError("Arco craneal ambiguo")
    if len(arc)<30: raise GeometryError("Poco borde de calva posterior")
    return np.asarray(arc,dtype=int)

def extend_visible_dome(p,f,params):
    """Five smooth, visible rings descending all the way into low rear neck.
    The original skull dome is never modified, so the top join is exact.
    """
    old=boundary_arc(p,f)
    base=p[old]
    n=len(old)
    u=np.linspace(0,1,n)
    # taper to zero at sides so the extension stays behind the ears.
    taper=.09+.91*(np.sin(np.pi*u)**.58)
    center=np.array([-.000038,-.010537])
    radial=base[:,[0,2]]-center
    rows=[]
    steps=(.20,.40,.60,.80,1.0)
    for t in steps:
        # Bulge mildly over old ragged back (without growing endless hair);
        # narrow toward low neck, seamlessly from the existing dome rim.
        bulge=1+(params["bulk"]-1)*np.sin(np.pi*t)
        neck=.78 if t==1 else 1-.22*t*t
        radial_scale=bulge*neck
        xyz=base.copy()
        xyz[:,1]=base[:,1]-params["drop"]*t*taper
        xyz[:,0]=center[0]+radial[:,0]*radial_scale
        xyz[:,2]=center[1]+radial[:,1]*radial_scale
        rows.append(xyz)
    new_p=np.vstack([p,*rows])
    new_faces=[]
    old_row=old
    for row_i in range(len(rows)):
        next_row=np.arange(len(p)+row_i*n,len(p)+(row_i+1)*n)
        for k in range(n-1):
            a,b=int(old_row[k]),int(old_row[k+1])
            c,d=int(next_row[k]),int(next_row[k+1])
            new_faces.extend(((b,a,c),(b,c,d)))
        old_row=next_row
    new_faces=np.asarray(new_faces,dtype=np.int64)
    tri=new_p[new_faces]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
    if np.any(area<1e-11): raise GeometryError("Relleno produjo triangulos degenerados")
    if np.min(tri[:,:,1])<.50 or np.max(tri[:,:,2])> .09:
        raise GeometryError("El relleno invade limites de seguridad de la cabeza")
    # Lower ring is part of a remaining open partial boundary: do not claim manifold.
    stats={"original_cranium_faces":len(f),"added_faces":len(new_faces),
       "added_vertices":len(rows)*n,"anchored_original_rim_vertices":n,
       "lowest_new_y":float(rows[-1][:,1].min()),
       "new_rear_most_z":float(new_p[len(p):,2].min()),
       "original_skull_vertices_unchanged":True,"original_skull_faces_unchanged":True,
       "complete_manifold":False}
    return new_p,np.vstack([f,new_faces]),np.tile(old,len(rows)),stats

def shave_hair(face_p,face_f,params):
    """Discard only 100% rear and tightly-limited temple hair TRIANGLES.
    Ears and front face protected by vertex-wise exclusion; NO vertex moves.
    """
    corners=face_p[face_f]
    x,y,z=corners[:,:,0],corners[:,:,1],corners[:,:,2]
    # Completely protect the ear housing incl. rear of ears and nearby margin.
    ear_vertices=((np.abs(x)>=.187)&(y>=.605)&(y<=.805)&
                  (z>=-.17)&(z<=.164))
    face_vertices=(z>=.075)
    # A triangle touching an ear, a front facial point, or above the dome
    # cannot be shaved, irrespective of category.
    protected=np.any(ear_vertices|face_vertices,axis=1)
    rear=np.all(z<params["z_cut"],axis=1)&np.all(y<.810,axis=1)
    # Sideburn candidates: side of head, behind face and before ears,
    # with every corner inside narrow cheek-free posterior window.
    side=(np.all(np.abs(x)<.188,axis=1)&
          np.all(np.abs(x)>.128,axis=1)&
          np.all((y>.644)&(y<.788),axis=1)&
          np.all(z<params["sideburn_z"],axis=1))
    back_mask=rear&~protected
    side_mask=side&~protected&~back_mask
    removed=back_mask|side_mask
    if removed.sum()<40:
        raise GeometryError("Rapado insuficiente: clasificacion de pelo revisar")
    # strict non-edit guarantee for protected triangles
    if np.any(removed&protected):raise GeometryError("Se intento cortar oreja o rostro")
    new_f=face_f[~removed]
    # Facial and ear face triangle sets preserve original order.
    if len(new_f)+removed.sum()!=len(face_f):
        raise GeometryError("Perdida de indices en rapado")
    stats={"original_face_primitive_triangles":len(face_f),
       "removed_rear_hair_triangles":int(back_mask.sum()),
       "removed_sideburn_triangles":int(side_mask.sum()),
       "remaining_face_triangles":len(new_f),
       "preserved_protected_triangles":int(protected.sum()),
       "protected_triangles_removed":int(np.sum(removed&protected)),
       "face_vertices_untouched":True,"ear_vertices_untouched":True,
       "morph_targets_untouched":True,
       "not_all_hair_assumed_removed":True}
    return new_f,removed,stats

def write_candidate(profile,params,baseline,binary):
    original=copy.deepcopy(baseline)
    j=copy.deepcopy(baseline)
    orig_prims=original["meshes"][0]["primitives"]
    prims=j["meshes"][0]["primitives"]
    face,cap=prims[:2]
    assert face.get("extras",{}).get("pieza")=="Cabeza" and cap.get("extras",{}).get("pieza")=="Craneo"
    oldcap=orig_prims[1]
    cattr={name:render.acc(original,binary,idx) for name,idx in oldcap["attributes"].items()}
    if set(cattr)!={"POSITION","NORMAL","JOINTS_0","WEIGHTS_0"} or "targets" in cap:
        raise RuntimeError("Atributos craneales inesperados")
    cf=render.acc(original,binary,oldcap["indices"]).astype(np.int64).reshape(-1,3)
    p,f,parents,cstats=extend_visible_dome(cattr["POSITION"],cf,params)
    faceattr=orig_prims[0]["attributes"]
    fp=render.acc(original,binary,faceattr["POSITION"])
    ff=render.acc(original,binary,orig_prims[0]["indices"]).astype(np.int64).reshape(-1,3)
    remaining,removed,fstats=shave_hair(fp,ff,params)
    raw=bytearray(binary)
    for key,data in cattr.items():
        expanded=p if key=="POSITION" else np.vstack((data,data[parents]))
        acc=original["accessors"][oldcap["attributes"][key]]
        cap["attributes"][key]=add_accessor(j,raw,
            np.asarray(expanded,dtype=render.CT[acc["componentType"]]),
            acc["componentType"],acc["type"],34962,key=="POSITION")
    cap["indices"]=add_accessor(j,raw,f.astype(np.uint32).ravel(),5125,"SCALAR",34963)
    face["indices"]=add_accessor(j,raw,remaining.astype(np.uint32).ravel(),5125,"SCALAR",34963)
    cap.setdefault("extras",{})["copox_edit"]="G2C3 skull continuation, experimental"
    face.setdefault("extras",{})["copox_edit"]="G2C3 remove rear/sideburn faces, experimental"
    j["asset"].setdefault("extras",{})["copox"]="G2C3 NOT APPROVED / no automatic merge"
    name=f"maniqui_v0_3_r3_g2c3_nuca_{profile}_SIN_APROBAR.glb"
    dst=Path("assets/maniqui")/name
    if dst.exists():raise FileExistsError("Nunca sobrescribir candidato: "+str(dst))
    write_glb(dst,j,raw)
    out,bb=render.load(dst)
    new_prims=out["meshes"][0]["primitives"]
    oldp=orig_prims[0]; newp=new_prims[0]
    if not(all(newp.get(k)==oldp.get(k) for k in ("attributes","targets","material","mode"))
           and out["skins"]==original["skins"]
           and out["animations"]==original["animations"]
           and out["nodes"]==original["nodes"]
           and out["materials"]==original["materials"]
           and new_prims[2:]==orig_prims[2:]
           and bb[:len(binary)]==binary):
        raise RuntimeError("Algo fuera de ROI o rig/morph/materiales fue modificado")
    if len(render.acc(out,bb,newp["indices"]))!=3*len(remaining):
        raise RuntimeError("Rapado no exportado correctamente")
    if not np.array_equal(render.acc(out,bb,new_prims[1]["attributes"]["POSITION"])[:len(cattr["POSITION"])],cattr["POSITION"]):
        raise RuntimeError("Se modifico la superficie suave de Codex")
    if sha(SRC)!=SRC_SHA:raise RuntimeError("Fuente original modificada")
    return {"profile":profile,"glb":str(dst),"sha256":sha(dst),
       "source_sha256":SRC_SHA,"dome":cstats,"shave":fstats,
       "face_eyes_mouth_nose_vertices_unchanged":True,
       "ear_vertices_unchanged":True,
       "all_original_face_morphs_unchanged":True,
       "rig_bones":len(j["skins"][0]["joints"]),
       "animation_definitions":len(j["animations"]),
       "godot_import_pending":True,"visual_approval":False,
       "model_approved":False,"source_untouched":True}

def render_comparison(candidates,original_face_count,original_cap_count):
    entries=[("ORIGINAL",SRC)]+[(k,v["glb"]) for k,v in candidates.items()]
    out=Image.new("RGB",(6*420,len(entries)*495),"white")
    pen=ImageDraw.Draw(out)
    originals=render.gather(SRC)[:2]
    changes={}
    for row,(label,path) in enumerate(entries):
        tris=render.gather(path)[:2]
        differences={}
        for col,(view,yaw) in enumerate(CAMERAS):
            frame=render.render(tris,yaw,W=420,H=463,bounds=BOUNDS)
            out.paste(frame,(420*col,495*row+32))
            pen.text((420*col+9,495*row+9),label+" | "+view,fill=(17,30,45))
            if row>0:
                orig=render.render(originals,yaw,W=420,H=463,bounds=BOUNDS)
                pixels=np.asarray(frame).astype(int)-np.asarray(orig).astype(int)
                changed=np.max(np.abs(pixels),axis=2)>18
                differences[view]={"changed_pixels":int(changed.sum()),
                    "changed_fraction":round(float(changed.mean()),5)}
        if row>0:changes[label]=differences
    OUT.mkdir(parents=True,exist_ok=True)
    sheet=OUT/"G2C3_ANTES_DESPUES_6V.png"
    out.save(sheet)
    # Independently show which new triangles extend the smooth cap.
    newtri=render.gather(candidates["completo"]["glb"])[:2]
    newcap=(newtri[1][0][original_cap_count:],np.array([.04,.68,.86]),None,None,None)
    oldcap=(newtri[1][0][:original_cap_count],np.array([.7,.7,.7]),None,None,None)
    masked=Image.new("RGB",(6*420,495),"white"); md=ImageDraw.Draw(masked)
    for col,(view,yaw) in enumerate(CAMERAS):
        frame=render.render([newtri[0],oldcap,newcap],yaw,W=420,H=463,bounds=BOUNDS)
        masked.paste(frame,(col*420,32))
        md.text((col*420+9,9),view+" | NUEVA NUCA AZUL",fill=(17,30,45))
    colored=OUT/"G2C3_NUEVA_SUPERFICIE_6V.png";masked.save(colored)
    return str(sheet),str(colored),changes

def main():
    if not SRC.is_file() or sha(SRC)!=SRC_SHA:raise RuntimeError("SHA original distinto")
    base,bin0=render.load(SRC)
    if len(base.get("skins",[]))!=1 or len(base["skins"][0]["joints"])!=56 or len(base["animations"])!=29:
        raise RuntimeError("Rig/maniqui de entrada inesperado")
    prims=base["meshes"][0]["primitives"]
    fc=len(render.acc(base,bin0,prims[0]["indices"]))//3
    cc=len(render.acc(base,bin0,prims[1]["indices"]))//3
    candidates={name:write_candidate(name,params,base,bin0)
                for name,params in PROFILES.items()}
    comparison,marked,diffs=render_comparison(candidates,fc,cc)
    for key,c in candidates.items():
        c["visual_difference"]=diffs[key]
        # Visibility gate: unlike G2-C2, this cannot be called a visual change
        # if it doesn't produce tangible differences from the real GLB render.
        rear=diffs[key]["NUCA"]["changed_fraction"]
        if rear<.025:raise RuntimeError(f"{key}: nuca cambia solo {rear:.3%} de pixeles")
        c["visibility_gate_pass"]=True
        if c["shave"]["removed_rear_hair_triangles"]<40:
            raise RuntimeError(f"{key}: sin pelo posterior realmente rapado")
        if c["shave"]["protected_triangles_removed"]>0:
            raise RuntimeError("Orejas/rostro modificados")
    report={"title":"G2-C3 cráneo extendido + limpieza de mechón y patillas",
       "status":"G2C3_VISIBILITY_MEASURED__ARTISTIC_REVIEW_REQUIRED",
       "glbs_are_unapproved":True,"original_glb_untouched":True,
       "base_source_sha256":SRC_SHA,"candidates":candidates,
       "comparison":comparison,"new_surface_mask":marked,
       "limitations":["No se garantiza soldadura craneofacial ni manifold",
          "Orejas protegidas; patillas solapadas con oreja pueden quedar",
          "La fidelidad artística y animaciones deformadas requieren inspección",
          "No sustituir modelo sin aprobación"] }
    (OUT/"REPORTE_G2C3.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"comparison":comparison,
       "candidates":{k:{"shave":v["shave"],"dome":v["dome"],
          "rear_pixels_changed":v["visual_difference"]["NUCA"]} for k,v in candidates.items()}},ensure_ascii=False))
    return report

if __name__=="__main__":
    main()
