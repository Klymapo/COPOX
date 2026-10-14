#!/usr/bin/env python3
"""COPOX · G2-C2 · Parches de nuca independientes de la cara.

Real r3 in, two separate GLB variants (nape-only) out. No modification
of the original assets, face primitive or any pre-existing vertex.
Four-view evidence and regional verdicts; no automatic global approval.
"""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw

from copox.geometry.regional_nape_patch import patch_nape_arc
from copox.geometry.regional_acceptance import RegionVerdict,evaluate_regions

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor,write_glb

SRC=Path("assets/maniqui/maniqui_v0_3_r3.glb")
SRC_SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/regional")
PROFILES={
    "nuca_local_suave":{"rear_z_max":-.048,"drop_m":.022,"depth_m":.003,"rings":3},
    "nuca_local_profunda":{"rear_z_max":-.048,"drop_m":.037,"depth_m":.007,"rings":4},
}
VIEWS=[("FRONTAL",0),("3/4",45),("PERFIL",90),("POSTERIOR",180)]
BOUNDS=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_one(name,params,base,binary):
    doc=copy.deepcopy(base)
    if sha(SRC)!=SRC_SHA or len(base["skins"][0]["joints"])!=56 or len(base["animations"])!=29:
        raise RuntimeError("Fuente sin SHA o rig aprobado")
    cap=doc["meshes"][0]["primitives"][1]
    face=doc["meshes"][0]["primitives"][0]
    oldcap=base["meshes"][0]["primitives"][1]
    if cap.get("extras",{}).get("pieza")!="Craneo" or face.get("extras",{}).get("pieza")!="Cabeza":
        raise RuntimeError("Primitivas no corresponden a r3")
    original_arrays={}
    for key,idx in oldcap["attributes"].items():
        accessor=base["accessors"][idx]
        if accessor.get("normalized") or accessor.get("sparse"):
            raise RuntimeError("Atributos normalizados/sparse no soportados: "+key)
        original_arrays[key]=render.acc(base,binary,idx)
    if set(original_arrays)-{"POSITION","NORMAL","JOINTS_0","WEIGHTS_0","TEXCOORD_0","TEXCOORD_1","COLOR_0"}:
        raise RuntimeError("Atributos desconocidos - no perder datos")
    idx=render.acc(base,binary,oldcap["indices"]).astype(int).reshape(-1,3)
    p=original_arrays["POSITION"]
    patch=patch_nape_arc(p,idx,**params)
    if patch.selected_boundary_edges<5 or patch.added_triangles<=0:
        raise RuntimeError("No se encontró zona de nuca útil")
    attributes={}
    for key,orig in original_arrays.items():
        if key=="POSITION": data=patch.positions
        else: data=np.concatenate([orig,orig[patch.parents]],axis=0)
        if len(data)!=len(patch.positions):raise RuntimeError("Atributos no alineados: "+key)
        attributes[key]=data

    if "JOINTS_0" not in attributes or "WEIGHTS_0" not in attributes:
        raise RuntimeError("El candidato perdió skinning")
    weights=attributes["WEIGHTS_0"]
    if np.max(abs(weights.sum(axis=1)-1))>1e-4 or np.max(attributes["JOINTS_0"])>=56:
        raise RuntimeError("Pesos o referencias a huesos inválidos")
    raw=bytearray(binary)
    for key,data in attributes.items():
        source_accessor=base["accessors"][oldcap["attributes"][key]]
        ct=source_accessor["componentType"]
        typ=source_accessor["type"]
        arr=np.asarray(data,dtype=render.CT[ct])
        cap["attributes"][key]=add_accessor(doc,raw,arr,ct,typ,34962,key=="POSITION")
    cap["indices"]=add_accessor(doc,raw,patch.faces.astype(np.uint32).ravel(),
                                5125,"SCALAR",34963)
    cap.setdefault("extras",{})["regional_patch"]=name
    doc["asset"].setdefault("extras",{})["copox"]="NAPE LOCAL ONLY - UNAPPROVED"
    dst=Path("assets/maniqui")/f"maniqui_r3_{name}_NO_APROBADO.glb"
    if dst.exists():raise FileExistsError("No overwrite: "+str(dst))
    write_glb(dst,doc,raw)
    check,b2=render.load(dst)
    oldprims=base["meshes"][0]["primitives"]
    newprims=check["meshes"][0]["primitives"]
    if newprims[0]!=oldprims[0] or newprims[2:]!=oldprims[2:]:
        raise RuntimeError("Regresión: cara u otras primitivas modificadas")
    if (b2[:len(binary)]!=binary or check["skins"]!=base["skins"]
        or check["animations"]!=base["animations"] or check["nodes"]!=base["nodes"]
        or check.get("materials")!=base.get("materials")):
        raise RuntimeError("Rig/animaciones/buffer/escena alterada")
    if sha(SRC)!=SRC_SHA:raise RuntimeError("Modelo histórico modificado")
    verts=render.acc(check,b2,newprims[1]["attributes"]["POSITION"])
    faces=render.acc(check,b2,newprims[1]["indices"]).astype(int).reshape(-1,3)
    if len(faces)!=len(patch.faces) or not np.allclose(verts,patch.positions,atol=1e-7):
        raise RuntimeError("Reimport GLB perdió geometría del parche")
    result={
       "name":name,"glb":str(dst),"sha256":sha(dst),"size":dst.stat().st_size,
       "baseline_sha256":SRC_SHA,"changed_region":"nuca",
       "selected_boundary_edges":patch.selected_boundary_edges,
       "added_vertices":patch.added_vertices,"added_triangles":patch.added_triangles,
       "maximum_new_vertex_displacement_mm":round(patch.max_displacement_m*1000,3),
       "original_vertices_unchanged":True,"original_faces_unchanged":True,
       "original_face_primitive_untouched":True,"original_other_body_parts_untouched":True,
       "original_attributes_retained":True,"skin_56_bones_retained":True,
       "animation_definitions_29_retained":True,
       "cranium_to_face_welded":False,
       "entire_head_watertight":False,
       "godot_import_pending":True,
       "artistic_review_pending":True,
       "full_model_approved":False,
       "source_model_untouched":True,
       "parameters":params,
    }
    return result


