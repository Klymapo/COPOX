#!/usr/bin/env python3
"""COPOX G2-C: preflight HONESTO sobre r3 real, sin export o costura ciega."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
from copox.geometry.kernel import boundary_loops,GeometryError
sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render

SOURCE=Path("assets/maniqui/maniqui_v0_3_r3.glb")
SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/g2c/REAL_R3_PREFLIGHT.json")


def edge_statistics(f):
    e=np.sort(np.vstack((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1)
    _,count=np.unique(e,axis=0,return_counts=True)
    return {"boundary_edges_by_index":int((count==1).sum()),
            "nonmanifold_edges_by_index":int((count>2).sum())}


def analyze():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("Baseline no coincide, no operar")
    j,b=render.load(SOURCE)
    face,cap=j["meshes"][0]["primitives"][:2]
    rows=[]
    for name,prim in (("Cara",face),("Cráneo",cap)):
        points=render.acc(j,b,prim["attributes"]["POSITION"])
        faces=render.acc(j,b,prim["indices"]).astype(np.int64).reshape((-1,3))
        row={"piece":name,"vertices":len(points),"triangles":len(faces),
             **edge_statistics(faces)}
        try:
            loops=boundary_loops(faces)
            row["loops_by_index"]=len(loops)
            row["loop_sizes"]=[len(loop) for loop in loops]
            row["valid_simple_loops"]=True
        except GeometryError as e:
            row["valid_simple_loops"]=False
            row["rejection_reason"]=str(e)
        rows.append(row)
    face_row,cap_row=rows
    blocked=not (face_row["valid_simple_loops"] and len(face_row["loop_sizes"])==1
                 and cap_row["valid_simple_loops"] and len(cap_row["loop_sizes"])==1)
    if not blocked:
        # Existence of 1 + 1 loops still not enough; need correspondence,
        # valid authoritatively identified references and preserved GLB attrs.
        blocked=True
    report={"state":"BLOCKED_R3_NOT_TWO_HOMOLOGOUS_LOOPS" if blocked else "RESEARCH_REQUIRED",
         "source_sha256":SHA,"parts":rows,
         "actual_asset_name":"Maniqui v0.3 r3 historical GLB",
         "selected_face_loop":None,
         "selected_cranium_loop":None,
         "candidate_generated":False,
         "unsafe_gemini_assumptions":[
             "face has one comparable ring",
             "Trimesh edges_unique_length==1 selects boundary edges",
             "trimesh.load(force=mesh) retains 56 joint rig and 29 clips",
             "greedy diagonal always creates a nonintersecting manifold",
             "unchanged positions guarantee unchanged skin/morph/UV after GLB export",
             "Taubin smoothing does not move important facial vertices"],
         "required_before_real_stitch":[
             "Anatomic Cut of authentic single facial boundary verified on every reference",
             "Only simple manifold oriented contour for each part",
             "Canonical shared index space, UV/material/skin preserving exporter",
             "Self-intersection test of new triangles against face and cranium",
             "4-view visual critic and Godot validation",
             "Admin approval before any replacement or merge"],
         "no_source_modified":hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if report["state"]!="BLOCKED_R3_NOT_TWO_HOMOLOGOUS_LOOPS" or not report["no_source_modified"]:
        raise RuntimeError("Preflight must block unsafe stitching on r3")
    print(json.dumps({"state":report["state"],"parts":rows,
                      "no_model_modified":report["no_source_modified"]},ensure_ascii=False))
    return report

if __name__=="__main__":
    analyze()
