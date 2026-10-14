#!/usr/bin/env python3
"""COPOX · Nuca G2-C2, candidato REGIONAL sobre r3 REAL.

Añade una banda sólo detrás del cráneo, sin editar vértices originales,
cualquier triángulo de Cara, ni rig. Es ensayo, no soldadura definitiva.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from copox.geometry.partial_loft import extend_rear_arc
from copox.geometry.regional_acceptance import evaluate_regions,RegionVerdict

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor,write_glb

SOURCE=Path("assets/maniqui/maniqui_v0_3_r3.glb")
SOURCE_SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
CANDIDATE=Path("assets/maniqui/maniqui_v0_3_r3_nuca_regional_probe.glb")
OUT=Path("docs/maniqui/regions/nuca")
BOUNDS=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
VIEWS=[("FRENTE",0),("3/4",45),("PERFIL",90),("ESPALDA",180)]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    if sha(SOURCE)!=SOURCE_SHA or CANDIDATE.exists():
        raise RuntimeError("Baseline distinta o candidato existente: no sobrescribir")
    old,raw=render.load(SOURCE)
    if len(old.get("skins",[]))!=1 or len(old["skins"][0]["joints"])!=56 or len(old["animations"])!=29:
        raise RuntimeError("Rig original distinto")
    before_face=copy.deepcopy(old["meshes"][0]["primitives"][0])
    cap=old["meshes"][0]["primitives"][1]
    if before_face.get("extras",{}).get("pieza")!="Cabeza" or cap.get("extras",{}).get("pieza")!="Craneo":
        raise RuntimeError("R3 primitiva inesperada")
    attrs={k:render.acc(old,raw,v) for k,v in cap["attributes"].items()}
    if "targets" in cap or not {"POSITION","JOINTS_0","WEIGHTS_0"}.issubset(attrs):
        raise RuntimeError("Morphs o skin no soportados en prototipo regional")
    cap_faces=render.acc(old,raw,cap["indices"]).astype(np.int64).reshape(-1,3)
    result=extend_rear_arc(attrs["POSITION"],cap_faces,sector_threshold=.36,
                            drop_m=.027,radius_factor=.97,
                            center_xz=(-.000038,-.010537))
    if result.report["front_sector_selected"] or result.report["remaining_open_loops"]!=1:
        raise RuntimeError("El arco deja de ser exclusivamente posterior")
    new=copy.deepcopy(old)
    ncap=new["meshes"][0]["primitives"][1]
    destination_raw=bytearray(raw)
    for name,values in attrs.items():
        if name=="POSITION":
            combined=result.positions
        else:
            combined=np.concatenate([values,values[result.source_vertex_ids]],axis=0)
        original_accessor=old["accessors"][cap["attributes"][name]]
        component=original_accessor["componentType"]
        typ=original_accessor["type"]
        arr=np.asarray(combined,dtype=render.CT[component])
        ncap["attributes"][name]=add_accessor(new,destination_raw,arr,component,typ,34962,name=="POSITION")
    ncap["indices"]=add_accessor(new,destination_raw,result.faces.astype(np.uint32).reshape(-1),5125,"SCALAR",34963)
    ncap.setdefault("extras",{})["copox_region"]="nuca / local-only / unapproved"
    new.setdefault("asset",{}).setdefault("extras",{})["copox"]="Nuca local candidate, NOT a welded/repaired face"
    write_glb(CANDIDATE,new,destination_raw)

    candidate_doc,candidate_raw=render.load(CANDIDATE)
    assert candidate_raw[:len(raw)]==raw, "Original binary buffer changed"
    assert candidate_doc["skins"]==old["skins"]
    assert candidate_doc["animations"]==old["animations"]
    assert candidate_doc["nodes"]==old["nodes"]
    assert candidate_doc["materials"]==old["materials"]
    assert candidate_doc["meshes"][0]["primitives"][0]==before_face
    assert candidate_doc["meshes"][0]["primitives"][2:]==old["meshes"][0]["primitives"][2:]
    assert sha(SOURCE)==SOURCE_SHA

    # Real four-camera compare from actual GLB, not regenerated illustration
    sheet=Image.new("RGB",(4*370,2*430),(250,250,249))
    pen=ImageDraw.Draw(sheet)
    for row,(label,file) in enumerate((("R3 ORIGINAL",SOURCE),("NUCA REGIONAL",CANDIDATE))):
        geo=render.gather(file)[:2]
        for col,(view,yaw) in enumerate(VIEWS):
            img=render.render(geo,yaw,W=370,H=395,bounds=BOUNDS)
            sheet.paste(img,(col*370,row*430+35))
            pen.text((col*370+10,row*430+10),f"{label} / {view}",fill=(28,40,52))
    OUT.mkdir(parents=True,exist_ok=True)
    sheet.save(OUT/"NUCA_ANTES_DESPUES_4V.png")

    # Real data supports local structural QA; likeness of nape is still
    # pending independently. Face was rejected in prior G2-B and should NOT
    # veto regional progress on nape.
    statuses=evaluate_regions({
        "nuca":RegionVerdict("nuca",True,True,True,False,
            "Extensión posterior preserva frente/cara; evaluación estética por vistas pendiente"),
        "rostro":RegionVerdict("rostro",False,True,True,True,
            "Problema heredado de cara; NO afecta el estado estructural de nuca"),
    })
    report={
       "baseline_sha256":SOURCE_SHA,
       "nuca_candidate_path":str(CANDIDATE),
       "candidate_sha256":sha(CANDIDATE),
       "region":"nuca",
       "local_operator":"partial rear arc extension",
       "added_triangles":result.created_triangles,
       "added_vertices":len(result.source_vertex_ids),
       "original_cranium_triangle_count":len(cap_faces),
       "cranial_open_loops_after":result.report["remaining_open_loops"],
       "cranium_to_face_welded":False,
       "original_face_mesh_untouched":True,
       "other_body_mesh_primitives_untouched":True,
       "original_buffers_prefix_identical":True,
       "skeleton_56_bones_preserved":True,
       "clip_definitions_29_preserved":True,
       "materials_preserved":True,
       "godot_import_not_yet_verified":True,
       "self_intersections_not_verified":True,
       "local_visual_review_required":True,
       "global_visual_approval":False,
       "regional_decisions":statuses,
       "capture_sheet":str(OUT/"NUCA_ANTES_DESPUES_4V.png"),
       "source_not_modified":sha(SOURCE)==SOURCE_SHA,
       "production_ready":False,
       "warnings":[
          "Local closing band does not weld face, and still has one open loop",
          "Nape status is NEEDS_EVIDENCE, not ACCEPTED_LOCAL until reviewed against references",
          "Face failure does not invalidate independently verified nape structure",
          "Do not replace historical r3 or merge without approval",
       ],
    }
    (OUT/"REGIONAL_QA.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("warnings",)},ensure_ascii=False))
    return report


if __name__=="__main__":
    run()