def preview(base,candidates):
    # Exactly the same cameras, bounds and lighting in both rows.
    entries=[("R3 ORIGINAL",SRC)]+[(key,Path(v["glb"])) for key,v in candidates.items()]
    sheet=Image.new("RGB",(4*400,len(entries)*470),(249,249,249))
    painter=ImageDraw.Draw(sheet)
    for row,(label,path) in enumerate(entries):
        tris=render.gather(path)[:2]
        for col,(view,yaw) in enumerate(VIEWS):
            img=render.render(tris,yaw,W=400,H=440,bounds=BOUNDS)
            sheet.paste(img,(col*400,row*470+30))
            painter.text((col*400+12,row*470+8),
                         f"{label} | {view}",fill=(28,39,52))
    sheet.save(OUT/"G2C2_NUCA_LOCAL_4V.png")


def run():
    if sha(SRC)!=SRC_SHA:
        raise RuntimeError("SHA original no concuerda")
    base,binary=render.load(SRC)
    OUT.mkdir(parents=True,exist_ok=True)
    candidates={}
    for name,params in PROFILES.items():
        candidates[name]=build_one(name,params,base,binary)
    preview(base,candidates)
    verdicts={
       "nuca":RegionVerdict("nuca",True,True,True,True,
                           notes="QA local y cuatro vistas generadas; revisión artística humana pendiente"),
       "rostro":RegionVerdict("rostro",False,True,True,True,
                             notes="Fragmentación previa conocida: NO invalida el parche de nuca"),
       "ojos":RegionVerdict("ojos",True,True,True,False,
                           notes="Intactos; inspección de facciones y lentes aún pendiente"),
       "orejas":RegionVerdict("orejas",True,True,True,False,
                             notes="Sin modificación; comprobar las patillas en close-up"),
    }
    gate=evaluate_regions(verdicts)
    if gate["regions"]["nuca"]["status"]!="PASS_LOCAL_TECHNICAL":
        raise RuntimeError("Nuca no pasa QA técnico local")
    if gate["regions"]["rostro"]["status"]!="REJECTED_LOCAL":
        raise RuntimeError("Rostro debía mantenerse como pendiente")
    if gate["promotion_allowed"] or gate["global_approval"]:
        raise RuntimeError("Promoción global no autorizada")
    summary={
        "status":"NAPE_CANDIDATES_LOCAL_TECHNICAL_PASS__ARTISTIC_REVIEW_PENDING",
        "baseline":str(SRC),"baseline_sha256":SRC_SHA,
        "variants":list(candidates.values()),
        "regions":gate,
        "comparison_png":"docs/maniqui/regional/G2C2_NUCA_LOCAL_4V.png",
        "warning":"Parche de nuca = continuidad local parcial; NO soldadura a toda la cara. Sin aprobar hasta revisar las vistas y las zonas colindantes.",
        "no_merge_or_original_replacement":True,
    }
    (OUT/"G2C2_NUCA_REGIONAL_REPORT.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":summary["status"],
                      "candidates":list(candidates.values()),
                      "region_statuses":{k:v["status"] for k,v in gate["regions"].items()}},
                      ensure_ascii=False))
    return summary


if __name__=="__main__":
    run()
