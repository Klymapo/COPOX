#!/usr/bin/env python3
"""G2-B · tres reconstrucciones de piel realmente conectadas AL CRÁNEO de r3.

No se confunde la topología cerrada del NUEVO cascarón con soldadura al mesh
facial original: las facciones siguen siendo primitivas aparte. No fusionar.
Todos los candidatos parten DIRECTAMENTE del r3 validado, jamás de G2 Cut Probe.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from copox.geometry.craniofacial_loft import extend_boundary_skin,vertex_normals
from copox.geometry.anatomic_roi import classify_anatomic_band
from copox.geometry.kernel import boundary_loops

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor,write_glb
from g2_anatomic_dryrun import SRC,SHA,boxes

OUT=Path("docs/maniqui/g2b")
PARAMS={
 "r1_short":{"rings":10,"front_end_y":.617,"side_end_y":.621,"rear_end_y":.605,
             "front_end_radius":.98,"side_end_radius":.91,"rear_end_radius":.95,"cut_face":False},
 "r2_deep":{"rings":14,"front_end_y":.566,"side_end_y":.590,"rear_end_y":.564,
            "front_end_radius":.96,"side_end_radius":.89,"rear_end_radius":.93,"cut_face":False},
 "r3_deep_cut":{"rings":14,"front_end_y":.566,"side_end_y":.590,"rear_end_y":.564,
                "front_end_radius":.96,"side_end_radius":.89,"rear_end_radius":.93,"cut_face":True}
}
ALLOWED={"POSITION","NORMAL","JOINTS_0","WEIGHTS_0","COLOR_0","TEXCOORD_0","TEXCOORD_1"}
HEAD_BOUND=(np.array([-.29,.515,-.29]),np.array([.29,1.,.29]))


def verify_source(j):
    if len(j.get("skins",[]))!=1 or len(j["skins"][0]["joints"])!=56 or len(j["animations"])!=29:
        raise RuntimeError("Rig fuente no coincide")
    face,cap=j["meshes"][0]["primitives"][:2]
    if face.get("extras",{}).get("pieza")!="Cabeza" or cap.get("extras",{}).get("pieza")!="Craneo":
        raise RuntimeError("Primitivas fuente inesperadas")
    if set(cap["attributes"])-ALLOWED:
        raise RuntimeError("Atributos del cráneo no implementados: "+str(set(cap["attributes"])-ALLOWED))
    if "targets" in cap or "targets" in face:
        raise RuntimeError("Morph targets aún no transferibles; cancelar G2-B")
    return face,cap


def export_variant(source_doc,raw_bytes,name,parameters,source_attrs):
    j=copy.deepcopy(source_doc)
    raw=bytearray(raw_bytes)
    face,cap=verify_source(j)
    cap_arrays={key:render.acc(source_doc,raw_bytes,idx) for key,idx in cap["attributes"].items()}
    old_positions=cap_arrays["POSITION"]
    old_faces=render.acc(source_doc,raw_bytes,cap["indices"]).astype(np.int64).reshape((-1,3))
    args={k:v for k,v in parameters.items() if k not in ("cut_face",)}
    loft=extend_boundary_skin(old_positions,old_faces,
          center_xz=(-.000038,-.010537),**args,close_bottom=True)
    if loft.old_vertex_count!=len(old_positions):
        raise RuntimeError("Estructura del cráneo invalidada")
    normals=vertex_normals(loft.positions,loft.faces)
    arrays={}
    for key,data in cap_arrays.items():
        if key=="POSITION":arrays[key]=loft.positions
        elif key=="NORMAL":arrays[key]=normals
        else:
            # Cada vértice nuevo conserva weights/UV/color del vértice origen
            # del borde: sin añadir influencias de huesos ni perder atributos.
            arrays[key]=np.concatenate((data,data[loft.correspondence]),axis=0)
    if "JOINTS_0" not in arrays or "WEIGHTS_0" not in arrays:
        raise RuntimeError("Pérdida de skinning")
    weights=arrays["WEIGHTS_0"]
    if (np.any(weights<-1e-8) or
        np.max(abs(weights.sum(axis=1)-1))>1e-5 or
        np.max(arrays["JOINTS_0"])>=56):
        raise RuntimeError("Pesos del nuevo cascarón inválidos")
    for k,x in arrays.items():
        accessor=source_doc["accessors"][cap["attributes"][k]]
        typ=accessor["type"];ct=accessor["componentType"]
        datatype=render.CT[ct]
        arr=np.asarray(x,dtype=datatype)
        cap["attributes"][k]=add_accessor(j,raw,arr,ct,typ,34962,k=="POSITION")
    cap["indices"]=add_accessor(j,raw,loft.faces.astype(np.uint32).reshape(-1),5125,"SCALAR",34963)
    cap.setdefault("extras",{})["g2b_prototype"]="cráneo extendido con shared indexed rim; face NO welded"
    base_face_indices=render.acc(source_doc,raw_bytes,face["indices"]).astype(np.int64).reshape(-1,3)
    kept=len(base_face_indices);cut=0;protected=0
    if parameters["cut_face"]:
        fp=source_attrs["POSITION"]
        rim=old_positions[np.asarray(boundary_loops(old_faces)[0],dtype=int)]
        roi=classify_anatomic_band(fp,base_face_indices,rim,boxes(),
             seam_distance=.015,clearance=.008,angle_center_xz=(-.000038,-.010537))
        legacy_features=np.any(((fp[:,2]>.155)&(np.abs(fp[:,0])<.185)&(fp[:,1]<.775))[base_face_indices],axis=1)
        legacy_ears=np.any(((np.abs(fp[:,0])>.205)&(fp[:,1]<.712))[base_face_indices],axis=1)
        if np.any(roi.candidate & (legacy_features|legacy_ears|roi.protected)):
            raise RuntimeError("Máscara corta facciones protegidas; abortar")
        indices=base_face_indices[~roi.candidate]
        protected=int(roi.protected.sum());kept=len(indices);cut=int(roi.candidate.sum())
        face["indices"]=add_accessor(j,raw,indices.astype(np.uint32).ravel(),5125,"SCALAR",34963)
        face.setdefault("extras",{})["g2b_prototype"]="recorte conservador face experimental"
    j["asset"].setdefault("extras",{})["copox"]=f"G2B {name} experimental unapproved; face is NOT welded"
    dest=Path("assets/maniqui")/f"maniqui_v0_3_r3_g2b_{name}.glb"
    if dest.exists():raise FileExistsError("No sobrescribir modelo ya existente: "+str(dest))
    write_glb(dest,j,raw)
    dst_doc,dst_bin=render.load(dest)
    if (dst_doc["nodes"]!=source_doc["nodes"] or
        dst_doc["skins"]!=source_doc["skins"] or
        dst_doc["animations"]!=source_doc["animations"] or
        dst_doc["materials"]!=source_doc["materials"] or
        dst_bin[:len(raw_bytes)]!=raw_bytes):
        raise RuntimeError("Regresión de recursos preexistentes")
    if dst_doc["meshes"][0]["primitives"][2:]!=source_doc["meshes"][0]["primitives"][2:]:
        raise RuntimeError("Se alteraron piezas del cuerpo")
    if np.any(loft.faces[:len(old_faces)]!=old_faces) or np.any(loft.positions[:len(old_positions)]!=old_positions):
        raise RuntimeError("Pérdida de geometría histórica de cráneo")
    # Verify on REIMPORTED GLB, not just the in-memory generator:
    cprim=dst_doc["meshes"][0]["primitives"][1]
    positions=render.acc(dst_doc,dst_bin,cprim["attributes"]["POSITION"])
    triangles=render.acc(dst_doc,dst_bin,cprim["indices"]).astype(int).reshape(-1,3)
    if len(boundary_loops(triangles))!=0:
        raise RuntimeError("Reimportación GLB abierta pese a cierre prometido")
    vv=positions[triangles]
    areas=np.linalg.norm(np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0]),axis=1)*.5
    if np.any(areas<1e-11):
        raise RuntimeError("Reimportación GLB tiene triángulos degenerados")
    metadata={"name":name,"source":str(SRC),"source_sha256":SHA,
       "glb":str(dest),"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
       "model_bytes":dest.stat().st_size,"bones":56,"clips":29,
       "original_cranium_vertices":len(old_positions),
       "new_cranium_vertices":len(positions),
       "original_cranium_triangles":len(old_faces),
       "new_cranium_triangles":len(triangles),
       "added_loft_triangles":loft.added_triangles,
       "original_face_triangles":len(base_face_indices),
       "new_face_triangles":kept,"face_triangles_cut":cut,
       "protected_triangles_lost":0,
       "original_materials_and_animations_identical":True,
       "new_shell_watertight_as_one_primitive":True,
       "original_face_to_new_shell_welded":False,
       "actual_geometry_source":"Maniqui r3 experimental historical mixed provenance",
       "deficiency":"Facial mesh remains separate, possibly intersecting shell; no semantic artistic likeness guaranteed",
       "godot_verified":False,"all_refs_verified":False,"self_intersection_verified":False,
       "approve_or_merge":False,"parameters":parameters}
    return metadata


def render_compare(baseline,candidates):
    original_tris=render.gather(baseline)
    all_pts=np.concatenate([t[0].reshape(-1,3) for t in original_tris])
    full_bounds=(all_pts.min(axis=0),all_pts.max(axis=0))
    viewlist=[("FRENTE",0),("3/4",45),("PERFIL",90),("ESPALDA",180)]
    names=["BASE"]+list(candidates)
    # Include only frontal/head primitive meshes at 400x400 and show 4 views.
    sheet=Image.new("RGB",(4*380,len(names)*448),"white")
    d=ImageDraw.Draw(sheet)
    for row,label in enumerate(names):
        path=baseline if label=="BASE" else candidates[label]
        tris=render.gather(path)[:2]
        for col,(view,yaw) in enumerate(viewlist):
            img=render.render(tris,yaw,W=380,H=420,bounds=HEAD_BOUND)
            sheet.paste(img,(col*380,row*448+28))
            d.text((col*380+8,row*448+8),f"{label} - {view}",fill=(30,41,56))
    OUT.mkdir(parents=True,exist_ok=True)
    sheet.save(OUT/"G2B_lamina_4v_candidatos.png")
    return str(OUT/"G2B_lamina_4v_candidatos.png")


def main():
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("SHA de base histórica incorrecta; G2-B bloqueado")
    j,b=render.load(SRC);face,cap=verify_source(j)
    attrs={k:render.acc(j,b,v) for k,v in face["attributes"].items()}
    outputs={}
    for name,p in PARAMS.items():
        outputs[name]=export_variant(j,b,name,p,attrs)
        print(f"[G2B] {name}: closed shell {outputs[name]['new_shell_watertight_as_one_primitive']} "
              f"skin {outputs[name]['bones']} bones, {outputs[name]['clips']} clips")
    render_compare(SRC,{k:v["glb"] for k,v in outputs.items()})
    summary={"source":str(SRC),"source_sha256":SHA,"variants":list(outputs.values()),
       "artistic_status":"REVIEW_REQUIRED","auto_select":False,
       "invariants":["old r3 untouched","rig 56 bones","29 clips retained",
          "all materials preserved","original face attributes preserved",
          "cap and extended skin share same indexed topology, watertight after reimport"],
       "blocking_issues":["face primitive still NOT welded to shell",
          "unknown interpenetration with old face and garments",
          "manual comparison across all actual references pending",
          "Godot animation importer not yet run"],
       "fourview_comparison":"docs/maniqui/g2b/G2B_lamina_4v_candidatos.png",
       "status":"CANDIDATES_EXPERIMENTAL_NOT_APPROVED"}
    (OUT/"G2B_reporte.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="variants"},ensure_ascii=False))
if __name__=="__main__":main()
